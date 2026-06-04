# Inventory ATP Agentic Copilot

An AI agent that proactively ensures order fulfillment and prevents stockouts by perceiving real-time S/4HANA inventory signals, planning multi-step ATP checks and simulations, and executing policy-controlled actions with mandatory human approvals.

## Overview

Uses A2A Protocol, LangGraph, LiteLLM, and SAP Cloud SDK.

## Structure

- `app/main.py` - A2A server entry
- `app/agent_executor.py` - Request handling
- `app/agent.py` - Agent logic
