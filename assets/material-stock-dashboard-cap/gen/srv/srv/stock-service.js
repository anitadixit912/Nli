'use strict';

const cds = require('@sap/cds');
const { mockStockData } = require('../test/data/material-stock-mock');

// Agent service URL — override via env var when deployed
const AGENT_URL = process.env.AGENT_SERVICE_URL || 'http://localhost:5000';

module.exports = class StockService extends cds.ApplicationService {

  async init() {
    const { MaterialStockView, StockThresholdConfig } = this.entities;

    // ── READ MaterialStockView ──────────────────────────────────────────────
    this.on('READ', MaterialStockView, async (req) => {
      // 1. Load threshold config (default: 20%)
      const configs = await SELECT.from(StockThresholdConfig).where({ id: 1 });
      const safetyStockPct = configs.length > 0 ? Number(configs[0].safetyStockPct) : 20;

      // 2. In production: fetch live data from S/4HANA via external service.
      //    For local development, use mock data.
      let rawStock;
      try {
        const s4 = await cds.connect.to('API_MATERIAL_STOCK_SRV');
        const { A_MatlStkInAcctModType } = s4.entities;
        rawStock = await s4.run(
          SELECT.from(A_MatlStkInAcctModType).columns(
            'Material', 'Plant', 'StorageLocation', 'MaterialBaseUnit',
            'MatlWrhsStkQtyInMatlBaseUnit'
          )
        );
        // Map external fields to our view shape
        rawStock = rawStock.map(r => ({
          Material        : r.Material,
          Plant           : r.Plant,
          StorageLocation : r.StorageLocation,
          BaseUnit        : r.MaterialBaseUnit,
          StockQuantity   : Number(r.MatlWrhsStkQtyInMatlBaseUnit || 0),
          // ReorderPoint and SafetyStock are not in this API — use 0 as fallback
          ReorderPoint    : 0,
          SafetyStock     : 0,
          MaterialDescription: '',
        }));
      } catch {
        // Fall back to mock data when no real destination is configured
        rawStock = mockStockData.map(r => ({
          Material            : r.Material,
          Plant               : r.Plant,
          StorageLocation     : r.StorageLocation,
          MaterialDescription : r.MaterialDescription,
          StockQuantity       : r.StockQuantity,
          BaseUnit            : r.BaseUnit,
          ReorderPoint        : r.ReorderPoint,
          SafetyStock         : r.SafetyStock,
        }));
      }

      // 3. Classify each material
      const classified = rawStock.map(item => classify(item, safetyStockPct));

      // 4. Apply OData $filter if present (StockStatus eq '...')
      let result = classified;
      const filter = req.query.SELECT?.where;
      if (filter) {
        result = applyFilter(classified, filter);
      }

      // 5. Log milestone
      console.log(`M1.achieved: material stock data retrieved successfully — ${rawStock.length} records loaded`);
      console.log(`M2.achieved: stock classification complete — ${result.filter(r => r.StockStatus === 'SUFFICIENT').length} sufficient, ${result.filter(r => r.StockStatus === 'NEARLY_OUT_OF_STOCK').length} nearly out of stock`);

      return result;
    });

    // ── CHAT action — proxy to Stock Advisor Agent ─────────────────────────
    this.on('chat', async (req) => {
      const { message, contextId } = req.data;
      const threadId = contextId || `thread-${Date.now()}`;

      try {
        // Try calling the Python A2A agent
        const response = await callAgent(message, threadId);
        return response;
      } catch (err) {
        // Agent not available — fall back to rule-based recommendations
        cds.log('stock-service').warn('Agent unavailable, using rule-based fallback:', err.message);
        return ruleBasedRecommendation(message, await this.getClassifiedStock(req));
      }
    });

    await super.init();
  }

  /** Helper: get classified stock data (reused by fallback) */
  async getClassifiedStock(req) {
    const { StockThresholdConfig } = this.entities;
    const configs = await SELECT.from(StockThresholdConfig).where({ id: 1 });
    const safetyStockPct = configs.length > 0 ? Number(configs[0].safetyStockPct) : 20;
    return mockStockData.map(item => classify(item, safetyStockPct));
  }
};

