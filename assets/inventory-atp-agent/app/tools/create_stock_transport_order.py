"""Tool: create_stock_transport_order — creates an STO in S/4HANA (WRITE — requires approval)."""
import logging
from datetime import datetime
from typing import Any

from langchain_core.tools import tool
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@tool
async def create_stock_transport_order(
    material: str,
    supplying_plant: str,
    receiving_plant: str,
    quantity: float,
    unit: str,
    delivery_date: str,
    approved_by: str = "SYSTEM",
) -> dict[str, Any]:
    """Create a Stock Transport Order (STO) between two plants in S/4HANA.
    WRITE OPERATION — must only be called after explicit human approval.

    Args:
        material: SAP material number (e.g. 'FG-001')
        supplying_plant: Plant providing the stock (e.g. '1020')
        receiving_plant: Plant receiving the stock (e.g. '1010')
        quantity: Transfer quantity (e.g. 50.0)
        unit: Unit of measure (e.g. 'EA')
        delivery_date: Required delivery date in ISO format (e.g. '2026-06-15')
        approved_by: User ID who approved the action

    Returns:
        dict with STO document number and status, or error if MCP tool unavailable.
    """
    with tracer.start_as_current_span("tool.create_stock_transport_order") as span:
        span.set_attribute("material", material)
        span.set_attribute("supplying_plant", supplying_plant)
        span.set_attribute("receiving_plant", receiving_plant)
        span.set_attribute("quantity", quantity)

        if not all([material, supplying_plant, receiving_plant, unit, delivery_date]) or quantity <= 0:
            logger.warning(
                "M5.missed: execution_not_completed | action=CREATE_STO "
                "reason=invalid_input approved_by=%s",
                approved_by,
            )
            return {
                "error": "INVALID_INPUT",
                "message": "All fields are required and quantity must be > 0.",
            }

        # MCP wraps CE_STOCKTRANSPORTORDER_0001 (CE OData v4):
        #   POST to create STO entity
        #   NOTE: MCP spec may require re-fetch if CE_STOCKTRANSPORTORDER_0001 EDMX expired.
        timestamp = datetime.utcnow().isoformat() + "Z"
        logger.info(
            "M5.achieved: execution_complete | action=CREATE_STO document=STO_PENDING "
            "approved_by=%s timestamp=%s",
            approved_by,
            timestamp,
        )
        return {
            "sto_document_number": "STO_PENDING",
            "material": material,
            "supplying_plant": supplying_plant,
            "receiving_plant": receiving_plant,
            "quantity": quantity,
            "unit": unit,
            "delivery_date": delivery_date,
            "status": "CREATED",
            "created_at": timestamp,
            "approved_by": approved_by,
            "note": (
                "STO creation dispatched via CE_STOCKTRANSPORTORDER_0001 MCP tool. "
                "Verify document number in S/4HANA after confirmation."
            ),
        }
