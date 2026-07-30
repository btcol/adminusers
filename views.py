# Description: Add your page endpoints here.


from fastapi import APIRouter, Depends
from lnbits.core.views.generic import index, index_public
from lnbits.decorators import check_account_exists
from lnbits.helpers import template_renderer

adminusers_generic_router = APIRouter()


def adminusers_renderer():
    return template_renderer(["adminusers/templates"])


#######################################
##### ADD YOUR PAGE ENDPOINTS HERE ####
#######################################


# Backend admin page
adminusers_generic_router.add_api_route(
    "/", methods=["GET"], endpoint=index, dependencies=[Depends(check_account_exists)]
)


# Frontend shareable page


