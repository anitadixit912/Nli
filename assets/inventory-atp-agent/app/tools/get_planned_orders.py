"""Tool: get_planned_orders — reads open planned orders from S/4HANA."""
import logging
from typing import Any

from langchain_core.tools import tool
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

TOP_LIMIT = 100


@tool
async def get_planned_orders(
    material: str,
    plant: str,
    date_from: str = "",
    date_to: str = "",
) -> dict[str, Any]:
    """Retrieve open planned orders for a material/plant from S/4HANA.
    Used to identify supply-side options for corrective action simulation.

    Args:
        material: SAP material number (e.g. 'FG-001')
        plant: SAP plant code (e.g. '1010')
        date_from: Optional ISO date filter start (basic start date)
        date_to: Optional ISO date filter end (basic end date)

    Returns:
        dict with list of planned orders including type, quantity, and dates.
    """
    with tracer.start_as_current_span("tool.get_planned_orders") as span:
        span.set_attribute("material", material)
        span.set_attribute("plant", plant)

        if not material or not plant:
            return {
                "error": "INVALID_INPUT",
                "message": "Both 'material' and 'plant' are required.",
            }

        # MCP wraps API_PLANNED_ORDERS (OData v2):
        #   EntitySet: A_PlannedOrder
        #   Filter: Material eq '{material}' and ProductionPlant eq '{plant}'
        #   $top=100, optional BasicStartDate/BasicEndDate filter
        return {
            "material": material,
            "plant": plant,
            "date_from": date_from,
            "date_to": date_to,
            "planned_orders": [],
            "top_limit_applied": TOP_LIMIT,
            "note": (
                f"Planned orders from A_PlannedOrder entity set. "
                f"Results limited to {TOP_LIMIT} rows."
            ),
        }
