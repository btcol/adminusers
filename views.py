# Description: Page endpoints for the adminwallets extension.

from fastapi import APIRouter, Depends
from lnbits.core.views.generic import index
from lnbits.decorators import check_admin
from lnbits.helpers import template_renderer

adminwallets_generic_router = APIRouter()


def adminwallets_renderer():
    return template_renderer(["adminwallets/templates"])


#######################################
##### ADD YOUR PAGE ENDPOINTS HERE ####
#######################################


# Admin-only page — requires admin privileges
adminwallets_generic_router.add_api_route("/", methods=["GET"], endpoint=index, dependencies=[Depends(check_admin)])
