"""Unit tests for get_demand_elements tool."""
import pytest
from app.tools.get_demand_elements import get_demand_elements


@pytest.mark.asyncio
async def test_get_demand_elements_returns_structure():
    result = await get_demand_elements.ainvoke({"material": "FG-001", "plant": "1010"})
    assert result["material"] == "FG-001"
    assert result["plant"] == "1010"
    assert "safety_stock" in result
    assert "reorder_point" in result
    assert "demand_elements" in result
    assert "supply_elements" in result
    assert isinstance(result["demand_elements"], list)
    assert isinstance(result["supply_elements"], list)


@pytest.mark.asyncio
async def test_get_demand_elements_with_date_filter():
    result = await get_demand_elements.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
        }
    )
    assert result["date_from"] == "2026-06-01"
    assert result["date_to"] == "2026-06-30"
    assert "error" not in result


@pytest.mark.asyncio
async def test_get_demand_elements_missing_material_returns_error():
    result = await get_demand_elements.ainvoke({"material": "", "plant": "1010"})
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_get_demand_elements_missing_plant_returns_error():
    result = await get_demand_elements.ainvoke({"material": "FG-001", "plant": ""})
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_get_demand_elements_top_limit_applied():
    result = await get_demand_elements.ainvoke({"material": "RM-100", "plant": "2000"})
    assert result["top_limit_applied"] == 100
