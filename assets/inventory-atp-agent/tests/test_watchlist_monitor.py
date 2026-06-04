"""Unit tests for watchlist_monitor."""
import pytest
from unittest.mock import AsyncMock
from app.tools.watchlist_monitor import check_watchlist, compute_breach_severity


# --- Unit tests for severity classifier ---

def test_severity_high_when_stock_zero():
    assert compute_breach_severity(0.0, 80.0) == "HIGH"


def test_severity_high_when_below_25_percent():
    assert compute_breach_severity(10.0, 80.0) == "HIGH"


def test_severity_medium_when_between_25_and_75_percent():
    assert compute_breach_severity(40.0, 80.0) == "MEDIUM"


def test_severity_low_when_above_75_percent():
    assert compute_breach_severity(70.0, 80.0) == "LOW"


def test_severity_zero_threshold_returns_low():
    assert compute_breach_severity(100.0, 0.0) == "LOW"


# --- Integration tests for check_watchlist ---

@pytest.mark.asyncio
async def test_watchlist_detects_breach():
    mock_fetcher = AsyncMock(return_value={
        "material": "FG-001",
        "plant": "1010",
        "unrestricted_stock": 20.0,
        "unit_of_measure": "EA",
    })
    entries = [
        {"material": "FG-001", "plant": "1010", "safety_stock_threshold": 80.0, "sla_date": "2026-06-10"}
    ]
    alerts = await check_watchlist(entries, mock_fetcher)
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "SAFETY_STOCK_BREACH"
    assert alerts[0]["material"] == "FG-001"
    assert alerts[0]["breach_severity"] in ("HIGH", "MEDIUM", "LOW")


@pytest.mark.asyncio
async def test_watchlist_no_alert_when_stock_sufficient():
    mock_fetcher = AsyncMock(return_value={
        "material": "FG-001",
        "plant": "1010",
        "unrestricted_stock": 200.0,
        "unit_of_measure": "EA",
    })
    entries = [
        {"material": "FG-001", "plant": "1010", "safety_stock_threshold": 80.0, "sla_date": "2026-06-10"}
    ]
    alerts = await check_watchlist(entries, mock_fetcher)
    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_watchlist_skips_entry_with_api_error():
    mock_fetcher = AsyncMock(return_value={"error": "API_UNAVAILABLE"})
    entries = [
        {"material": "FG-001", "plant": "1010", "safety_stock_threshold": 80.0, "sla_date": "2026-06-10"}
    ]
    alerts = await check_watchlist(entries, mock_fetcher)
    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_watchlist_skips_entry_missing_material():
    mock_fetcher = AsyncMock(return_value={"unrestricted_stock": 10.0})
    entries = [{"material": "", "plant": "1010", "safety_stock_threshold": 80.0}]
    alerts = await check_watchlist(entries, mock_fetcher)
    assert len(alerts) == 0
    mock_fetcher.assert_not_called()


@pytest.mark.asyncio
async def test_watchlist_high_severity_breach():
    mock_fetcher = AsyncMock(return_value={
        "material": "FG-001",
        "plant": "1010",
        "unrestricted_stock": 5.0,
    })
    entries = [
        {"material": "FG-001", "plant": "1010", "safety_stock_threshold": 80.0, "sla_date": "2026-06-10"}
    ]
    alerts = await check_watchlist(entries, mock_fetcher)
    assert alerts[0]["breach_severity"] == "HIGH"