/**
 * Classify a stock item as SUFFICIENT or NEARLY_OUT_OF_STOCK based on:
 * 1. Stock below reorder point
 * 2. Stock below (safetyStock * safetyStockPct / 100)
 */
function classify(item, safetyStockPct) {
  const qty          = Number(item.StockQuantity)  || 0;
  const reorderPoint = Number(item.ReorderPoint)   || 0;
  const safetyStock  = Number(item.SafetyStock)    || 0;

  const belowReorderPoint  = qty < reorderPoint;
  const safetyStockThresh  = safetyStock * safetyStockPct / 100;
  const belowSafetyStockPct = safetyStock > 0 && qty < safetyStockThresh;

  let StockStatus = 'SUFFICIENT';
  let RiskReason  = null;

  if (belowReorderPoint && belowSafetyStockPct) {
    StockStatus = 'NEARLY_OUT_OF_STOCK';
    RiskReason  = 'BOTH';
  } else if (belowReorderPoint) {
    StockStatus = 'NEARLY_OUT_OF_STOCK';
    RiskReason  = 'REORDER_POINT_BREACH';
  } else if (belowSafetyStockPct) {
    StockStatus = 'NEARLY_OUT_OF_STOCK';
    RiskReason  = 'SAFETY_STOCK_PCT_BREACH';
  }

  return { ...item, StockStatus, RiskReason };
}

/**
 * Send a message to the Stock Advisor Agent via A2A protocol.
 * Returns the agent's final text response.
 */
