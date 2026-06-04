"""Unit tests for get_planned_orders tool."""
import pytest
from app.tools.get_planned_orders import get_planned_orders


@pytest.mark.asyncio
async def test_get_planned_orders_returns_structure():
    result = await get_planned_orders.ainvoke({"material": "FG-001", "plant": "1010"})
    assert result["material"] == "FG-001"
    assert result["plant"] == "1010"
    assert "planned_orders" in result
    assert isinstance(result["planned_orders"], list)


@pytest.mark.asyncio
async def test_get_planned_orders_with_date_filter():
    result = await get_planned_orders.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
        }
    )
    assert result["date_from"] == "2026-06-01"
    assert "error" not in result


@pytest.mark.asyncio
async def test_get_planned_orders_missing_material_returns_error():
    result = await get_planned_orders.ainvoke({"material": "", "plant": "1010"})
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_get_planned_orders_missing_plant_returns_error():
    result = await get_planned_orders.ainvoke({"material": "FG-001", "plant": ""})
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_get_planned_orders_top_limit_applied():
    result = await get_planned_orders.ainvoke({"material": "FG-001", "plant": "1010"})
    assert result["top_limit_applied"] == 100
