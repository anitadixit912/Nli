"""Unit tests for flag_po_expedite tool."""
import pytest
from app.tools.flag_po_expedite import flag_po_expedite


@pytest.mark.asyncio
async def test_flag_po_expedite_success():
    result = await flag_po_expedite.ainvoke(
        {
            "purchase_order": "4500099999",
            "purchase_order_item": "00010",
            "expedite_reason": "Safety stock breach at Plant 1010",
            "buyer_note": "Please advance by 5 days",
            "approved_by": "PROCUREMENT_MGR",
        }
    )
    assert result["status"] == "PENDING_BUYER_ACTION"
    assert result["purchase_order"] == "4500099999"
    assert result["approved_by"] == "PROCUREMENT_MGR"
    assert "flagged_at" in result


@pytest.mark.asyncio
async def test_flag_po_expedite_without_optional_fields():
    result = await flag_po_expedite.ainvoke(
        {
            "purchase_order": "4500099999",
            "purchase_order_item": "00010",
            "expedite_reason": "Stockout risk",
        }
    )
    assert result["status"] == "PENDING_BUYER_ACTION"
    assert "error" not in result


@pytest.mark.asyncio
async def test_flag_po_expedite_missing_po_returns_error():
    result = await flag_po_expedite.ainvoke(
        {
            "purchase_order": "",
            "purchase_order_item": "00010",
            "expedite_reason": "Stockout risk",
        }
    )
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_flag_po_expedite_missing_reason_returns_error():
    result = await flag_po_expedite.ainvoke(
        {
            "purchase_order": "4500099999",
            "purchase_order_item": "00010",
            "expedite_reason": "",
        }
    )
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_flag_po_expedite_returns_timestamp():
    result = await flag_po_expedite.ainvoke(
        {
            "purchase_order": "4500099999",
            "purchase_order_item": "00010",
            "expedite_reason": "Urgent",
        }
    )
    assert result["flagged_at"].endswith("Z")
