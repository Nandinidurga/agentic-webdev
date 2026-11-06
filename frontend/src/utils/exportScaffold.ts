/**
 * Known-good client and server scaffold definitions for full-stack project bundle export.
 * Pins all dependencies to exact versions to avoid upstream breaking changes.
 */

export const PINNED_CLIENT_DEPENDENCIES = {
  "react": "18.3.1",
  "react-dom": "18.3.1",
  "lucide-react": "0.453.0"
};

export const PINNED_CLIENT_DEV_DEPENDENCIES = {
  "@vitejs/plugin-react": "4.3.1",
  "vite": "5.4.2"
};

export const KNOWN_GOOD_CLIENT_PACKAGE_JSON = {
  name: "frontend-client",
  private: true,
  version: "1.0.0",
  type: "module",
  scripts: {
    dev: "vite",
    start: "vite",
    build: "vite build",
    preview: "vite preview"
  },
  dependencies: PINNED_CLIENT_DEPENDENCIES,
  devDependencies: PINNED_CLIENT_DEV_DEPENDENCIES
};

export const KNOWN_GOOD_SERVER_PACKAGE_JSON = {
  name: "backend-server",
  version: "1.0.0",
  main: "server.js",
  scripts: {
    start: "node server.js"
  },
  dependencies: {
    express: "4.19.2",
    cors: "2.8.5"
  }
};

export const INDEX_HTML = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚡</text></svg>" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Agentic Full-Stack Application</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
`;

export const MAIN_JSX = `import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
`;

export const VITE_CONFIG_JS = `import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  }
});
`;

export const ROOT_README = `# Full-Stack Application Bundle
Generated autonomously by Agentic Full-Stack Studio.

## 📁 Architecture
- \`/server\`: Node.js + Express REST API Backend
- \`/client\`: React 18 + Vite Production Frontend

## 🚀 Quickstart Guide

### 1. Launch the Backend Server
\`\`\`bash
cd server
npm install
npm start
\`\`\`
The Express server starts at http://localhost:5000 with CORS and REST endpoints.

### 2. Launch the Frontend Client
\`\`\`bash
cd client
npm install
npm start
\`\`\`
The Vite development server opens at http://localhost:3000 with HMR and proxies / connects to the backend on port 5000.
`;

/**
 * Builds the complete dictionary of relative file paths and contents for zip export.
 * Ignores any model-generated package.json for the client and pins all dependencies.
 */
export function buildExportBundle(rawFiles: Record<string, string>): Record<string, string> {
  const bundle: Record<string, string> = {};

  // 1. Root documentation
  bundle["README.md"] = ROOT_README;

  // 2. Known-good client scaffold (Always pinned, ignores model's client package.json)
  bundle["client/package.json"] = JSON.stringify(KNOWN_GOOD_CLIENT_PACKAGE_JSON, null, 2);
  bundle["client/index.html"] = INDEX_HTML;
  bundle["client/src/main.jsx"] = MAIN_JSX;
  bundle["client/vite.config.js"] = VITE_CONFIG_JS;

  // 3. Known-good server defaults
  let hasServerJs = false;
  let hasServerPkg = false;
  let hasClientApp = false;
  let hasClientStyles = false;
  let hasClientApi = false;

  for (const [path, fileVal] of Object.entries(rawFiles || {})) {
    const cleanPath = path.startsWith("/") ? path.slice(1) : path;
    const lower = cleanPath.toLowerCase();

    // Ignore client package.json from model
    if (lower === "package.json" || lower === "client/package.json") {
      continue;
    }

    if (lower.startsWith("server/") || lower === "server.js") {
      const subPath = cleanPath.replace(/^server\//i, "");
      bundle[`server/${subPath}`] = fileVal;
      if (subPath === "server.js" || lower === "server.js") hasServerJs = true;
      if (subPath === "package.json") hasServerPkg = true;
    } else if (lower.includes("services/api.js") || lower.endsWith("api.js")) {
      bundle["client/src/services/api.js"] = fileVal;
      hasClientApi = true;
    } else if (lower.endsWith("styles.css") || lower.endsWith("index.css") || lower.endsWith("globals.css")) {
      bundle["client/src/styles.css"] = fileVal;
      hasClientStyles = true;
    } else if (lower.endsWith("app.js") || lower.endsWith("app.jsx") || lower.endsWith("app.tsx")) {
      bundle["client/src/App.jsx"] = fileVal;
      hasClientApp = true;
    } else if (lower === "readme.md") {
      // Handled by ROOT_README
    } else {
      // Other frontend auxiliary files
      const targetPath = cleanPath.startsWith("client/") ? cleanPath : `client/src/${cleanPath}`;
      bundle[targetPath] = fileVal;
    }
  }

  // Ensure client services/api.js exists
  if (!hasClientApi) {
    bundle["client/src/services/api.js"] = `export const api = {
  get: async (url: string) => fetch(url).then(r => r.json())
};
export default api;
`;
  }

  // Ensure server.js exists
  if (!hasServerJs) {
    bundle["server/server.js"] = `const express = require('express');
const cors = require('cors');
const app = express();
app.use(cors());
app.use(express.json());
app.get('/api/health', (req, res) => res.json({ status: 'ok', uptime: process.uptime() }));
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log('Server running on port ' + PORT));
`;
  }

  // Ensure server package.json exists with pinned versions
  if (!hasServerPkg) {
    bundle["server/package.json"] = JSON.stringify(KNOWN_GOOD_SERVER_PACKAGE_JSON, null, 2);
  }

  // Ensure client App.jsx exists
  if (!hasClientApp) {
    bundle["client/src/App.jsx"] = `import React from 'react';
import './styles.css';

export default function App() {
  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Welcome to Agentic App</h1>
      <p>Frontend successfully scaffolded with Vite and React.</p>
    </div>
  );
}
`;
  }

  // Ensure client styles.css exists
  if (!hasClientStyles) {
    bundle["client/src/styles.css"] = `body {
  margin: 0;
  font-family: system-ui, -apple-system, sans-serif;
  background-color: #0f172a;
  color: #f8fafc;
}
`;
  }

  return bundle;
}
