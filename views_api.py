# Description: API endpoints for the adminusers extension.
from http import HTTPStatus

from fastapi import APIRouter, Depends, UploadFile
from fastapi.exceptions import HTTPException
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
)
from .services import (
    get_settings,
    process_wallet_csv,
    update_settings,
)

managed_wallet_filters = parse_filters(ManagedWalletFilters)

adminusers_api_router = APIRouter()


############################# Wallet Batch Upload #############################


@adminusers_api_router.post(
    "/api/v1/wallets/upload",
    name="Upload Wallet CSV",
    summary=(
        "Upload a CSV file with wallet names to create wallets in bulk. "
        "Returns structured results for client-side CSV download."
    ),
    response_description="Batch creation result with per-row status.",
    response_model=WalletBatchResult,
    status_code=HTTPStatus.CREATED,
)
async def api_upload_wallet_csv(
    file: UploadFile,
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
    except UnicodeDecodeError:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            "File encoding not supported. Please upload a UTF-8 encoded CSV.",
        )

    try:
        result = await process_wallet_csv(user_id=account.id, csv_content=csv_content)
    except ValueError as exc:
        raise HTTPException(HTTPStatus.BAD_REQUEST, str(exc))

    return result


############################# Wallet List #############################


@adminusers_api_router.get(
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


@adminusers_api_router.get(
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


@adminusers_api_router.delete(
    "/api/v1/wallets/{wallet_id}",
    name="Delete Managed Wallet Record",
    summary=(
        "Remove the wallet record from the extension's registry. "
        "Does NOT delete the actual wallet from the LNbits core."
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

    await delete_managed_wallet(account.id, wallet_id)
    return SimpleStatus(success=True, message="Wallet record removed from registry.")


############################ Settings #############################


@adminusers_api_router.get(
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


@adminusers_api_router.put(
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
