"""Unit tests for run_atp_check tool."""
import pytest
from app.tools.run_atp_check import run_atp_check


@pytest.mark.asyncio
async def test_atp_check_full_confirmation():
    result = await run_atp_check.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "requested_quantity": 50.0,
            "requested_date": "2026-06-10",
        }
    )
    assert result["is_fully_confirmed"] is True
    assert result["confirmed_quantity"] == 50.0
    assert result["unfulfilled_quantity"] == 0.0
    assert result["atp_date"] == "2026-06-10"


@pytest.mark.asyncio
async def test_atp_check_with_order_context():
    result = await run_atp_check.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "requested_quantity": 100.0,
            "requested_date": "2026-06-15",
            "sales_order": "4500012345",
            "sales_order_item": "10",
        }
    )
    assert result["sales_order"] == "4500012345"
    assert result["sales_order_item"] == "10"
    assert "error" not in result


@pytest.mark.asyncio
async def test_atp_check_invalid_quantity_returns_error():
    result = await run_atp_check.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "requested_quantity": 0.0,
            "requested_date": "2026-06-10",
        }
    )
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_atp_check_missing_date_returns_error():
    result = await run_atp_check.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "requested_quantity": 50.0,
            "requested_date": "",
        }
    )
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_atp_check_missing_material_returns_error():
    result = await run_atp_check.ainvoke(
        {
            "material": "",
            "plant": "1010",
            "requested_quantity": 50.0,
            "requested_date": "2026-06-10",
        }
    )
    assert result["error"] == "INVALID_INPUT"
