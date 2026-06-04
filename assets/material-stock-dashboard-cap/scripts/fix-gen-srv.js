#!/usr/bin/env node
/**
 * Post-build script: patches gen/srv/package.json to use SQLite instead of
 * HANA, and copies React dist + mock data into gen/srv so the platform image
 * contains everything needed to run.
 */
const fs   = require('fs');
const path = require('path');

const root     = path.join(__dirname, '..');
const genSrv   = path.join(root, 'gen', 'srv');

// ── 1. Patch gen/srv/package.json ──────────────────────────────────────────
const pkgPath = path.join(genSrv, 'package.json');
const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));

delete pkg.dependencies['@cap-js/hana'];
pkg.dependencies['@cap-js/sqlite'] = '^2.4';

pkg.cds = pkg.cds || {};
pkg.cds['[production]'] = {
  requires: {
    db: {
      kind: 'sqlite',
      credentials: { url: '/app/db.sqlite' }
    },
    auth: 'dummy'
  }
};

fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');
console.log('[fix-gen-srv] Patched gen/srv/package.json: SQLite for production.');

// ── 2. Copy React dist → gen/srv/app/react-ui/dist ─────────────────────────
function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

const reactSrc  = path.join(root, 'app', 'react-ui', 'dist');
const reactDest = path.join(genSrv, 'app', 'react-ui', 'dist');
if (fs.existsSync(reactSrc)) {
  copyDir(reactSrc, reactDest);
  console.log('[fix-gen-srv] Copied React dist → gen/srv/app/react-ui/dist');
} else {
  console.warn('[fix-gen-srv] WARNING: app/react-ui/dist not found — run npm run build:ui first');
}

// ── 3. Copy mock data → gen/srv/test/data ──────────────────────────────────
const mockSrc  = path.join(root, 'test', 'data', 'material-stock-mock.js');
const mockDest = path.join(genSrv, 'test', 'data', 'material-stock-mock.js');
if (fs.existsSync(mockSrc)) {
  fs.mkdirSync(path.dirname(mockDest), { recursive: true });
  fs.copyFileSync(mockSrc, mockDest);
  console.log('[fix-gen-srv] Copied mock data → gen/srv/test/data/');
}
