# Specification: material-stock-dashboard-cap

> **Guidelines**: Read [guidelines.md](../guidelines.md) and [guidelines-cap.md](../guidelines-cap.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [x] Read the project input (`product-requirements-document.md`, `intent.md`)
- [x] Invoke the `cap-development` skill from `assets/material-stock-dashboard-cap/` to set up the CAP project structure
- [x] Install dependencies (`npm install`), validate the project starts (`cds watch`) and responds

## API Spec Reference

The Material Stock Read OData API spec (EDMX) is located at:
`specification/material-stock-dashboard-cap/api-specs/material-stock.edmx`

Key entity used for stock data: `A_MatlStkInAcctModType`
- `Material` (String) — material number
- `Plant` (String) — plant
- `StorageLocation` (String) — storage location
- `MatlWrhsStkQtyInMatlBaseUnit` (Decimal) — unrestricted stock quantity
- `MaterialBaseUnit` (String) — base unit of measure

**Note**: The Material Stock API does not expose reorder point or safety stock. These values must be mocked in the CAP backend using an in-memory configuration store until a Material Master API integration is available.

## Data Model

- [ ] Define CDS entity `MaterialStockView` in `srv/stock-service.cds`:
  - `Material` : String (key)
  - `Plant` : String (key)
  - `StorageLocation` : String (key)
  - `MaterialDescription` : String
  - `StockQuantity` : Decimal
  - `BaseUnit` : String
  - `ReorderPoint` : Decimal
  - `SafetyStock` : Decimal
  - `StockStatus` : String (enum: `SUFFICIENT`, `NEARLY_OUT_OF_STOCK`)
  - `RiskReason` : String (e.g. `REORDER_POINT_BREACH`, `SAFETY_STOCK_PCT_BREACH`, `BOTH`, or null)

- [ ] Define CDS entity `StockThresholdConfig`:
  - `id` : Integer (key, value = 1 — singleton config)
  - `safetyStockPct` : Decimal (default 20 — meaning stock must be >= 20% of safety stock)

- [ ] Expose both entities via a CDS service `StockService` at path `/stock`

## Backend: S/4HANA Integration via Destination

- [ ] Define an external service in `package.json` under `cds.requires` pointing to the S/4HANA Material Stock OData API:
  ```json
  "API_MATERIAL_STOCK_SRV": {
    "kind": "odata-v2",
    "model": "srv/external/API_MATERIAL_STOCK_SRV",
    "credentials": { "destination": "S4HANA_MATERIAL_STOCK" }
  }
  ```
- [ ] Import the EDMX spec into the CAP project: copy `specification/material-stock-dashboard-cap/api-specs/material-stock.edmx` to `assets/material-stock-dashboard-cap/srv/external/API_MATERIAL_STOCK_SRV.edmx`
- [ ] Run `cds import srv/external/API_MATERIAL_STOCK_SRV.edmx` to generate the CDS model for the external service
- [ ] Create a mock CSV fixture for local development (since no real S/4HANA system is available at this stage):
  - `assets/material-stock-dashboard-cap/test/data/API_MATERIAL_STOCK_SRV-A_MatlStkInAcctModType.csv` with at least 10 realistic rows covering both sufficient and nearly-out-of-stock cases
  - Include materials with: high stock (well above reorder point), low stock (below reorder point), stock below 20% of safety stock, and both conditions

## Backend: Classification Logic (Custom Handler)

- [ ] Implement a custom `READ` handler for `MaterialStockView` in `srv/stock-service.js`:
  1. Fetch all `A_MatlStkInAcctModType` records from the external service (or mock data)
  2. Fetch the current `StockThresholdConfig` (safetyStockPct) — default to 20 if not configured
  3. For each stock record, apply classification:
     - **REORDER_POINT_BREACH**: `StockQuantity < ReorderPoint`
     - **SAFETY_STOCK_PCT_BREACH**: `StockQuantity < (SafetyStock * safetyStockPct / 100)`
     - If both conditions are true → `RiskReason = 'BOTH'`
     - If any condition is true → `StockStatus = 'NEARLY_OUT_OF_STOCK'`
     - Otherwise → `StockStatus = 'SUFFICIENT'`
  4. Return the enriched `MaterialStockView` records

- [ ] Implement `CREATE`/`UPDATE` handler for `StockThresholdConfig` to persist threshold changes in-memory (or SQLite for local dev)

- [ ] Ensure `ReorderPoint` and `SafetyStock` are seeded from mock data; document that these will come from a Material Master API in a future iteration

## Backend: Tests

- [ ] Write unit tests for the classification logic:
  - Test: material with stock above reorder point AND above safety stock threshold → `SUFFICIENT`
  - Test: material with stock below reorder point → `NEARLY_OUT_OF_STOCK` with `REORDER_POINT_BREACH`
  - Test: material with stock < safetyStockPct% of safety stock → `NEARLY_OUT_OF_STOCK` with `SAFETY_STOCK_PCT_BREACH`
  - Test: material breaching both conditions → `NEARLY_OUT_OF_STOCK` with `BOTH`
  - Test: threshold config change is applied in subsequent classification calls

- [ ] Run `cds compile srv/` to confirm models compile without errors
- [ ] Run `cds watch` and verify `/odata/v4/stock/MaterialStockView` returns classified results

## Frontend: Dashboard UI

The frontend is a React app using SAP UI5 Web Components. It is a **dashboard** with two main panels side-by-side (or stacked on smaller screens).

- [ ] Scaffold the React frontend in `assets/material-stock-dashboard-cap/ui/` following the `cap-development` skill frontend guidelines
- [ ] Install SAP UI5 Web Components for React: `@ui5/webcomponents-react`

### Dashboard Layout

- [ ] Create a main `Dashboard` page as the root route (`/`)
- [ ] Implement a top header bar (`ui5-shellbar`) showing the app title "Material Stock Dashboard" and a **Refresh** button
- [ ] Implement a threshold configuration bar below the header:
  - Label: "Safety Stock Threshold (%)"
  - `ui5-input` (type number) pre-filled with the current `safetyStockPct` value
  - "Apply" button — on click, PATCHes/POSTs the new value to `StockThresholdConfig` and re-fetches the stock data
- [ ] Layout two panels horizontally using a CSS grid or flexbox:
  - **Left panel**: Sufficient Stock
  - **Right panel**: Nearly Out of Stock
- [ ] Each panel has a `ui5-title` heading and a `ui5-table` (or `AnalyticalTable` from `@ui5/webcomponents-react`)

### Sufficient Stock Panel

- [ ] Display a `ui5-table` with columns: Material, Description, Plant, Storage Location, Stock Quantity, Unit
- [ ] Populate from `MaterialStockView` filtered by `StockStatus eq 'SUFFICIENT'`
- [ ] Show record count in the panel header (e.g. "Sufficient Stock (42)")
- [ ] Style the panel with a subtle green border or header accent

### Nearly Out of Stock Panel

- [ ] Display a `ui5-table` with columns: Material, Description, Plant, Storage Location, Stock Quantity, Unit, Risk Reason
- [ ] Populate from `MaterialStockView` filtered by `StockStatus eq 'NEARLY_OUT_OF_STOCK'`
- [ ] Show record count in the panel header (e.g. "Nearly Out of Stock (8)")
- [ ] Highlight each row based on risk:
  - `BOTH` → red background / urgent indicator
  - `REORDER_POINT_BREACH` or `SAFETY_STOCK_PCT_BREACH` → amber/orange indicator
- [ ] Style the panel with a red/amber border or header accent
- [ ] Display a human-readable Risk Reason label (not the raw enum value):
  - `REORDER_POINT_BREACH` → "Below Reorder Point"
  - `SAFETY_STOCK_PCT_BREACH` → "Below Safety Stock %"
  - `BOTH` → "Below Reorder Point & Safety Stock %"

### Filtering

- [ ] Add a `ui5-select` filter for **Plant** above each panel (shared or per-panel), populated dynamically from distinct plant values in the response
- [ ] Add a `ui5-select` filter for **Storage Location**, cascading from the selected Plant
- [ ] Filters apply client-side to the already-loaded data (no additional API call required)

### Loading & Error States

- [ ] Show a `ui5-busy-indicator` over both panels while data is loading
- [ ] On API error, show a `ui5-message-strip` (type="Error") with the error message and a retry option
- [ ] If no data is returned, show an empty state message in each panel ("No materials found")

### Export to CSV

- [ ] Add an "Export CSV" button in the Nearly Out of Stock panel toolbar
- [ ] On click, generate and download a CSV file containing all at-risk materials (client-side, no backend call)
- [ ] CSV columns: Material, Description, Plant, Storage Location, Stock Quantity, Unit, Risk Reason

## Frontend: Connect to CAP Backend

- [ ] Configure the React app to proxy API calls to `http://localhost:4004` during local development
- [ ] Fetch `MaterialStockView` from `/odata/v4/stock/MaterialStockView` using the OData query parameters for filtering by `StockStatus`
- [ ] Fetch current `StockThresholdConfig` from `/odata/v4/stock/StockThresholdConfig(1)` on app load
- [ ] Refresh data on demand when the Refresh button is clicked

## Validation

- [ ] Run `cds compile srv/` — no errors
- [ ] Run `cds watch` — service starts and `/odata/v4/stock/MaterialStockView` returns data
- [ ] Start the React frontend — both panels render with mock data
- [ ] Verify: changing the threshold percentage and clicking Apply updates classification in real time
- [ ] Verify: Plant and Storage Location filters correctly narrow both panels
- [ ] Verify: Export CSV produces a valid file with at-risk materials
- [ ] Verify: row colour coding distinguishes BOTH, REORDER_POINT_BREACH, and SAFETY_STOCK_PCT_BREACH
