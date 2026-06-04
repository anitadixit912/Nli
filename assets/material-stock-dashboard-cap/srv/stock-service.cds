using { material.stock as db } from '../db/schema';
using { API_MATERIAL_STOCK_SRV as external } from './external/API_MATERIAL_STOCK_SRV';

@requires: 'authenticated-user'
service StockService @(path: '/stock') {

  @readonly
  entity MaterialStockView {
    key Material            : String(40);
    key Plant               : String(4);
    key StorageLocation     : String(4);
        MaterialDescription : String(100);
        StockQuantity       : Decimal(13, 3);
        BaseUnit            : String(3);
        ReorderPoint        : Decimal(13, 3);
        SafetyStock         : Decimal(13, 3);
        StockStatus         : String(30);  // SUFFICIENT | NEARLY_OUT_OF_STOCK
        RiskReason          : String(60);  // REORDER_POINT_BREACH | SAFETY_STOCK_PCT_BREACH | BOTH | null
  }

  entity StockThresholdConfig as projection on db.StockThresholdConfig;

  /**
   * Send a natural-language question to the Stock Advisor Agent.
   * Returns the agent's text recommendation.
   */
  action chat(message: String not null, contextId: String) returns String;
}
