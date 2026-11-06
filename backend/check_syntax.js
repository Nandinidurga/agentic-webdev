const fs = require('fs');
const path = require('path');

function resolveEsbuild() {
  const candidates = [
    path.resolve(__dirname, '../frontend/node_modules/esbuild'),
    path.resolve(__dirname, 'node_modules/esbuild'),
    path.resolve(process.cwd(), 'frontend/node_modules/esbuild'),
    'esbuild'
  ];
  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch (_) {}
  }
  return null;
}

const esbuild = resolveEsbuild();
const args = process.argv.slice(2);
const targetFile = args[0];
const loader = args[1] || 'jsx';

if (!targetFile || !fs.existsSync(targetFile)) {
  console.log(JSON.stringify({ valid: false, errors: [{ line: 1, column: 0, message: 'Target file not found for syntax verification.' }] }));
  process.exit(0);
}

const code = fs.readFileSync(targetFile, 'utf8');

if (esbuild) {
  try {
    esbuild.transformSync(code, {
      loader: loader,
      sourcefile: targetFile
    });
    console.log(JSON.stringify({ valid: true, errors: [] }));
  } catch (err) {
    const errors = (err.errors || []).map(e => ({
      line: e.location ? e.location.line : 1,
      column: e.location ? e.location.column : 0,
      message: e.text || err.message
    }));
    if (errors.length === 0) {
      errors.push({ line: 1, column: 0, message: err.message });
    }
    console.log(JSON.stringify({ valid: false, errors }));
  }
} else {
  // Explicit unavailable report when esbuild binary is not reachable
  console.log(JSON.stringify({ valid: false, unavailable: true, errors: [], warning: 'esbuild unavailable' }));
}
