import asyncio

from fastapi import APIRouter
from lnbits.tasks import create_permanent_unique_task
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import adminusers_generic_router
from .views_api import adminusers_api_router

adminusers_ext: APIRouter = APIRouter(
    prefix="/adminusers", tags=["adminusers"]
)
adminusers_ext.include_router(adminusers_generic_router)
adminusers_ext.include_router(adminusers_api_router)


adminusers_static_files = [
    {
        "path": "/adminusers/static",
        "name": "adminusers_static",
    }
]

scheduled_tasks: list[asyncio.Task] = []


def adminusers_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def adminusers_start():
    task = create_permanent_unique_task("ext_adminusers", wait_for_paid_invoices)
    scheduled_tasks.append(task)


__all__ = [
    "db",
    "adminusers_ext",
    "adminusers_start",
    "adminusers_static_files",
    "adminusers_stop",
]