async function callAgent(message, contextId) {
  const taskId   = `task-${Date.now()}`;
  const payload  = {
    jsonrpc: '2.0',
    id: taskId,
    method: 'tasks/send',
    params: {
      id: taskId,
      sessionId: contextId,
      message: {
        role: 'user',
        parts: [{ type: 'text', text: message }],
      },
      acceptedOutputModes: ['text'],
    },
  };

  return new Promise((resolve, reject) => {
    const url  = new URL(`${AGENT_URL}/`);
    const body = JSON.stringify(payload);
    const opts = {
      hostname: url.hostname,
      port    : Number(url.port) || 5000,
      path    : url.pathname,
      method  : 'POST',
      headers : { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
      timeout : 30000,
    };
    const http = require('http');
    const req  = http.request(opts, (res) => {
      let raw = '';
      res.on('data', chunk => { raw += chunk; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(raw);
          // Extract text from A2A response
          const artifacts = parsed?.result?.artifacts || [];
          const text = artifacts
            .flatMap(a => a.parts || [])
            .filter(p => p.type === 'text')
            .map(p => p.text)
            .join('\n') || parsed?.result?.status?.message?.parts?.[0]?.text || 'No response from agent.';
          resolve(text);
        } catch (e) {
          reject(new Error('Failed to parse agent response: ' + e.message));
        }
      });
    });
    req.on('error',   reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Agent request timed out')); });
    req.write(body);
    req.end();
  });
}

/**
 * Rule-based fallback: answer common stock questions from classified data.
 */
function ruleBasedRecommendation(message, stockData) {
  const q        = (message || '').toLowerCase();
  const atRisk   = stockData.filter(r => r.StockStatus === 'NEARLY_OUT_OF_STOCK');
  const critical = atRisk.filter(r => r.RiskReason === 'BOTH');
  const sufficient = stockData.filter(r => r.StockStatus === 'SUFFICIENT');

  // Summary question
  if (/summ|overview|status|how many/.test(q)) {
    return (
      `**Stock Health Summary**\n\n` +
      `- Total materials tracked: ${stockData.length}\n` +
      `- ✅ Sufficient stock: ${sufficient.length}\n` +
      `- ⚠️ Nearly out of stock: ${atRisk.length}\n` +
      `  - 🔴 Critical (both thresholds breached): ${critical.length}\n` +
      `  - 🟠 Below reorder point: ${atRisk.filter(r => r.RiskReason === 'REORDER_POINT_BREACH').length}\n` +
      `  - 🟡 Below safety stock %: ${atRisk.filter(r => r.RiskReason === 'SAFETY_STOCK_PCT_BREACH').length}`
    );
  }

  // Critical / urgent / most important
  if (/critical|urgent|most|priorit|worst/.test(q)) {
    if (!critical.length && !atRisk.length) return 'No critical stock issues found at this time.';
    const top = (critical.length ? critical : atRisk).slice(0, 5);
    const lines = top.map(m =>
      `- **${m.Material}** (${m.MaterialDescription}) — Plant ${m.Plant} / ${m.StorageLocation} | ` +
      `Stock: ${m.StockQuantity} ${m.BaseUnit} | Reorder Point: ${m.ReorderPoint}`
    );
    return `**Most Critical Materials to Reorder**\n\n${lines.join('\n')}`;
  }

  // Reorder / what to order
  if (/reorder|order|buy|replenish|purchas/.test(q)) {
    if (!atRisk.length) return 'No materials require reordering at this time.';
    const lines = atRisk.map(m =>
      `- **${m.Material}** (${m.MaterialDescription}) — Plant ${m.Plant} / ${m.StorageLocation} | ` +
      `Current: ${m.StockQuantity} ${m.BaseUnit} | Reorder at: ${m.ReorderPoint}`
    );
    return (
      `**Materials Recommended for Reordering (${atRisk.length})**\n\n${lines.join('\n')}\n\n` +
      `💡 Prioritize the ${critical.length} critical item(s) marked with both threshold breaches.`
    );
  }

  // Plant-specific question
  const plantMatch = q.match(/plant\s+(\w+)/i);
  if (plantMatch) {
    const plant = plantMatch[1].toUpperCase();
    const plantRisk = atRisk.filter(r => r.Plant === plant);
    if (!plantRisk.length) return `No at-risk materials found for plant ${plant}.`;
    const lines = plantRisk.map(m =>
      `- **${m.Material}** (${m.MaterialDescription}) — ${m.StorageLocation} | Stock: ${m.StockQuantity} ${m.BaseUnit}`
    );
    return `**At-Risk Materials in Plant ${plant} (${plantRisk.length})**\n\n${lines.join('\n')}`;
  }

  // Default: full recommendations
  if (!atRisk.length) {
    return '✅ All materials currently have sufficient stock. No immediate action required.';
  }
  const topLines = atRisk.slice(0, 8).map(m =>
    `- **${m.Material}** (${m.MaterialDescription}) — Plant ${m.Plant}, ${m.StorageLocation}`
  );
  return (
    `**Stock Recommendations**\n\n` +
    `There are currently **${atRisk.length} material(s)** requiring attention:\n\n` +
    topLines.join('\n') +
    (atRisk.length > 8 ? `\n…and ${atRisk.length - 8} more.` : '') +
    `\n\n💡 **Tip:** Ask me "What are the most critical items?" or "What should I reorder today?"`
  );
}

/**
 * Simple filter application for OData $filter on StockStatus.
 * Handles the common case: StockStatus eq 'VALUE'
 */
function applyFilter(data, where) {
  // where is a CQN array like ['StockStatus', '=', 'SUFFICIENT']
  if (!Array.isArray(where)) return data;
  try {
    const [left, op, right] = where;
    if (left?.ref?.[0] === 'StockStatus' && (op === '=' || op === 'eq')) {
      return data.filter(r => r.StockStatus === right?.val);
    }
  } catch {
    // ignore filter errors, return all
  }
  return data;
}
