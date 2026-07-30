# Description: CRUD operations for the adminwallets extension database.

from lnbits.db import Database, Filters, Page

from .models import (
    ExtensionSettings,
    ManagedWallet,
    ManagedWalletFilters,
    UserExtensionSettings,
)

db = Database("ext_adminwallets")


########################### Managed Wallets ############################


async def create_managed_wallet(
    user_id: str,
    wallet_id: str,
    wallet_name: str,
    include_admin_key: bool,
) -> ManagedWallet:
    record = ManagedWallet(
        id=wallet_id,
        user_id=user_id,
        wallet_name=wallet_name,
        include_admin_key=include_admin_key,
    )
    await db.insert("adminwallets.managed_wallets", record)
    return record


async def get_managed_wallet(
    user_id: str,
    wallet_id: str,
) -> ManagedWallet | None:
    return await db.fetchone(
        """
            SELECT * FROM adminwallets.managed_wallets
            WHERE id = :id AND user_id = :user_id
        """,
        {"id": wallet_id, "user_id": user_id},
        ManagedWallet,
    )


async def get_managed_wallets_paginated(
    user_id: str,
    filters: Filters[ManagedWalletFilters] | None = None,
) -> Page[ManagedWallet]:
    return await db.fetch_page(
        "SELECT * FROM adminwallets.managed_wallets",
        where=["user_id = :user_id"],
        values={"user_id": user_id},
        filters=filters,
        model=ManagedWallet,
    )


async def delete_managed_wallet(user_id: str, wallet_id: str) -> None:
    await db.execute(
        """
            DELETE FROM adminwallets.managed_wallets
            WHERE id = :id AND user_id = :user_id
        """,
        {"id": wallet_id, "user_id": user_id},
    )


############################ Settings #############################


async def create_extension_settings(user_id: str, data: ExtensionSettings) -> ExtensionSettings:
    settings = UserExtensionSettings(**data.dict(), id=user_id)
    await db.insert("adminwallets.extension_settings", settings)
    return settings


async def get_extension_settings(
    user_id: str,
) -> ExtensionSettings | None:
    return await db.fetchone(
        """
            SELECT * FROM adminwallets.extension_settings
            WHERE id = :user_id
        """,
        {"user_id": user_id},
        ExtensionSettings,
    )


async def update_extension_settings(user_id: str, data: ExtensionSettings) -> ExtensionSettings:
    settings = UserExtensionSettings(**data.dict(), id=user_id)
    await db.update("adminwallets.extension_settings", settings)
    return settings
