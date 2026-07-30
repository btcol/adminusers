from uuid import uuid4

import pytest

from adminwallets.crud import (  # type: ignore[import]
    create_owner_data,
    delete_owner_data,
    get_owner_data,
    get_owner_data_by_id,
    get_owner_data_ids_by_user,
    get_owner_data_paginated,
    update_owner_data,
)
from adminwallets.models import (  # type: ignore[import]
    CreateOwnerData,
    OwnerData,
)


@pytest.mark.asyncio
async def test_create_and_get_owner_data():
    user_id = uuid4().hex

    data = CreateOwnerData(
        name = "name_dYQZebtCAkprt85FvfgprW",
        wallet = "e064be16-6451-493b-9325-c2a6863ae0d3",
        currency = "sat",
        amount = 19,
        paid_down = True,
        date = datetime.fromisoformat("2026-07-14T19:33:01.175442+00:00"),
    )
    owner_data_one = await create_owner_data(user_id, data)
    assert owner_data_one.id is not None
    assert owner_data_one.user_id == user_id

    owner_data_one = await get_owner_data(user_id, owner_data_one.id)
    assert owner_data_one.id is not None
    assert owner_data_one.user_id == user_id
    assert owner_data_one.name == data.name
    assert owner_data_one.wallet == data.wallet
    assert owner_data_one.currency == data.currency
    assert owner_data_one.amount == data.amount
    assert owner_data_one.paid_down == data.paid_down
    assert owner_data_one.date == data.date

    data = CreateOwnerData(
        name = "name_dYQZebtCAkprt85FvfgprW",
        wallet = "e064be16-6451-493b-9325-c2a6863ae0d3",
        currency = "sat",
        amount = 19,
        paid_down = True,
        date = datetime.fromisoformat("2026-07-14T19:33:01.175442+00:00"),
    )
    owner_data_two = await create_owner_data(user_id, data)
    assert owner_data_two.id is not None
    assert owner_data_two.user_id == user_id

    owner_data_list = await get_owner_data_ids_by_user(user_id=user_id)
    assert len(owner_data_list) == 2

    owner_data_page = await get_owner_data_paginated(user_id=user_id)
    assert owner_data_page.total == 2
    assert len(owner_data_page.data) == 2

    await delete_owner_data(user_id, owner_data_one.id)
    owner_data_list = await get_owner_data_ids_by_user(user_id=user_id)
    assert len(owner_data_list) == 1

    owner_data_page = await get_owner_data_paginated(user_id=user_id)
    assert owner_data_page.total == 1
    assert len(owner_data_page.data) == 1


@pytest.mark.asyncio
async def test_update_owner_data():
    user_id = uuid4().hex

    data = CreateOwnerData(
        name = "name_dYQZebtCAkprt85FvfgprW",
        wallet = "e064be16-6451-493b-9325-c2a6863ae0d3",
        currency = "sat",
        amount = 19,
        paid_down = True,
        date = datetime.fromisoformat("2026-07-14T19:33:01.175442+00:00"),
    )
    owner_data_one = await create_owner_data(user_id, data)
    assert owner_data_one.id is not None
    assert owner_data_one.user_id == user_id

    owner_data_one = await get_owner_data(user_id, owner_data_one.id)
    assert owner_data_one.id is not None
    assert owner_data_one.user_id == user_id
    assert owner_data_one.name == data.name
    assert owner_data_one.wallet == data.wallet
    assert owner_data_one.currency == data.currency
    assert owner_data_one.amount == data.amount
    assert owner_data_one.paid_down == data.paid_down
    assert owner_data_one.date == data.date

    data_updated = CreateOwnerData(
        name = "name_dYQZebtCAkprt85FvfgprW",
        wallet = "e064be16-6451-493b-9325-c2a6863ae0d3",
        currency = "sat",
        amount = 19,
        paid_down = True,
        date = datetime.fromisoformat("2026-07-14T19:33:01.175442+00:00"),
    )
    owner_data_updated = OwnerData(**{**owner_data_one.dict(), **data_updated.dict()})

    await update_owner_data(owner_data_updated)
    owner_data_one = await get_owner_data_by_id(owner_data_one.id)
    assert owner_data_one.name == owner_data_updated.name
    assert owner_data_one.wallet == owner_data_updated.wallet
    assert owner_data_one.currency == owner_data_updated.currency
    assert owner_data_one.amount == owner_data_updated.amount
    assert owner_data_one.paid_down == owner_data_updated.paid_down
    assert owner_data_one.date == owner_data_updated.date
