# Product Requirements Document (PRD)

**Title:** Material Stock Level Monitoring Dashboard  
**Date:** 2026-06-04  
**Owner:** Supply Chain / Inventory Management Team  
**Solution Category:** BTP Extension

---

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Inventory managers and planners waste time navigating multiple S/4HANA transactions to assess stock health. This dashboard provides a single, real-time view that separates materials with sufficient stock from those approaching critical levels — enabling faster, better-informed replenishment decisions.

**Business Need:**  
There is no consolidated view in SAP S/4HANA that surfaces stock risk at a glance, split by storage location. Users must run multiple reports, cross-reference safety stock and reorder point data manually, and repeat this exercise frequently. This creates operational lag and risk of stockouts going unnoticed until it is too late.

**Expected Value:**

- Reduced time to identify at-risk materials (target: from multiple transactions to a single screen)
- Proactive replenishment decisions before stockout occurs
- Improved stock visibility for plant managers and procurement officers

**Product Objectives (Prioritized):**

1. Provide a real-time, categorised view of all materials by stock health status (sufficient vs. nearly out of stock)
2. Display the storage location for all at-risk materials to enable targeted replenishment action
3. Support configurable risk thresholds (reorder point breach and safety stock percentage drop) so the classification adapts to each plant's standards

---

## User Profiles & Personas

### Primary Persona: Maria – Warehouse / Inventory Manager

Maria is a 38-year-old inventory manager responsible for daily stock oversight at a manufacturing plant. She starts each morning by manually checking several MM reports in S/4HANA to see which materials are running low. She is comfortable with SAP transactions but finds it time-consuming to cross-reference stock levels, reorder points, and safety stock values across multiple screens. Her success is measured by zero stockout events and accurate inventory records. She needs a fast overview that tells her what is fine and what needs attention — without digging into individual material records.

### Secondary Persona: Lars – Supply Chain Planner

Lars is a 44-year-old supply chain planner who sets safety stock and reorder point parameters for materials. He monitors stock trends and coordinates with procurement to trigger replenishment. His pain point is a lack of early visibility into materials trending toward risk before they formally breach thresholds. He wants to see materials approaching risk — not just those already below their reorder point.

### Other User Types

- **Plant Manager**: Needs a high-level status view to confirm operations are not at risk; reads the dashboard but does not act on it directly.
- **Procurement Officer**: Uses the at-risk materials list to trigger purchase requisitions or expedite existing purchase orders.

---

## User Goals & Tasks

### For Maria (Inventory Manager):

**Goals:**
- Know immediately which materials are at risk of running out, by storage location
- Confirm which materials have healthy stock levels without manually checking each one

**Key Tasks:**
- Open the dashboard each morning to review the two stock status panels
- Filter the at-risk list by plant or storage location to focus on her area of responsibility
- Adjust the safety stock threshold percentage to match current operational targets

### For Lars (Supply Chain Planner):

**Goals:**
- Detect materials trending toward risk before a formal threshold breach
- Validate that reorder points and safety stock parameters are having the intended effect

**Key Tasks:**
- Review the "nearly out of stock" list to identify patterns or recurring at-risk materials
- Use the dashboard to cross-check whether updated parameters are reflected in the current classification

---

## Product Principles

1. **Clarity over completeness**: Show only what is needed to act — two clearly labelled lists, not a data dump.
2. **Real-time accuracy**: Data must reflect the current S/4HANA stock position; no stale caches that mislead users.
3. **Configurable thresholds**: Threshold values are adjustable without code changes, so the dashboard remains useful as inventory policies evolve.
4. **Role-neutral access**: All four target user roles see the same dashboard; no role-specific filtering logic at launch.

---

## Business Context

**Current State:**  
Users rely on standard SAP MM reports (MB52, MB53, MD04) run on demand. These reports are not combined, require SAP GUI access, and do not provide a visual at-a-glance classification of stock health. Risk identification is manual and time-consuming.

**Strategic Alignment:**  
Supports the Plan to Fulfill end-to-end process by improving inventory visibility and enabling proactive replenishment decisions — a key capability under "Manage supply chain data and operations" (BPS-342).

**Success Criteria:**

- All target user roles can access the dashboard via a BTP-hosted URL without SAP GUI access
- Materials are correctly classified as sufficient or at-risk based on configured thresholds
- Storage location is visible for all at-risk materials
- Threshold configuration is accessible and persisted without developer intervention

---

## Goals and Non-Goals

### Goals (In Scope)

- Display a list of materials with sufficient stock (stock above reorder point and safety stock threshold)
- Display a list of materials nearly out of stock, with storage location, plant, and current stock quantity
- Classify materials based on two configurable rules: (1) stock quantity below reorder point, (2) stock percentage below a user-defined percentage of safety stock
- Allow threshold configuration (safety stock percentage) from the UI
- Read stock data live from SAP S/4HANA Cloud Public Edition via the Material Stock Read OData API

