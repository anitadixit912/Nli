import logging
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Literal, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langchain_litellm import ChatLiteLLM
from langgraph.checkpoint.memory import InMemorySaver
from opentelemetry import trace
from sap_cloud_sdk.agent_decorators import agent_config, agent_model, prompt_section

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# ---------------------------------------------------------------------------
# Role-based tool access policy
# Keys: user role strings. Values: set of allowed write-tool names.
# Read-only tools are always accessible to all roles.
# ---------------------------------------------------------------------------
READ_ONLY_TOOLS = {
    "get_material_stock",
    "get_demand_elements",
    "run_atp_check",
    "get_planned_orders",
    "propose_corrective_actions",
}

WRITE_TOOLS_BY_ROLE: dict[str, set[str]] = {
    "PLANNER": {
        "create_stock_transport_order",
        "convert_planned_order",
        "adjust_pir",
        "flag_po_expedite",
    },
    "SALES_OPS": set(),
    "CUSTOMER_SERVICE": set(),
    "PROCUREMENT_MANAGER": {"flag_po_expedite"},
}

THREAD_TTL_SECONDS = 3600  # evict threads inactive for 1 hour


@agent_model(
    key="config.model",
    label="LLM Model",
    description="The language model powering this agent",
)
def get_model_name() -> str:
    return "sap/anthropic--claude-4.5-sonnet"


@agent_config(
    key="config.temperature",
    label="LLM Temperature",
    description="Controls randomness of responses (0.0 = deterministic, 1.0 = creative)",
)
def get_temperature() -> float:
    return 0.0


@prompt_section(
    key="prompts.system",
    label="System Prompt",
    description="The full system prompt defining the agent's role and behavior",
    validation={"format": "markdown", "max_length": 5000},
)
def get_system_prompt() -> str:
    return """You are the Inventory ATP Agentic Copilot for SAP S/4HANA Cloud Public Edition.
You proactively ensure order fulfillment and prevent stockouts by perceiving real-time inventory
signals, planning multi-step checks and simulations, and executing policy-controlled actions
with mandatory human approvals.

## Sub-Intents You Handle

1. **Explain_Stock_Drop**: Explain why on-hand stock is declining for a material/plant/sloc.
   - Call get_material_stock to read current stock by category.
   - Call get_demand_elements to retrieve demand and supply elements from MRP.
   - Identify the primary cause (e.g. large sales order, low safety stock, no open supply).
   - Present a clear natural-language explanation with the contributing demand lines.

2. **Check_Order_Feasibility**: Determine if an order/schedule line can be fulfilled.
   - Call run_atp_check with the material, plant, requested quantity, and required date.
   - Report confirmed quantity, earliest ATP date, unfulfilled quantity, and reason codes.
   - If ATP is partial, explain the shortfall and offer to simulate options.

3. **Protect_Service_Level**: Monitor prioritised materials and alert on ATP/stock risk.
   - When asked to monitor a material, confirm the watchlist entry has been noted.
   - Proactive alerts are delivered via the BTP Notifications layer; describe what would trigger one.

4. **Simulate_Options**: Propose and rank corrective alternatives.
   - Call propose_corrective_actions with material, plant, shortfall quantity, and required date.
   - Present options ranked by ascending estimated lead days with trade-offs.

5. **Execute_With_Approval**: Present an approval card and execute approved write-back actions.
   - BEFORE calling any write tool (create_stock_transport_order, convert_planned_order,
     adjust_pir, flag_po_expedite), you MUST present the action card to the user and
     wait for their explicit "confirm" or "reject" in the SAME conversation turn.
   - Approval card format:
       ACTION: <action type>
       DETAILS: <key parameters>
       ESTIMATED IMPACT: <quantity, date, plant>
       Please reply CONFIRM to execute or REJECT to cancel.
   - Only call the write tool AFTER the user has replied CONFIRM in this turn.
   - If the user replies REJECT, do NOT call the write tool. Offer to propose an alternative.
   - Approval is valid for the current turn only. Expired approvals require re-confirmation.

## CRITICAL Rules

- NEVER hallucinate quantities, dates, document numbers, or material codes.
  Only cite values that were returned directly by a tool call.
- Always set $top=100 (or equivalent limit parameter) on every tool call that accepts it.
  Inform the user if the result may be truncated because the limit was applied.
- If a tool returns an error, report the error clearly. Do NOT fabricate a result.
- When ATP simulation returns partial or ambiguous results, explicitly state the uncertainty
  before proposing any action.
- If the user's role restricts a write action, explain the restriction and suggest they
  contact the appropriate role (e.g. PLANNER) to execute it.
"""


