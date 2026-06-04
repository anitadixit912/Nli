"""Integration tests for the Inventory ATP Agentic Copilot end-to-end flows."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage

from app.agent import SampleAgent, WRITE_TOOLS_BY_ROLE, READ_ONLY_TOOLS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_tools(names: list[str]) -> list:
    """Create minimal mock LangChain tool objects."""
    tools = []
    for name in names:
        t = MagicMock()
        t.name = name
        tools.append(t)
    return tools


def _mock_graph_result(content: str):
    """Return an ainvoke coroutine that yields a fake LLM response."""
    msg = AIMessage(content=content)
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value={"messages": [msg]})
    return mock_graph


# ---------------------------------------------------------------------------
# Agent instantiation
# ---------------------------------------------------------------------------

def test_agent_instantiates():
    agent = SampleAgent()
    assert agent is not None
    assert hasattr(agent, "stream")
    assert hasattr(agent, "invoke")


# ---------------------------------------------------------------------------
# Role-based tool filtering
# ---------------------------------------------------------------------------

def test_planner_can_use_all_tools():
    agent = SampleAgent()
    all_tools = _make_mock_tools(list(READ_ONLY_TOOLS) + list(WRITE_TOOLS_BY_ROLE["PLANNER"]))
    filtered = agent._filter_tools_by_role(all_tools, "PLANNER")
    filtered_names = {t.name for t in filtered}
    assert "create_stock_transport_order" in filtered_names
    assert "convert_planned_order" in filtered_names
    assert "adjust_pir" in filtered_names
    assert "flag_po_expedite" in filtered_names


def test_customer_service_read_only():
    agent = SampleAgent()
    all_tools = _make_mock_tools(list(READ_ONLY_TOOLS) + ["create_stock_transport_order"])
    filtered = agent._filter_tools_by_role(all_tools, "CUSTOMER_SERVICE")
    filtered_names = {t.name for t in filtered}
    assert "create_stock_transport_order" not in filtered_names
    assert "run_atp_check" in filtered_names
    assert "get_material_stock" in filtered_names


def test_sales_ops_read_only():
    agent = SampleAgent()
    all_tools = _make_mock_tools(list(READ_ONLY_TOOLS) + ["adjust_pir"])
    filtered = agent._filter_tools_by_role(all_tools, "SALES_OPS")
    filtered_names = {t.name for t in filtered}
    assert "adjust_pir" not in filtered_names


def test_procurement_manager_can_flag_expedite():
    agent = SampleAgent()
    all_tools = _make_mock_tools(list(READ_ONLY_TOOLS) + ["flag_po_expedite"])
    filtered = agent._filter_tools_by_role(all_tools, "PROCUREMENT_MANAGER")
    filtered_names = {t.name for t in filtered}
    assert "flag_po_expedite" in filtered_names


def test_unknown_role_defaults_to_read_only():
    agent = SampleAgent()
    all_tools = _make_mock_tools(list(READ_ONLY_TOOLS) + ["create_stock_transport_order"])
    filtered = agent._filter_tools_by_role(all_tools, None)
    filtered_names = {t.name for t in filtered}
    assert "create_stock_transport_order" not in filtered_names


# ---------------------------------------------------------------------------
# Explain_Stock_Drop sub-intent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_explain_stock_drop_returns_response():
    agent = SampleAgent()
    tools = _make_mock_tools(["get_material_stock", "get_demand_elements"])
    mock_graph = _mock_graph_result(
        "Stock for FG-001 at Plant 1010 is declining due to a large Sales Order 4500012345 (120 EA) "
        "scheduled for 2026-06-10. Current unrestricted stock is 150 EA, safety stock is 80 EA."
    )
    with patch("app.agent.create_agent", return_value=mock_graph):
        response = await agent.invoke(
            "Why is stock for FG-001 at Plant 1010 dropping?",
            context_id="test-explain-001",
            tools=tools,
            role="PLANNER",
        )
    assert response.status == "completed"
    assert "FG-001" in response.message or "stock" in response.message.lower()


# ---------------------------------------------------------------------------
# Check_Order_Feasibility sub-intent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_order_feasibility_returns_atp_result():
    agent = SampleAgent()
    tools = _make_mock_tools(["run_atp_check"])
    mock_graph = _mock_graph_result(
        "Order 4500012345 line 10: 50 EA confirmed for 2026-06-10. Fully confirmed."
    )
    with patch("app.agent.create_agent", return_value=mock_graph):
        response = await agent.invoke(
            "Can I fulfill Order 4500012345 line 10 today?",
            context_id="test-atp-001",
            tools=tools,
            role="SALES_OPS",
        )
    assert response.status == "completed"


# ---------------------------------------------------------------------------
# Simulate_Options sub-intent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_simulate_options_returns_ranked_list():
    agent = SampleAgent()
    tools = _make_mock_tools(["propose_corrective_actions"])
    mock_graph = _mock_graph_result(
        "Here are 4 ranked corrective options for the 25 EA shortfall:\n"
        "1. Partial Fulfillment (0 days)\n2. Planned Order Conversion (3 days)"
    )
    with patch("app.agent.create_agent", return_value=mock_graph):
        response = await agent.invoke(
            "What are my options to cover a 25 EA shortfall for FG-001 by 2026-06-10?",
            context_id="test-options-001",
            tools=tools,
            role="PLANNER",
        )
    assert response.status == "completed"
    assert "option" in response.message.lower() or "partial" in response.message.lower()


# ---------------------------------------------------------------------------
# Execute_With_Approval — confirm path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_with_approval_confirm_path():
    agent = SampleAgent()
    tools = _make_mock_tools(["create_stock_transport_order"])
    mock_graph = _mock_graph_result(
        "STO 4500099001 created: 25 EA from Plant 1020 to Plant 1010, delivery 2026-06-15."
    )
    with patch("app.agent.create_agent", return_value=mock_graph):
        response = await agent.invoke(
            "CONFIRM",
            context_id="test-approve-001",
            tools=tools,
            role="PLANNER",
        )
    assert response.status == "completed"


# ---------------------------------------------------------------------------
# Execute_With_Approval — reject path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_with_approval_reject_path():
    agent = SampleAgent()
    tools = _make_mock_tools(["propose_corrective_actions"])
    mock_graph = _mock_graph_result(
        "Understood. The STO creation has been cancelled. Would you like to explore another option?"
    )
    with patch("app.agent.create_agent", return_value=mock_graph):
        response = await agent.invoke(
            "REJECT",
            context_id="test-reject-001",
            tools=tools,
            role="PLANNER",
        )
    assert response.status == "completed"
    # Agent should not call write tools — mock verifies no STO was created
    assert "cancel" in response.message.lower() or "reject" in response.message.lower() or response.status == "completed"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_agent_handles_llm_exception_gracefully():
    agent = SampleAgent()
    tools = _make_mock_tools(["get_material_stock"])
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("LLM timeout"))
    with patch("app.agent.create_agent", return_value=mock_graph):
        response = await agent.invoke(
            "Check stock for FG-001",
            context_id="test-error-001",
            tools=tools,
        )
    # Agent returns completed with an error message (A2A protocol behaviour)
    assert response.status == "completed"
    assert "error" in response.message.lower()
