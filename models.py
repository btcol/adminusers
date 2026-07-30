from datetime import datetime, timezone

from lnbits.db import FilterModel
from pydantic import BaseModel, Field


########################### Managed Wallets ############################


class ManagedWallet(BaseModel):
    """Metadata record for a wallet created by this extension."""

    id: str  # wallet_id from LNbits core
    user_id: str  # admin account user_id
    wallet_name: str
    include_admin_key: bool = False

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ManagedWalletFilters(FilterModel):
    __search_fields__ = ["wallet_name", "id"]

    __sort_fields__ = [
        "wallet_name",
        "created_at",
        "updated_at",
    ]

    wallet_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


########################### CSV Processing ############################


class CsvInputRow(BaseModel):
    """A single parsed row from the uploaded CSV."""

    wallet_name: str
    include_admin_key: bool = False


class WalletBatchResultRow(BaseModel):
    """Result for a single wallet from the batch operation."""

    wallet_name: str
    wallet_id: str | None = None
    admin_key: str | None = None
    invoice_key: str | None = None
    status: str  # "success" | "error"
    error: str | None = None


class WalletBatchResult(BaseModel):
    """Full result of a batch wallet creation operation."""

    total: int
    success_count: int
    error_count: int
    rows: list[WalletBatchResultRow]


class CsvDeleteInputRow(BaseModel):
    """A single parsed row from the uploaded CSV for deletion."""

    wallet_id: str


class WalletDeleteBatchResultRow(BaseModel):
    """Result for a single wallet from the batch delete operation."""

    wallet_id: str
    funds_swept: int = 0
    status: str  # "success" | "error"
    error: str | None = None


class WalletDeleteBatchResult(BaseModel):
    """Full result of a batch wallet delete operation."""

    total: int
    success_count: int
    error_count: int
    rows: list[WalletDeleteBatchResultRow]


############################ Settings #############################


class ExtensionSettings(BaseModel):
    name: str | None = None

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def is_admin_only(cls) -> bool:
        return True


class UserExtensionSettings(ExtensionSettings):
    id: str
