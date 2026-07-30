# Description: Page endpoints for the adminusers extension.

from fastapi import APIRouter, Depends
from lnbits.core.views.generic import index
from lnbits.decorators import check_admin
from lnbits.helpers import template_renderer

adminusers_generic_router = APIRouter()


def adminusers_renderer():
    return template_renderer(["adminusers/templates"])


#######################################
##### ADD YOUR PAGE ENDPOINTS HERE ####
#######################################


# Admin-only page — requires admin privileges
adminusers_generic_router.add_api_route(
    "/", methods=["GET"], endpoint=index, dependencies=[Depends(check_admin)]
)
