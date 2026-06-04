"""Unit tests for create_stock_transport_order tool."""
import pytest
from app.tools.create_stock_transport_order import create_stock_transport_order


@pytest.mark.asyncio
async def test_create_sto_success():
    result = await create_stock_transport_order.ainvoke(
        {
            "material": "FG-001",
            "supplying_plant": "1020",
            "receiving_plant": "1010",
            "quantity": 50.0,
            "unit": "EA",
            "delivery_date": "2026-06-15",
            "approved_by": "PLANNER_USER",
        }
    )
    assert result["status"] == "CREATED"
    assert result["material"] == "FG-001"
    assert result["approved_by"] == "PLANNER_USER"
    assert "sto_document_number" in result
    assert "created_at" in result


@pytest.mark.asyncio
async def test_create_sto_missing_material_returns_error():
    result = await create_stock_transport_order.ainvoke(
        {
            "material": "",
            "supplying_plant": "1020",
            "receiving_plant": "1010",
            "quantity": 50.0,
            "unit": "EA",
            "delivery_date": "2026-06-15",
        }
    )
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_create_sto_zero_quantity_returns_error():
    result = await create_stock_transport_order.ainvoke(
        {
            "material": "FG-001",
            "supplying_plant": "1020",
            "receiving_plant": "1010",
            "quantity": 0.0,
            "unit": "EA",
            "delivery_date": "2026-06-15",
        }
    )
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_create_sto_returns_timestamp():
    result = await create_stock_transport_order.ainvoke(
        {
            "material": "FG-001",
            "supplying_plant": "1020",
            "receiving_plant": "1010",
            "quantity": 25.0,
            "unit": "EA",
            "delivery_date": "2026-06-20",
        }
    )
    assert "created_at" in result
    assert result["created_at"].endswith("Z")