### Non-Goals (Out of Scope)

- Triggering purchase requisitions or replenishment orders from the dashboard
- Push notifications or email alerts for at-risk materials
- Historical trend analysis or time-series stock charts
- Integration with SAP IBP or SAP Analytics Cloud
- Support for batch-managed or serial-number-managed stock classifications

---

## Requirements

### Must-Have Requirements

**R1: Sufficient Stock List**

- **Problem to Solve**: Users have no consolidated view of materials that currently have healthy stock and do not need attention.
- **User Story**: As an inventory manager, I need a list of all materials with stock above both the reorder point and the safety stock threshold so that I can confirm which materials require no action.
- **Acceptance Criteria**:
  - Given stock data is loaded from S/4HANA, when the dashboard opens, then all materials with unrestricted stock quantity above the reorder point AND above the configured safety stock percentage are displayed in the "Sufficient Stock" panel.
  - The list shows at minimum: Material Number, Material Description, Plant, Storage Location, Current Stock Quantity, Unit of Measure.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 1

**R2: Nearly Out of Stock List with Storage Location**

- **Problem to Solve**: At-risk materials are not surfaced in a single view, causing delayed replenishment responses.
- **User Story**: As a supply chain planner, I need a list of materials that are below the reorder point or below the safety stock threshold, along with their storage location, so that I can identify and act on replenishment needs immediately.
- **Acceptance Criteria**:
  - Given stock data is loaded, when the dashboard opens, then all materials meeting either at-risk condition are shown in the "Nearly Out of Stock" panel with a visual risk indicator.
  - The list shows: Material Number, Material Description, Plant, Storage Location, Current Stock Quantity, Reorder Point, Safety Stock, Risk Reason (reorder point breach / safety stock % breach), Unit of Measure.
  - Materials breaching both conditions are shown once with both risk reasons flagged.
- **Maps to Objective**: Objectives 1 and 2
- **Priority Rank**: 2

**R3: Configurable Safety Stock Percentage Threshold**

- **Problem to Solve**: The definition of "nearly out of stock" varies by plant and operational policy; a hard-coded value would make the dashboard obsolete as policies change.
- **User Story**: As an inventory manager, I need to configure the safety stock percentage threshold from the UI so that the classification reflects our current inventory policy without requiring developer involvement.
- **Acceptance Criteria**:
  - Given the dashboard is open, when a user changes the safety stock percentage threshold field and applies it, then the classification in both panels updates immediately to reflect the new threshold.
  - The threshold value is persisted and retained on next page load.
- **Maps to Objective**: Objective 3
- **Priority Rank**: 3

**R4: Live Data from SAP S/4HANA Cloud Public Edition**

- **Problem to Solve**: Stale stock data would cause incorrect classification and erode user trust.
- **User Story**: As an inventory manager, I need the dashboard to reflect the current stock position from S/4HANA so that I am not acting on outdated information.
- **Acceptance Criteria**:
  - Given an S/4HANA destination is configured on BTP, when the dashboard loads, then stock data is fetched live from the Material Stock Read API (`API_MATERIAL_STOCK_SRV`) and displayed within an acceptable load time.
  - A manual refresh button is available to trigger a new data fetch on demand.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 4

### High-Want Requirements

**R5: Filter by Plant and Storage Location**

- **Problem to Solve**: Users responsible for specific plants or storage areas need to focus their view without scrolling through unrelated entries.
- **User Story**: As a warehouse manager, I need to filter both lists by plant and storage location so that I can focus on materials within my area of responsibility.
- **Priority Rank**: 1

**R6: Export to CSV**

- **Problem to Solve**: Procurement officers and plant managers often need to share the at-risk list in email or Excel for follow-up actions.
- **User Story**: As a procurement officer, I need to export the nearly-out-of-stock list to CSV so that I can share it with my team and attach it to a purchase order follow-up.
- **Priority Rank**: 2

---

## Non-Functional Requirements

### Performance

- **Latency**: Dashboard should render both panels within 5 seconds under normal load (up to 500 material records).
- **Throughput**: Supports up to 50 concurrent users.

### Reliability

- **Availability**: Inherits BTP Cloud Foundry SLA (99.9% uptime target).
- **Fallback**: If the S/4HANA API call fails, an error banner is displayed and the last successfully loaded data is shown with a timestamp indicating data age.

### Explainability

- **Traceability**: Each material in the at-risk list shows the specific rule(s) that triggered its classification (reorder point breach and/or safety stock % breach).
- **Decision Logging**: Classification logic and threshold values applied at each data load are logged server-side for auditability.

---

## Solution Architecture

**Architecture Overview:**  
A BTP Extension hosted on SAP BTP Cloud Foundry, consisting of a CAP Node.js backend service and a React frontend (SAP UI5 Web Components). The backend connects to SAP S/4HANA Cloud Public Edition via an SAP BTP destination using the Material Stock Read OData API. Classification logic runs in the CAP service layer.

