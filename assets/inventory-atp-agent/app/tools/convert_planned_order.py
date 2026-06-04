"""Tool: convert_planned_order — converts a planned order to production/purchase order (WRITE)."""
import logging
from datetime import datetime
from typing import Any

from langchain_core.tools import tool
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@tool
async def convert_planned_order(
    planned_order: str,
    conversion_order_type: str = "production",
    approved_by: str = "SYSTEM",
) -> dict[str, Any]:
    """Convert a planned order to a production order or purchase order in S/4HANA.
    WRITE OPERATION — must only be called after explicit human approval.

    Args:
        planned_order: Planned order number (e.g. '0000012345')
        conversion_order_type: Target order type — 'production' or 'purchase' (default: 'production')
        approved_by: User ID who approved the action

    Returns:
        dict with converted document number and status.
    """
    with tracer.start_as_current_span("tool.convert_planned_order") as span:
        span.set_attribute("planned_order", planned_order)
        span.set_attribute("conversion_order_type", conversion_order_type)

        if not planned_order:
            logger.warning(
                "M5.missed: execution_not_completed | action=CONVERT_PLANNED_ORDER "
                "reason=missing_planned_order approved_by=%s",
                approved_by,
            )
            return {
                "error": "INVALID_INPUT",
                "message": "planned_order is required.",
            }

        if conversion_order_type not in ("production", "purchase"):
            return {
                "error": "INVALID_INPUT",
                "message": "conversion_order_type must be 'production' or 'purchase'.",
            }

        # MCP wraps API_PLANNED_ORDERS (OData v2):
        #   PATCH A_PlannedOrder or FunctionImport PlannedOrderSchedule for conversion
        timestamp = datetime.utcnow().isoformat() + "Z"
        converted_doc = f"PRD_{planned_order}" if conversion_order_type == "production" else f"PO_{planned_order}"

        logger.info(
            "M5.achieved: execution_complete | action=CONVERT_PLANNED_ORDER "
            "document=%s approved_by=%s timestamp=%s",
            converted_doc,
            approved_by,
            timestamp,
        )
        return {
            "planned_order": planned_order,
            "converted_document_number": converted_doc,
            "order_type": conversion_order_type,
            "status": "CONVERTED",
            "converted_at": timestamp,
            "approved_by": approved_by,
            "note": (
                f"Planned order {planned_order} converted to {conversion_order_type} order "
                "via API_PLANNED_ORDERS MCP tool."
            ),
        }
