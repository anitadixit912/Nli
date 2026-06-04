"""Unit tests for convert_planned_order tool."""
import pytest
from app.tools.convert_planned_order import convert_planned_order


@pytest.mark.asyncio
async def test_convert_to_production_order():
    result = await convert_planned_order.ainvoke(
        {
            "planned_order": "0000012345",
            "conversion_order_type": "production",
            "approved_by": "PLANNER_USER",
        }
    )
    assert result["status"] == "CONVERTED"
    assert result["order_type"] == "production"
    assert "PRD_" in result["converted_document_number"]
    assert result["approved_by"] == "PLANNER_USER"


@pytest.mark.asyncio
async def test_convert_to_purchase_order():
    result = await convert_planned_order.ainvoke(
        {
            "planned_order": "0000099999",
            "conversion_order_type": "purchase",
        }
    )
    assert result["status"] == "CONVERTED"
    assert "PO_" in result["converted_document_number"]


@pytest.mark.asyncio
async def test_convert_missing_planned_order_returns_error():
    result = await convert_planned_order.ainvoke({"planned_order": ""})
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_convert_invalid_order_type_returns_error():
    result = await convert_planned_order.ainvoke(
        {"planned_order": "0000012345", "conversion_order_type": "invalid_type"}
    )
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_convert_returns_timestamp():
    result = await convert_planned_order.ainvoke({"planned_order": "0000012345"})
    assert "converted_at" in result
    assert result["converted_at"].endswith("Z")
