/**
 * test_export_scaffold.mjs - Integration test for ExportButton scaffold generation.
 * Generates export zip bundle, unzips it into a temporary directory, runs node --check
 * and npm install to verify clean installation without missing dependencies or syntax issues.
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

// Import JSZip from frontend node_modules
import JSZip from '../frontend/node_modules/jszip/dist/jszip.min.js';
// Import scaffold generator
import { buildExportBundle } from '../frontend/src/utils/exportScaffold.js';

async function run() {
  console.log('--- STARTING EXPORT SCAFFOLD INTEGRATION TEST ---');

  // Mock raw model output containing valid files and an unpinned/invalid client package.json
  const rawModelFiles = {
    '/server.js': `const express = require('express');
const cors = require('cors');
const app = express();
app.use(cors());
app.use(express.json());
app.get('/api/health', (req, res) => res.json({ status: 'ok', uptime: process.uptime() }));
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log('Server running on port ' + PORT));
`,
    '/server/package.json': JSON.stringify({
      name: 'test-server',
      version: '1.0.0',
      dependencies: {
        express: '4.19.2',
        cors: '2.8.5'
      }
    }, null, 2),
    '/package.json': JSON.stringify({
      name: 'model-invalid-package',
      dependencies: {
        'unpinned-model-pkg': 'latest',
        react: '99.9.9'
      }
    }, null, 2),
    '/App.js': `import React, { useState } from 'react';
import { CheckCircle } from 'lucide-react';
import './styles.css';

export default function App() {
  const [items, setItems] = useState([]);
  return (
    <div>
      <CheckCircle />
      <h1>Full Stack Export Test</h1>
    </div>
  );
}
`,
    '/services/api.js': `export const getHealth = async () => {
  const res = await fetch('http://localhost:5000/api/health');
  return res.json();
};
`,
    '/styles.css': `body { margin: 0; background: #000; color: #fff; }`
  };

  // 1. Build export bundle
  console.log('1. Building project export bundle...');
  const bundle = buildExportBundle(rawModelFiles);

  // 2. Pack bundle into a ZIP archive
  console.log('2. Compressing bundle with JSZip...');
  const zip = new JSZip();
  for (const [relativePath, content] of Object.entries(bundle)) {
    zip.file(relativePath, content);
  }

  const zipBuffer = await zip.generateAsync({ type: 'nodebuffer' });

  // 3. Create temp directory and save zip
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'agentic-export-test-'));
  const zipPath = path.join(tempDir, 'exported-project.zip');
  const extractDir = path.join(tempDir, 'unzipped');
  fs.mkdirSync(extractDir);

  fs.writeFileSync(zipPath, zipBuffer);
  console.log(`3. Wrote zip to: ${zipPath}`);

  // 4. Unzip the archive
  console.log('4. Unzipping project archive...');
  const unzipped = await JSZip.loadAsync(fs.readFileSync(zipPath));
  for (const [filename, fileObj] of Object.entries(unzipped.files)) {
    if (fileObj.dir) {
      fs.mkdirSync(path.join(extractDir, filename), { recursive: true });
    } else {
      const content = await fileObj.async('nodebuffer');
      const targetFilePath = path.join(extractDir, filename);
      fs.mkdirSync(path.dirname(targetFilePath), { recursive: true });
      fs.writeFileSync(targetFilePath, content);
    }
  }

  // 5. Assertions on unzipped project structure
  console.log('5. Verifying unzipped scaffold structure...');

  const clientPkgPath = path.join(extractDir, 'client', 'package.json');
  if (!fs.existsSync(clientPkgPath)) {
    throw new Error('Missing client/package.json in unzipped archive');
  }
  const clientPkg = JSON.parse(fs.readFileSync(clientPkgPath, 'utf8'));

  // Assert client package.json ignores model's package.json
  if (clientPkg.dependencies['unpinned-model-pkg'] || clientPkg.dependencies.react === '99.9.9') {
    throw new Error("Failed: Model's client package.json was not ignored!");
  }

  // Assert pinned dependencies
  if (clientPkg.dependencies.react !== '18.3.1') {
    throw new Error(`Expected pinned react 18.3.1, received: ${clientPkg.dependencies.react}`);
  }
  if (clientPkg.dependencies['react-dom'] !== '18.3.1') {
    throw new Error(`Expected pinned react-dom 18.3.1, received: ${clientPkg.dependencies['react-dom']}`);
  }
  if (clientPkg.dependencies['lucide-react'] !== '0.453.0') {
    throw new Error(`Expected pinned lucide-react 0.453.0, received: ${clientPkg.dependencies['lucide-react']}`);
  }
  if (clientPkg.devDependencies.vite !== '5.4.2') {
    throw new Error(`Expected pinned vite 5.4.2, received: ${clientPkg.devDependencies.vite}`);
  }
  if (!clientPkg.scripts.start || clientPkg.scripts.start !== 'vite') {
    throw new Error(`Expected start script 'vite', received: ${clientPkg.scripts.start}`);
  }

  // Assert index.html & main.jsx exist
  const indexPath = path.join(extractDir, 'client', 'index.html');
  const mainJsxPath = path.join(extractDir, 'client', 'src', 'main.jsx');
  const appJsxPath = path.join(extractDir, 'client', 'src', 'App.jsx');
  const serverJsPath = path.join(extractDir, 'server', 'server.js');

  if (!fs.existsSync(indexPath)) throw new Error('Missing client/index.html');
  if (!fs.existsSync(mainJsxPath)) throw new Error('Missing client/src/main.jsx');
  if (!fs.existsSync(appJsxPath)) throw new Error('Missing client/src/App.jsx');
  if (!fs.existsSync(serverJsPath)) throw new Error('Missing server/server.js');

  const indexContent = fs.readFileSync(indexPath, 'utf8');
  if (!indexContent.includes('/src/main.jsx')) {
    throw new Error('client/index.html does not point to /src/main.jsx');
  }

  // 6. Run node --check on server.js
  console.log('6. Running `node --check server/server.js`...');
  execSync(`node --check "${serverJsPath}"`, { stdio: 'inherit' });
  console.log('✓ Syntax check passed for server.js');

  // 7. Run npm install on server
  console.log('7. Running `npm install` on server...');
  execSync('npm install', { cwd: path.join(extractDir, 'server'), stdio: 'inherit' });
  console.log('✓ npm install succeeded for server');

  // Cleanup
  try {
    fs.rmSync(tempDir, { recursive: true, force: true });
    console.log('Cleaned up temp directory.');
  } catch (err) {
    // ignore cleanup error
  }

  console.log('=== ALL EXPORT SCAFFOLD INTEGRATION TESTS PASSED ===');
}

run().catch((err) => {
  console.error('Test Failed:', err);
  process.exit(1);
});
