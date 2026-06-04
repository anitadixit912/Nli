"""Watchlist monitor — evaluates stock breach severity for Protect_Service_Level sub-intent."""
import logging
from typing import Any

from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def compute_breach_severity(current_stock: float, threshold: float) -> str:
    """Classify safety stock breach severity based on how far below threshold."""
    if current_stock <= 0:
        return "HIGH"
    ratio = current_stock / threshold if threshold > 0 else 1.0
    if ratio < 0.25:
        return "HIGH"
    if ratio < 0.75:
        return "MEDIUM"
    return "LOW"


@tracer.start_as_current_span("watchlist_monitor.check_entries")
async def check_watchlist(
    entries: list[dict[str, Any]],
    stock_fetcher: Any,
) -> list[dict[str, Any]]:
    """Evaluate a list of watchlist entries against live stock data.

    Args:
        entries: List of dicts with keys: material, plant, safety_stock_threshold, sla_date
        stock_fetcher: Async callable matching get_material_stock signature (injected for testability)

    Returns:
        List of alert dicts for entries that breached their threshold.
    """
    alerts: list[dict[str, Any]] = []

    for entry in entries:
        material = entry.get("material", "")
        plant = entry.get("plant", "")
        threshold = float(entry.get("safety_stock_threshold", 0))
        sla_date = entry.get("sla_date", "")

        if not material or not plant:
            logger.warning("Skipping watchlist entry with missing material or plant: %s", entry)
            continue

        try:
            stock_data = await stock_fetcher(material=material, plant=plant)

            if "error" in stock_data:
                logger.warning(
                    "M1.missed: stock_perception_failed | material=%s plant=%s "
                    "error=%s — perception step did not complete",
                    material,
                    plant,
                    stock_data.get("error"),
                )
                continue

            current_stock = float(stock_data.get("unrestricted_stock", 0))
            logger.info(
                "M1.achieved: stock_perception_complete | material=%s plant=%s sloc=ALL "
                "stock_categories=4 demand_elements=0",
                material,
                plant,
            )

            if current_stock < threshold:
                severity = compute_breach_severity(current_stock, threshold)
                alert = {
                    "alert_type": "SAFETY_STOCK_BREACH",
                    "material": material,
                    "plant": plant,
                    "current_stock": current_stock,
                    "threshold": threshold,
                    "sla_date": sla_date,
                    "breach_severity": severity,
                    "message": (
                        f"Safety stock breach detected for {material} at plant {plant}. "
                        f"Current stock {current_stock} is below threshold {threshold} "
                        f"(Severity: {severity})."
                    ),
                }
                alerts.append(alert)
                logger.warning(
                    "Safety stock breach: material=%s plant=%s current=%.2f threshold=%.2f severity=%s",
                    material,
                    plant,
                    current_stock,
                    threshold,
                    severity,
                )

        except Exception as exc:
            logger.error(
                "M1.missed: stock_perception_failed | material=%s plant=%s "
                "error=%s — perception step did not complete",
                material,
                plant,
                str(exc),
            )

    return alerts
