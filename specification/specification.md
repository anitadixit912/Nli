# Specification

> **Guidelines**: Read [guidelines.md](./guidelines.md) before executing ANY tasks below.

Check off items as completed.

## Solution Setup

- [x] Create asset directory: `mkdir -p assets/material-stock-dashboard-cap/`
- [x] Invoke `setup-solution` skill to create `solution.yaml` and `asset.yaml` files for the asset
- [x] Validate `asset.yaml` and `solution.yaml` files exist and are well-formed

## Asset Implementation

- [x] Execute specification/material-stock-dashboard-cap/specification.md (all items)
- [x] Execute specification/stock-advisor-agent/specification.md (all items — chatbox + agent)
- [x] Cross-implementation compatibility check: CAP `/stock/chat` action calls agent via HTTP; agent tools call back to CAP `/stock/MaterialStockView`; React UI calls CAP only
