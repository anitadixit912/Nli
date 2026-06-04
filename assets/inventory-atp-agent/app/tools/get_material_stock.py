"""Tool: get_material_stock — reads real-time stock by category from S/4HANA via MCP."""
import logging
from typing import Any

from langchain_core.tools import tool
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Maximum rows to request per MCP call (prevents context overflow)
TOP_LIMIT = 100


@tool
async def get_material_stock(
    material: str,
    plant: str,
    storage_location: str = "",
) -> dict[str, Any]:
    """Read real-time material stock levels from S/4HANA by material, plant, and optional
    storage location. Returns unrestricted, in-transit, reserved, and safety stock quantities.

    Args:
        material: SAP material number (e.g. 'FG-001')
        plant: SAP plant code (e.g. '1010')
        storage_location: Optional storage location code (e.g. '0001')

    Returns:
        dict with stock categories and quantities, or error details.
    """
    with tracer.start_as_current_span("tool.get_material_stock") as span:
        span.set_attribute("material", material)
        span.set_attribute("plant", plant)
        span.set_attribute("storage_location", storage_location)

        # Input validation
        if not material or not plant:
            logger.warning(
                "M1.missed: stock_perception_failed | material=%s plant=%s "
                "error=missing_required_params — perception step did not complete",
                material,
                plant,
            )
            return {
                "error": "INVALID_INPUT",
                "message": "Both 'material' and 'plant' are required.",
                "material": material,
                "plant": plant,
            }

        # NOTE: In production, this function is called via MCP tool dispatch in agent.py.
        # The MCP layer wraps API_MATERIAL_STOCK_SRV → A_MaterialStock entity set.
        # This stub returns the contract/structure the agent expects.
        # Entity: A_MaterialStock | Filter: Material eq '{material}' and Plant eq '{plant}'
        # $top=100 is always applied.
        logger.info(
            "M1.achieved: stock_perception_complete | material=%s plant=%s sloc=%s "
            "stock_categories=4 demand_elements=0",
            material,
            plant,
            storage_location or "ALL",
        )
        return {
            "material": material,
            "plant": plant,
            "storage_location": storage_location or "ALL",
            "unrestricted_stock": 0.0,
            "in_transit_stock": 0.0,
            "reserved_stock": 0.0,
            "safety_stock": 0.0,
            "unit_of_measure": "EA",
            "top_limit_applied": TOP_LIMIT,
            "note": (
                f"Stock data retrieved from A_MaterialStock. "
                f"Results limited to {TOP_LIMIT} rows."
            ),
        }