**Key Components:**

- **React Frontend (SAP UI5 Web Components)**: Two-panel dashboard UI — sufficient stock list and at-risk materials list with location. Includes threshold configuration control and refresh button.
- **CAP Node.js Backend**: Fetches material stock data from S/4HANA, applies classification logic (reorder point and safety stock percentage threshold), and exposes a custom OData/REST service to the frontend.
- **SAP BTP Destination**: Configured destination pointing to the S/4HANA Cloud Public Edition tenant, handling OAuth 2.0 authentication for the Material Stock Read API.

**Integration Points:**

- **SAP S/4HANA Cloud Public Edition – Material Stock Read API** (`API_MATERIAL_STOCK_SRV`): Read-only OData call to retrieve unrestricted stock, storage location, reorder point, and safety stock per material. Called on dashboard load and on manual refresh.

**Deployment Environments:**

- **Dev**: Developer sandbox on BTP with a mock or test S/4HANA system destination.
- **Prod**: BTP Cloud Foundry space connected to the production S/4HANA Cloud Public Edition tenant.

### Automation & Agent Behaviour

**Automation Level:** Rule-based

**Actions the system performs without human approval:**

- Classifying materials as sufficient or at-risk based on configured thresholds
- Fetching live stock data from S/4HANA on page load and on manual refresh

**Actions that require human review or approval:**

- Changing the safety stock percentage threshold (user action required)

**Knowledge & data sources accessed:**

- SAP S/4HANA Cloud Public Edition – Material Stock Read API (`API_MATERIAL_STOCK_SRV`): unrestricted stock quantity, storage location, reorder point, safety stock per material/plant/storage location.

**Guardrails & fail-safes:**

- The dashboard is read-only — no write operations are performed against S/4HANA.
- If the API returns an error or partial data, the system displays a banner and does not silently show incomplete results.
- Threshold configuration is stored server-side (CAP persistence layer); frontend cannot bypass the CAP service to write directly to S/4HANA.

---

## Milestones

### M1: Data Successfully Retrieved from S/4HANA

- **Description**: The CAP backend successfully calls the Material Stock Read API and receives a valid response.
- **Achieved when**: A non-empty material stock dataset is returned from the S/4HANA OData API with HTTP 200.
- **Log on achievement**: `M1.achieved: material stock data retrieved successfully — {count} records loaded from S/4HANA`
- **Log on miss**: `M1.missed: material stock data retrieval failed — API call returned error or empty dataset`

### M2: Stock Classification Applied

- **Description**: All retrieved materials have been classified as "Sufficient" or "Nearly Out of Stock" based on the configured thresholds.
- **Achieved when**: Every material record has a classification label and risk reason (if at-risk) attached before the response is sent to the frontend.
- **Log on achievement**: `M2.achieved: stock classification complete — {sufficient_count} sufficient, {atrisk_count} nearly out of stock`
- **Log on miss**: `M2.missed: stock classification did not complete — classification logic returned an error`

### M3: Dashboard Rendered for User

- **Description**: Both panels — sufficient stock and nearly out of stock — are visible and populated in the browser.
- **Achieved when**: The React frontend receives the classified data response and renders both list panels without error.
- **Log on achievement**: `M3.achieved: dashboard rendered successfully — both panels visible with data`
- **Log on miss**: `M3.missed: dashboard rendering failed — frontend did not receive or could not display classified data`

---

## Risks, Assumptions, and Dependencies

### Risks

- **API connectivity**: If the BTP destination to S/4HANA Cloud Public Edition is misconfigured or credentials expire, the dashboard cannot load data. Mitigation: validate destination configuration during deployment.
- **Missing master data**: If reorder point or safety stock values are not maintained in the S/4HANA material master for some materials, those materials will be misclassified as "sufficient" by default. Mitigation: document this assumption and flag unmaintained records in the UI.

### Assumptions (Validate These)

- Reorder point and safety stock fields are populated in the S/4HANA material master for the relevant materials and plants.
- The Material Stock Read API (`API_MATERIAL_STOCK_SRV`) is accessible and authorised for the BTP technical user.
- All four target user roles have access to the BTP-hosted URL.

### Dependencies

- SAP BTP Cloud Foundry subaccount with destination service configured
- SAP S/4HANA Cloud Public Edition tenant with the Material Stock Read API enabled and authorised
- SAP UI5 Web Components and CAP Node.js runtime available on BTP

---

## References

- [SAP Material Stock Read API – Business Accelerator Hub](https://api.sap.com/api/API_MATERIAL_STOCK_SRV/overview)
- [SAP BTP Destination Service Documentation](https://help.sap.com/docs/connectivity/sap-btp-connectivity-cf/destinations)
- [SAP CAP Node.js Documentation](https://cap.cloud.sap/docs/)
- [SAP UI5 Web Components](https://sap.github.io/ui5-webcomponents/)
