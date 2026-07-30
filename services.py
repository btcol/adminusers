import csv
import io

from loguru import logger

from lnbits.core.crud.wallets import create_wallet, delete_wallet, get_wallet
from lnbits.core.services import create_invoice, pay_invoice, fee_reserve_total

from .crud import (
    create_extension_settings,
    create_managed_wallet,
    get_extension_settings,
    update_extension_settings,
)
from .models import (
    CsvInputRow,
    CsvDeleteInputRow,
    ExtensionSettings,
    WalletBatchResult,
    WalletBatchResultRow,
    WalletDeleteBatchResultRow,
    WalletDeleteBatchResult,
)


########################### CSV Parsing ############################


def parse_csv_input(csv_content: str) -> list[CsvInputRow]:
    """
    Parse the uploaded CSV file content into a list of CsvInputRow.

    Expected columns: wallet_name, include_admin_key
    - wallet_name: the name for the wallet to create
    - include_admin_key: 1 = return both admin_key + invoice_key,
                         0 = return only invoice_key

    Raises ValueError for malformed input.
    """
    reader = csv.DictReader(io.StringIO(csv_content.strip()))

    required_columns = {"wallet_name", "include_admin_key"}
    if reader.fieldnames is None:
        raise ValueError("CSV file is empty or missing headers.")

    normalized_fields = {f.strip().lower() for f in reader.fieldnames}
    missing = required_columns - normalized_fields
    if missing:
        raise ValueError(
            f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
            f"Expected: wallet_name, include_admin_key"
        )

    rows = []
    for line_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
        wallet_name = row.get("wallet_name", "").strip()
        if not wallet_name:
            raise ValueError(f"Row {line_num}: wallet_name cannot be empty.")

        raw_flag = row.get("include_admin_key", "0").strip()
        if raw_flag not in ("0", "1"):
            raise ValueError(
                f"Row {line_num}: include_admin_key must be '0' or '1', got '{raw_flag}'."
            )

        rows.append(
            CsvInputRow(
                wallet_name=wallet_name,
                include_admin_key=(raw_flag == "1"),
            )
        )

    if not rows:
        raise ValueError("CSV contains no data rows.")

    return rows


########################### Batch Creation ############################


async def process_wallet_csv(
    user_id: str,
    csv_content: str,
) -> WalletBatchResult:
    """
    Parse the CSV, create each wallet under the admin's account,
    and return a structured result for CSV download.

    Errors on individual rows do not abort the entire batch.
    """
    rows = parse_csv_input(csv_content)

    results: list[WalletBatchResultRow] = []
    success_count = 0
    error_count = 0

    for row in rows:
        try:
            wallet = await create_wallet(
                user_id=user_id,
                wallet_name=row.wallet_name,
            )

            await create_managed_wallet(
                user_id=user_id,
                wallet_id=wallet.id,
                wallet_name=row.wallet_name,
                include_admin_key=row.include_admin_key,
            )

            results.append(
                WalletBatchResultRow(
                    wallet_name=row.wallet_name,
                    wallet_id=wallet.id,
                    admin_key=wallet.adminkey if row.include_admin_key else None,
                    invoice_key=wallet.inkey,
                    status="success",
                )
            )
            success_count += 1

        except Exception as exc:
            logger.warning(
                f"adminwallets: failed to create wallet '{row.wallet_name}': {exc}"
            )
            results.append(
                WalletBatchResultRow(
                    wallet_name=row.wallet_name,
                    status="error",
                    error=str(exc),
                )
            )
            error_count += 1

    return WalletBatchResult(
        total=len(rows),
        success_count=success_count,
        error_count=error_count,
        rows=results,
    )


def parse_delete_csv_input(csv_content: str) -> list[CsvDeleteInputRow]:
    reader = csv.DictReader(io.StringIO(csv_content.strip()))

    if reader.fieldnames is None:
        raise ValueError("CSV file is empty or missing headers.")

    normalized_fields = {f.strip().lower() for f in reader.fieldnames}
    if "wallet_id" not in normalized_fields:
        raise ValueError("CSV is missing required column: wallet_id")

    rows = []
    for line_num, row in enumerate(reader, start=2):
        wallet_id = row.get("wallet_id", "").strip()
        if not wallet_id:
            raise ValueError(f"Row {line_num}: wallet_id cannot be empty.")
        rows.append(CsvDeleteInputRow(wallet_id=wallet_id))

    if not rows:
        raise ValueError("CSV contains no data rows.")

    return rows


async def process_delete_wallet_csv(
    admin_user_id: str,
    admin_wallet_id: str,
    csv_content: str,
) -> WalletDeleteBatchResult:
    rows = parse_delete_csv_input(csv_content)

    results: list[WalletDeleteBatchResultRow] = []
    success_count = 0
    error_count = 0

    from .crud import delete_managed_wallet

    for row in rows:
        try:
            wallet = await get_wallet(row.wallet_id)
            if not wallet:
                raise ValueError("Wallet no encontrada en el sistema core.")

            if wallet.user == admin_user_id:
                raise ValueError("Protección de admin: No puedes borrar las wallets de tu cuenta de administrador.")

            # Realizar sweeping de fondos si el balance es mayor a cero
            funds_swept = 0
            balance_msat = wallet.balance_msat
            if balance_msat > 0:
                fee_msat = fee_reserve_total(balance_msat, internal=True)
                amount_to_send_msat = balance_msat - fee_msat
                
                if amount_to_send_msat > 0:
                    amount_sat = amount_to_send_msat // 1000
                    if amount_sat > 0:
                        # Crear invoice en la wallet del administrador
                        invoice = await create_invoice(
                            wallet_id=admin_wallet_id,
                            amount=amount_sat,
                            memo=f"Sweep from deleted wallet {row.wallet_id}",
                            internal=True,
                        )
                        # Pagar invoice desde la wallet que se va a borrar
                        await pay_invoice(
                            wallet_id=row.wallet_id,
                            payment_request=invoice.bolt11,
                        )
                        funds_swept = amount_sat

            # Borrar de la extensión
            await delete_managed_wallet(admin_user_id, row.wallet_id)
            
            # Borrar del core
            await delete_wallet(admin_user_id, row.wallet_id)

            results.append(
                WalletDeleteBatchResultRow(
                    wallet_id=row.wallet_id,
                    funds_swept=funds_swept,
                    status="success",
                )
            )
            success_count += 1

        except Exception as exc:
            logger.warning(
                f"adminwallets: failed to delete wallet '{row.wallet_id}': {exc}"
            )
            results.append(
                WalletDeleteBatchResultRow(
                    wallet_id=row.wallet_id,
                    status="error",
                    error=str(exc),
                )
            )
            error_count += 1

    return WalletDeleteBatchResult(
        total=len(rows),
        success_count=success_count,
        error_count=error_count,
        rows=results,
    )


########################### Settings ############################


async def get_settings(user_id: str) -> ExtensionSettings:
    settings = await get_extension_settings(user_id)
    if not settings:
        settings = await create_extension_settings(user_id, ExtensionSettings())
    return settings


async def update_settings(user_id: str, data: ExtensionSettings) -> ExtensionSettings:
    settings = await get_extension_settings(user_id)
    if not settings:
        settings = await create_extension_settings(user_id, data)
    else:
        settings = await update_extension_settings(user_id, data)
    return settings
