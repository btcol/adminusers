from uuid import uuid4

import pytest

from adminwallets.crud import (  # type: ignore[import]
    create_extension_settings,
    create_managed_wallet,
    delete_managed_wallet,
    get_extension_settings,
    get_managed_wallet,
    get_managed_wallets_paginated,
    update_extension_settings,
)
from adminwallets.models import (  # type: ignore[import]
    ExtensionSettings,
)


@pytest.mark.asyncio
async def test_managed_wallet_crud():
    user_id = uuid4().hex
    wallet_id = uuid4().hex
    wallet_name = "Test Wallet"

    wallet = await create_managed_wallet(user_id, wallet_id, wallet_name, True)
    assert wallet.id == wallet_id
    assert wallet.user_id == user_id
    assert wallet.wallet_name == wallet_name
    assert wallet.include_admin_key is True

    fetched = await get_managed_wallet(user_id, wallet_id)
    assert fetched is not None
    assert fetched.id == wallet_id

    page = await get_managed_wallets_paginated(user_id)
    assert page.total == 1
    assert len(page.data) == 1

    await delete_managed_wallet(user_id, wallet_id)
    fetched_deleted = await get_managed_wallet(user_id, wallet_id)
    assert fetched_deleted is None


@pytest.mark.asyncio
async def test_extension_settings_crud():
    user_id = uuid4().hex
    data = ExtensionSettings(name="Test Settings")

    settings = await create_extension_settings(user_id, data)
    assert settings.name == "Test Settings"

    fetched = await get_extension_settings(user_id)
    assert fetched is not None
    assert fetched.name == "Test Settings"

    data_updated = ExtensionSettings(name="Updated Settings")
    updated = await update_extension_settings(user_id, data_updated)
    assert updated.name == "Updated Settings"
