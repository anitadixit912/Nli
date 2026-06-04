"""Unit tests for get_material_stock tool."""
import pytest
from app.tools.get_material_stock import get_material_stock


@pytest.mark.asyncio
async def test_get_material_stock_returns_all_categories():
    result = await get_material_stock.ainvoke({"material": "FG-001", "plant": "1010"})
    assert result["material"] == "FG-001"
    assert result["plant"] == "1010"
    assert "unrestricted_stock" in result
    assert "in_transit_stock" in result
    assert "reserved_stock" in result
    assert "safety_stock" in result
    assert "unit_of_measure" in result


@pytest.mark.asyncio
async def test_get_material_stock_with_storage_location():
    result = await get_material_stock.ainvoke(
        {"material": "FG-001", "plant": "1010", "storage_location": "0001"}
    )
    assert result["storage_location"] == "0001"
    assert "error" not in result


@pytest.mark.asyncio
async def test_get_material_stock_missing_material_returns_error():
    result = await get_material_stock.ainvoke({"material": "", "plant": "1010"})
    assert result["error"] == "INVALID_INPUT"
    assert "material" in result["message"].lower()


@pytest.mark.asyncio
async def test_get_material_stock_missing_plant_returns_error():
    result = await get_material_stock.ainvoke({"material": "FG-001", "plant": ""})
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_get_material_stock_top_limit_applied():
    result = await get_material_stock.ainvoke({"material": "RM-100", "plant": "2000"})
    assert result["top_limit_applied"] == 100
