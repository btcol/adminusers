# Description: API endpoints for the adminwallets extension.
from http import HTTPStatus

from fastapi import APIRouter, Depends, Form, UploadFile
from fastapi.exceptions import HTTPException
from lnbits.core.crud.wallets import get_wallets
from lnbits.core.models import SimpleStatus, User
from lnbits.db import Filters, Page
from lnbits.decorators import check_admin, parse_filters
from lnbits.helpers import generate_filter_params_openapi

from .crud import (
    delete_managed_wallet,
    get_managed_wallet,
    get_managed_wallets_paginated,
)
from .models import (
    ExtensionSettings,
    ManagedWallet,
    ManagedWalletFilters,
    WalletBatchResult,
    WalletDeleteBatchResult,
)
from .services import (
    get_settings,
    process_wallet_csv,
    update_settings,
)

managed_wallet_filters = parse_filters(ManagedWalletFilters)

adminwallets_api_router = APIRouter()


############################# Admin Wallets Selector #############################


@adminwallets_api_router.get(
    "/api/v1/admin-wallets",
    name="List Admin Wallets",
    summary="List wallets belonging to the admin, for use as funding source selector.",
)
async def api_list_admin_wallets(
    account: User = Depends(check_admin),
):
    wallets = await get_wallets(account.id)
    return [
        {
            "id": w.id,
            "name": w.name,
            "balance_sat": w.balance_msat // 1000,
        }
        for w in wallets
    ]


############################# Wallet Batch Upload #############################


@adminwallets_api_router.post(
    "/api/v1/wallets/upload",
    name="Upload Wallet CSV",
    summary=(
        "Upload a CSV file with wallet names to create wallets in bulk. "
        "Optionally include an 'initial_balance' column (sats) and select a source wallet. "
        "Returns structured results for client-side CSV download."
    ),
    response_description="Batch creation result with per-row status.",
    response_model=WalletBatchResult,
    status_code=HTTPStatus.CREATED,
)
async def api_upload_wallet_csv(
    file: UploadFile,
    source_wallet_id: str | None = Form(default=None),
    account: User = Depends(check_admin),
) -> WalletBatchResult:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            "Only .csv files are accepted.",
        )

    raw_bytes = await file.read()
    try:
        csv_content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as err:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            "File encoding not supported. Please upload a UTF-8 encoded CSV.",
        ) from err

    # Validate source wallet belongs to this admin
    if source_wallet_id:
        admin_wallets = await get_wallets(account.id)
        admin_wallet_ids = {w.id for w in admin_wallets}
        if source_wallet_id not in admin_wallet_ids:
            raise HTTPException(
                HTTPStatus.FORBIDDEN,
                "source_wallet_id does not belong to your account.",
            )

    try:
        result = await process_wallet_csv(
            user_id=account.id,
            csv_content=csv_content,
            admin_wallet_id=source_wallet_id,
        )
    except ValueError as exc:
        raise HTTPException(HTTPStatus.BAD_REQUEST, str(exc)) from exc

    return result


############################# Wallet List #############################


@adminwallets_api_router.get(
    "/api/v1/wallets/paginated",
    name="Managed Wallet List",
    summary="Get paginated list of wallets created by this extension.",
    response_description="Paginated list of managed wallets (no keys returned).",
    openapi_extra=generate_filter_params_openapi(ManagedWalletFilters),
    response_model=Page[ManagedWallet],
)
async def api_get_managed_wallets(
    account: User = Depends(check_admin),
    filters: Filters = Depends(managed_wallet_filters),
) -> Page[ManagedWallet]:
    return await get_managed_wallets_paginated(
        user_id=account.id,
        filters=filters,
    )


@adminwallets_api_router.get(
    "/api/v1/wallets/{wallet_id}",
    name="Get Managed Wallet",
    summary="Get metadata for a single managed wallet (no keys returned).",
    response_description="A managed wallet record or 404 if not found.",
    response_model=ManagedWallet,
)
async def api_get_managed_wallet(
    wallet_id: str,
    account: User = Depends(check_admin),
) -> ManagedWallet:
    record = await get_managed_wallet(account.id, wallet_id)
    if not record:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Wallet record not found.")
    return record


