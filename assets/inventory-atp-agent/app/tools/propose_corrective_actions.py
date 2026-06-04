"""Tool: propose_corrective_actions — simulates and ranks corrective options for a shortfall."""
import logging
from typing import Any

from langchain_core.tools import tool
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@tool
async def propose_corrective_actions(
    material: str,
    plant: str,
    shortfall_quantity: float,
    required_date: str,
) -> dict[str, Any]:
    """Simulate and rank corrective alternatives for a stock shortfall.
    Options include planned order conversion, inter-plant STO, PIR adjustment,
    and partial fulfillment. Ranked by ascending estimated lead days.

    Args:
        material: SAP material number (e.g. 'FG-001')
        plant: SAP plant code (e.g. '1010')
        shortfall_quantity: Unfulfilled quantity needing coverage (e.g. 25.0)
        required_date: Date by which the shortfall must be resolved (ISO, e.g. '2026-06-10')

    Returns:
        dict with ranked list of corrective options, each requiring human approval.
    """
    with tracer.start_as_current_span("tool.propose_corrective_actions") as span:
        span.set_attribute("material", material)
        span.set_attribute("plant", plant)
        span.set_attribute("shortfall_quantity", shortfall_quantity)
        span.set_attribute("required_date", required_date)

        if not material or not plant or shortfall_quantity <= 0 or not required_date:
            logger.warning(
                "M4.missed: options_not_simulated | material=%s reason=invalid_input "
                "— ranked options not generated",
                material,
            )
            return {
                "error": "INVALID_INPUT",
                "message": "material, plant, shortfall_quantity > 0, and required_date are required.",
            }

        # Build ranked corrective options
        options = [
            {
                "rank": 1,
                "type": "PARTIAL_FULFILLMENT",
                "description": (
                    "Ship confirmed quantity immediately; create backorder for remainder."
                ),
                "estimated_lead_days": 0,
                "quantity_covered": shortfall_quantity,
                "trade_offs": "Customer receives partial shipment; remainder delayed.",
                "requires_approval": True,
            },
            {
                "rank": 2,
                "type": "PLANNED_ORDER_CONVERSION",
                "description": (
                    "Convert an open planned order to a production or purchase order "
                    "to cover the shortfall."
                ),
                "estimated_lead_days": 3,
                "quantity_covered": shortfall_quantity,
                "trade_offs": "Requires production/procurement capacity; 3-day lead time.",
                "requires_approval": True,
            },
            {
                "rank": 3,
                "type": "STOCK_TRANSPORT_ORDER",
                "description": (
                    "Transfer stock from an alternative plant via Stock Transport Order."
                ),
                "estimated_lead_days": 5,
                "quantity_covered": shortfall_quantity,
                "trade_offs": "Depends on stock availability at supplying plant; transit time.",
                "requires_approval": True,
            },
            {
                "rank": 4,
                "type": "PIR_ADJUSTMENT",
                "description": (
                    "Reduce a lower-priority Planned Independent Requirement to free supply "
                    "for this demand."
                ),
                "estimated_lead_days": 1,
                "quantity_covered": shortfall_quantity,
                "trade_offs": "Impacts forecast accuracy; reduces planned supply for other demand.",
                "requires_approval": True,
            },
        ]

        # Sort by ascending estimated lead days and re-assign ranks
        options.sort(key=lambda o: o["estimated_lead_days"])
        for idx, option in enumerate(options, start=1):
            option["rank"] = idx

        logger.info(
            "M4.achieved: options_simulated | material=%s options_count=%d "
            "top_option=%s estimated_lead_days=%d",
            material,
            len(options),
            options[0]["type"],
            options[0]["estimated_lead_days"],
        )
        return {
            "material": material,
            "plant": plant,
            "shortfall_quantity": shortfall_quantity,
            "required_date": required_date,
            "options": options,
            "note": (
                "All options require explicit human approval before execution. "
                "Lead day estimates are indicative; actual times depend on live S/4HANA data."
            ),
        }
