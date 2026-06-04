"""Unit tests for propose_corrective_actions tool."""
import pytest
from app.tools.propose_corrective_actions import propose_corrective_actions


@pytest.mark.asyncio
async def test_propose_returns_ranked_options():
    result = await propose_corrective_actions.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "shortfall_quantity": 25.0,
            "required_date": "2026-06-10",
        }
    )
    assert "options" in result
    options = result["options"]
    assert len(options) >= 2
    # Verify ranking is ascending by lead days
    lead_days = [o["estimated_lead_days"] for o in options]
    assert lead_days == sorted(lead_days)


@pytest.mark.asyncio
async def test_propose_all_options_require_approval():
    result = await propose_corrective_actions.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "shortfall_quantity": 50.0,
            "required_date": "2026-06-15",
        }
    )
    for option in result["options"]:
        assert option["requires_approval"] is True


@pytest.mark.asyncio
async def test_propose_option_types_include_key_strategies():
    result = await propose_corrective_actions.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "shortfall_quantity": 25.0,
            "required_date": "2026-06-10",
        }
    )
    option_types = {o["type"] for o in result["options"]}
    assert "PARTIAL_FULFILLMENT" in option_types
    assert "PLANNED_ORDER_CONVERSION" in option_types


@pytest.mark.asyncio
async def test_propose_invalid_shortfall_returns_error():
    result = await propose_corrective_actions.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "shortfall_quantity": 0.0,
            "required_date": "2026-06-10",
        }
    )
    assert result["error"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_propose_missing_date_returns_error():
    result = await propose_corrective_actions.ainvoke(
        {
            "material": "FG-001",
            "plant": "1010",
            "shortfall_quantity": 25.0,
            "required_date": "",
        }
    )
    assert result["error"] == "INVALID_INPUT"
