import asyncio

from lnbits.core.models import Payment
from lnbits.tasks import register_invoice_listener
from loguru import logger

#######################################
########## RUN YOUR TASKS HERE ########
#######################################

# Placeholder invoice listener — this extension does not process payments.
# The listener is kept so the extension lifecycle hooks work correctly.


async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, "ext_adminwallets")
    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra.get("tag") != "adminwallets":
        return
    # No payment processing needed for this extension.
    logger.debug(f"adminwallets: ignored payment {payment.payment_hash}")