@adminwallets_api_router.delete(
    "/api/v1/wallets/{wallet_id}",
    name="Delete Managed Wallet Record",
    summary=(
        "Remove the wallet record from the extension's registry and delete it from the LNbits core. "
        "Sweeps funds to the admin wallet."
    ),
    response_description="Deletion status.",
    response_model=SimpleStatus,
)
async def api_delete_managed_wallet(
    wallet_id: str,
    account: User = Depends(check_admin),
) -> SimpleStatus:
    record = await get_managed_wallet(account.id, wallet_id)
    if not record:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Wallet record not found.")

    from lnbits.core.crud.wallets import delete_wallet, get_wallet, get_wallets
    from lnbits.core.services import create_invoice, fee_reserve_total, pay_invoice

    wallet = await get_wallet(wallet_id)
    if not wallet:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Core wallet not found.")

    balance_msat = wallet.balance_msat
    if balance_msat > 0:
        fee_msat = fee_reserve_total(balance_msat, internal=True)
        amount_to_send_msat = balance_msat - fee_msat
        if amount_to_send_msat > 0:
            amount_sat = amount_to_send_msat // 1000
            if amount_sat > 0:
                admin_wallets = await get_wallets(account.id)
                if admin_wallets:
                    admin_wallet_id = admin_wallets[0].id
                    invoice = await create_invoice(
                        wallet_id=admin_wallet_id,
                        amount=amount_sat,
                        memo=f"Sweep from deleted wallet {wallet_id}",
                        internal=True,
                    )
                    await pay_invoice(
                        wallet_id=wallet_id,
                        payment_request=invoice.bolt11,
                    )

    await delete_managed_wallet(account.id, wallet_id)
    await delete_wallet(user_id=account.id, wallet_id=wallet_id)
    return SimpleStatus(success=True, message="Wallet deleted from core and registry.")


@adminwallets_api_router.post(
    "/api/v1/wallets/delete-csv",
    name="Delete Wallet CSV",
    summary="Upload a CSV file with wallet IDs to delete them in bulk, sweeping funds to the admin.",
    response_description="Batch deletion result with per-row status.",
    response_model=WalletDeleteBatchResult,
    status_code=HTTPStatus.OK,
)
async def api_delete_wallet_csv(
    file: UploadFile,
    account: User = Depends(check_admin),
) -> WalletDeleteBatchResult:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            "Only .csv files are accepted.",
        )

    raw_bytes = await file.read()
    try:
        csv_content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as err:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            "File encoding not supported. Please upload a UTF-8 encoded CSV.",
        ) from err

    from lnbits.core.crud.wallets import get_wallets

    admin_wallets = await get_wallets(account.id)
    if not admin_wallets:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Admin has no wallets to receive funds.")
    admin_wallet_id = admin_wallets[0].id

    from .services import process_delete_wallet_csv

    try:
        result = await process_delete_wallet_csv(
            admin_user_id=account.id, admin_wallet_id=admin_wallet_id, csv_content=csv_content
        )
    except ValueError as exc:
        raise HTTPException(HTTPStatus.BAD_REQUEST, str(exc)) from exc

    return result


############################ Settings #############################


@adminwallets_api_router.get(
    "/api/v1/settings",
    name="Get Settings",
    summary="Get the extension settings.",
    response_description="The extension settings.",
    response_model=ExtensionSettings,
)
async def api_get_settings(
    account: User = Depends(check_admin),
) -> ExtensionSettings:
    return await get_settings("admin")


@adminwallets_api_router.put(
    "/api/v1/settings",
    name="Update Settings",
    summary="Update the extension settings.",
    response_description="The updated settings.",
    response_model=ExtensionSettings,
)
async def api_update_extension_settings(
    data: ExtensionSettings,
    account: User = Depends(check_admin),
) -> ExtensionSettings:
    return await update_settings("admin", data)
