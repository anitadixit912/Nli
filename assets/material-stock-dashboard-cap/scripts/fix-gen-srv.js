#!/usr/bin/env node
/**
 * Post-build script: patches gen/srv/package.json to use SQLite instead of
 * HANA, so no hdi-deployer init job is needed on this platform.
 */
const fs = require('fs');
const path = require('path');

const pkgPath = path.join(__dirname, '..', 'gen', 'srv', 'package.json');
const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));

// Swap @cap-js/hana → @cap-js/sqlite in runtime dependencies
delete pkg.dependencies['@cap-js/hana'];
pkg.dependencies['@cap-js/sqlite'] = '^2.4';

// Inject production SQLite config
pkg.cds = pkg.cds || {};
pkg.cds['[production]'] = {
  requires: {
    db: {
      kind: 'sqlite',
      credentials: { url: '/app/db.sqlite' }
    }
  }
};

fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');
console.log('[fix-gen-srv] Patched gen/srv/package.json: using SQLite for production.');
