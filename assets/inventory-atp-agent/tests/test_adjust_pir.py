"""Unit tests for adjust_pir tool."""
import pytest
from app.tools.adjust_pir import adjust_pir


@pytest.mark.asyncio
async def test_adjust_pir_success():
    result = await adjust_pir.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "version": "00",
            "requirement_date": "2026-06-30",
            "new_quantity": 100.0,
            "approved_by": "PLANNER_USER",
        }
    )
    assert "new_quantity" in result
    assert result["new_quantity"] == 100.0
    assert result["material"] == "FG-001"
    assert "document_number" in result
    assert result["approved_by"] == "PLANNER_USER"


@pytest.mark.asyncio
async def test_adjust_pir_zero_quantity_allowed():
    result = await adjust_pir.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "version": "00",
            "requirement_date": "2026-07-31",
            "new_quantity": 0.0,
        }
    )
    assert "error" not in result
    assert result["new_quantity"] == 0.0


@pytest.mark.asyncio
async def test_adjust_pir_missing_material_returns_error():
    result = await adjust_pir.ainvoke(
        {
            "material": "",
            "plant": "1010",
            "version": "00",
            "requirement_date": "2026-06-30",
            "new_quantity": 100.0,
        }
    )
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_adjust_pir_negative_quantity_returns_error():
    result = await adjust_pir.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "version": "00",
            "requirement_date": "2026-06-30",
            "new_quantity": -10.0,
        }
    )
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_adjust_pir_returns_timestamp():
    result = await adjust_pir.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "version": "00",
            "requirement_date": "2026-06-30",
            "new_quantity": 50.0,
        }
    )
    assert "updated_at" in result
    assert result["updated_at"].endswith("Z")
