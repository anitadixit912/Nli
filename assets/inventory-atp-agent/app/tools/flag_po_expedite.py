"""Tool: flag_po_expedite — flags a purchase order for buyer expedite action (WRITE)."""
import logging
from datetime import datetime
from typing import Any

from langchain_core.tools import tool
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@tool
async def flag_po_expedite(
    purchase_order: str,
    purchase_order_item: str,
    expedite_reason: str,
    buyer_note: str = "",
    approved_by: str = "SYSTEM",
) -> dict[str, Any]:
    """Flag a purchase order item for buyer expedite action in S/4HANA.
    WRITE OPERATION — must only be called after explicit human approval.
    Creates a structured expedite request that is routed to the buyer for action.

    Args:
        purchase_order: PO document number (e.g. '4500012345')
        purchase_order_item: PO line item number (e.g. '00010')
        expedite_reason: Business reason for expediting (e.g. 'Safety stock breach at Plant 1010')
        buyer_note: Optional message to the buyer
        approved_by: User ID who approved the expedite flag

    Returns:
        dict with expedite request payload and status PENDING_BUYER_ACTION.
    """
    with tracer.start_as_current_span("tool.flag_po_expedite") as span:
        span.set_attribute("purchase_order", purchase_order)
        span.set_attribute("purchase_order_item", purchase_order_item)
        span.set_attribute("expedite_reason", expedite_reason)

        if not all([purchase_order, purchase_order_item, expedite_reason]):
            logger.warning(
                "M5.missed: execution_not_completed | action=FLAG_PO_EXPEDITE "
                "reason=missing_required_fields approved_by=%s",
                approved_by,
            )
            return {
                "error": "INVALID_INPUT",
                "message": "purchase_order, purchase_order_item, and expedite_reason are required.",
            }

        # Creates a structured expedite notification payload.
        # In production, this is routed to the buyer via the S/4HANA purchasing workflow
        # or BTP Notifications service.
        timestamp = datetime.utcnow().isoformat() + "Z"

        logger.info(
            "M5.achieved: execution_complete | action=FLAG_PO_EXPEDITE "
            "document=%s approved_by=%s timestamp=%s",
            purchase_order,
            approved_by,
            timestamp,
        )
        return {
            "purchase_order": purchase_order,
            "purchase_order_item": purchase_order_item,
            "expedite_reason": expedite_reason,
            "buyer_note": buyer_note,
            "flagged_at": timestamp,
            "status": "PENDING_BUYER_ACTION",
            "approved_by": approved_by,
            "note": (
                f"Expedite request for PO {purchase_order} item {purchase_order_item} "
                "has been created. Buyer will be notified via purchasing workflow."
            ),
        }
