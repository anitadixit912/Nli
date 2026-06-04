# Material Stock Level Monitoring Dashboard

A BTP-hosted dashboard for monitoring material inventory status across storage locations, distinguishing sufficient-stock materials from those at near-stockout risk.

## Business challenge

Warehouse managers, supply chain planners, plant managers, and procurement officers lack a consolidated real-time view of material stock health. They need to quickly identify which materials have sufficient inventory and which are approaching critical stock levels — either by falling below their reorder point or by dropping below a defined percentage of their safety stock — along with the exact storage location of at-risk materials. In addition, users need an intelligent assistant embedded in the dashboard that can answer natural-language questions about stock status and provide actionable replenishment recommendations (e.g. "Which materials should I reorder today?", "What is the most critical item in plant 1000?").

## Key Milestones

- **Data loaded**: Material stock data successfully retrieved from SAP S/4HANA Cloud Public Edition via the Material Stock Read API.
- **Stock classification applied**: Each material is classified as "Sufficient" or "Nearly Out of Stock" based on reorder-point and safety-stock-percentage thresholds.
- **Dashboard rendered**: Two lists are presented — sufficient-stock materials and at-risk materials with storage location — visible to all target user roles.
- **Chat query received**: User submits a natural-language question via the chatbox.
- **Recommendation generated**: AI agent analyzes current stock data and returns a structured recommendation to the user.

## Business Architecture (RBA)

### End-to-End Process

Plan to Fulfill (E2E)

### Process Hierarchy

```
Plan to Fulfill (E2E)
└── Manage Fulfillment (generic)
    └── Manage supply chain data and operations (BPS-342)
        └── Manage inventory and warehouse operations
        └── Balance inventory
```

### Summary

The dashboard directly supports "Manage supply chain data and operations" within the Plan to Fulfill E2E by providing real-time inventory visibility that enables timely replenishment decisions.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ---- | ------------------- |
| Read material stock levels by storage location | SAP S/4HANA Cloud Public Edition – Inventory Analytics and Control (SC765) | `sap.s4:apiResource:API_MATERIAL_STOCK_SRV:v1` | — | No | OData Read API available; no MCP server found — direct API integration required |
| Classify materials as sufficient vs. nearly out of stock | SAP S/4HANA Cloud Public Edition – Inventory Analytics and Control (SC765) | `sap.s4:apiResource:API_MATERIAL_STOCK_SRV:v1` | — | Maybe | Reorder point is available in the API; safety stock % threshold logic requires custom classification in the backend |
| Display storage location for at-risk materials | SAP S/4HANA Cloud Public Edition – Internal Warehouse Management (SC841) | `sap.s4:apiResource:API_MATERIAL_STOCK_SRV:v1` | — | No | Storage location is a standard field in the Material Stock API |
| Configurable threshold (safety stock %) | Not covered by standard SAP reporting | — | — | Yes | Threshold configuration UI must be custom-built |
| Consolidated dashboard for multiple user roles | SAP Analytics Cloud (optional) | — | — | Yes | Standard SAP Analytics Cloud would require separate licensing; a custom BTP dashboard is more targeted |
| Natural-language stock recommendations chatbox | Not covered by standard SAP products | — | — | Yes | Custom AI agent required; LLM via SAP Generative AI Hub; agent has tool access to classified stock data |

### Key findings

- The **Material Stock - Read** OData API (`API_MATERIAL_STOCK_SRV`) provides unrestricted stock, storage location, and reorder point data — sufficient for the dashboard's core requirements.
- No MCP server exists for this API; integration must be done via direct OData calls from a CAP backend.
- Safety stock percentage threshold classification is not a native S/4HANA concept and must be implemented as custom backend logic.
- SAP S/4HANA Cloud Public Edition's **Inventory Analytics and Control** capability (SC765) is the primary standard capability supporting this use case.
- SAP Analytics Cloud could cover this use case but adds licensing overhead; a focused BTP Extension is a leaner and more targeted fit.
- All four target user roles (Warehouse Manager, Supply Chain Planner, Plant Manager, Procurement Officer) are served by a single shared dashboard view.

## Recommendations

### Custom Inventory Stock Dashboard on SAP BTP

#### Executive Summary

BTP Extension with CAP backend and React frontend connected to S/4HANA

#### Recommended Solution

Build a BTP Extension consisting of:
1. A **CAP Node.js backend** that connects to the SAP S/4HANA Cloud Public Edition **Material Stock - Read** OData API (`API_MATERIAL_STOCK_SRV`), retrieves stock data per material and storage location, applies classification logic (sufficient vs. nearly out of stock) based on configurable thresholds (reorder point breach and safety stock percentage), and exposes a custom OData/REST service.
2. A **React frontend** (with SAP UI5 Web Components) deployed on BTP that renders two panels: a table of sufficient-stock materials and a highlighted table of nearly-out-of-stock materials with their storage location and risk indicator.

#### Problem Statement

Inventory managers and planners have no single consolidated view to distinguish healthy stock from at-risk stock, forcing them to navigate multiple S/4HANA transactions to manually assess stock status.

#### Affected User Roles

- Warehouse / Inventory Manager
- Supply Chain Planner
- Plant Manager
- Procurement Officer

#### Important factors

##### Real-time data from S/4HANA Cloud Public Edition

The Material Stock OData API provides live unrestricted and restricted stock quantities per material and storage location, ensuring the dashboard reflects the current inventory state.

##### Configurable risk thresholds

Two threshold types are supported: (1) stock quantity falls below the material's reorder point, and (2) current stock drops below a user-defined percentage of the safety stock. These thresholds can be adjusted without code changes.

#### Potential risks

##### API connectivity and authorisation

The CAP service must be configured with the correct S/4HANA Cloud destination and OAuth credentials on BTP. Misconfiguration will prevent data from loading.

##### Safety stock data availability

Safety stock and reorder point fields must be maintained in the S/4HANA material master; if they are missing for a material, classification may default to "sufficient" incorrectly.

#### Recommended solution category

BTP Extension, AI Agent

#### Intent fit
95%