@dataclass
class AgentResponse:
    status: Literal["input_required", "completed", "error"]
    message: str


class SampleAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.llm = ChatLiteLLM(model=get_model_name(), temperature=get_temperature())
        self._checkpointer = InMemorySaver()
        self._last_active: dict[str, float] = {}
        self._summarization_middleware = SummarizationMiddleware(
            model=self.llm,
            trigger=("tokens", 100_000),
        )
        self._graph_cache: dict[str, object] = {}

    def _touch(self, thread_id: str) -> None:
        now = time.monotonic()
        expired = [
            tid
            for tid, ts in list(self._last_active.items())
            if now - ts > THREAD_TTL_SECONDS
        ]
        for tid in expired:
            self._checkpointer.delete_thread(tid)
            del self._last_active[tid]
            logger.info("Evicted inactive thread: %s", tid)
        self._last_active[thread_id] = now

    def _filter_tools_by_role(
        self, tools: Sequence[BaseTool], role: str | None
    ) -> list[BaseTool]:
        """Return tools permitted for the given role. Defaults to read-only."""
        allowed_write = WRITE_TOOLS_BY_ROLE.get((role or "").upper(), set())
        allowed = READ_ONLY_TOOLS | allowed_write
        filtered = [t for t in tools if t.name in allowed]
        removed = [t.name for t in tools if t.name not in allowed]
        if removed:
            logger.info(
                "Role %s: restricted write tools removed: %s", role, removed
            )
        return filtered

    @tracer.start_as_current_span("inventory-atp-agent._run_agent")
    async def _run_agent(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool],
        role: str | None,
    ) -> str:
        """Core reasoning loop — instrumented with OTel. Extracted from stream() to avoid
        GeneratorExit context errors when using start_as_current_span inside async generators."""
        permitted_tools = self._filter_tools_by_role(tools, role)

        graph = create_agent(
            self.llm,
            tools=permitted_tools,
            system_prompt=get_system_prompt(),
            checkpointer=self._checkpointer,
            middleware=[self._summarization_middleware],
        )
        config = {"configurable": {"thread_id": context_id}}
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=query)]}, config
        )
        return result["messages"][-1].content

    async def stream(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
        role: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream agent responses. All business logic is delegated to _run_agent()."""
        self._touch(context_id)
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Processing your inventory query...",
        }
        try:
            if tools:
                logger.info(
                    "Running agent with %d tool(s): %s",
                    len(tools),
                    [t.name for t in tools],
                )
            else:
                logger.info("Running agent without tools")

            response = await self._run_agent(
                query, context_id, tools or [], role
            )
            self._touch(context_id)
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": response,
            }
        except Exception as e:
            logger.exception("Agent stream() failed")
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": (
                    f"I encountered an error while processing your request: {str(e)}. "
                    "Please try again."
                ),
            }

    async def invoke(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
        role: str | None = None,
    ) -> AgentResponse:
        """Invoke agent and return final response."""
        last: dict = {}
        async for chunk in self.stream(query, context_id, tools=tools, role=role):
            last = chunk
        if last.get("is_task_complete"):
            return AgentResponse(status="completed", message=last["content"])
        if last.get("require_user_input"):
            return AgentResponse(status="input_required", message=last["content"])
        return AgentResponse(status="error", message=last.get("content", "Unknown error"))
