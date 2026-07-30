import asyncio

from fastapi import APIRouter
from lnbits.tasks import create_permanent_unique_task
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import adminwallets_generic_router
from .views_api import adminwallets_api_router

adminwallets_ext: APIRouter = APIRouter(
    prefix="/adminwallets", tags=["adminwallets"]
)
adminwallets_ext.include_router(adminwallets_generic_router)
adminwallets_ext.include_router(adminwallets_api_router)


adminwallets_static_files = [
    {
        "path": "/adminwallets/static",
        "name": "adminwallets_static",
    }
]

scheduled_tasks: list[asyncio.Task] = []


def adminwallets_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def adminwallets_start():
    task = create_permanent_unique_task("ext_adminwallets", wait_for_paid_invoices)
    scheduled_tasks.append(task)


__all__ = [
    "db",
    "adminwallets_ext",
    "adminwallets_start",
    "adminwallets_static_files",
    "adminwallets_stop",
]