# The migration file is where you build your database tables.
# Migrations are append-only — never edit existing migrations, only add new ones.

empty_dict: dict[str, str] = {}


async def m001_extension_settings(db):
    """
    Initial settings table.
    """
    await db.execute(
        f"""
        CREATE TABLE adminwallets.extension_settings (
            id TEXT NOT NULL,
            name TEXT,
            updated_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now}
        );
    """
    )


async def m002_managed_wallets(db):
    """
    Table to track wallets created via the adminwallets extension.
    Stores only metadata — admin/invoice keys are NOT persisted here,
    they are returned once at creation time via the CSV download.
    """
    await db.execute(
        f"""
        CREATE TABLE adminwallets.managed_wallets (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            wallet_name TEXT NOT NULL,
            include_admin_key BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now},
            updated_at TIMESTAMP NOT NULL DEFAULT {db.timestamp_now}
        );
    """
    )