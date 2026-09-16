# Express.js Middleware & CORS Configuration Guide

Middleware functions are functions that have access to the request object (`req`), the response object (`res`), and the next middleware function in the application’s request-response cycle (`next`).

## 1. CORS (Cross-Origin Resource Sharing)

In full-stack web applications where the frontend (e.g., running on port 3000 or in a web sandbox) communicates with a backend API (port 5000), CORS must be properly configured.

```javascript
const cors = require('cors');

// Standard development CORS (accepts requests from any origin)
app.use(cors());

// Or detailed configuration for production:
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:5173', '*'],
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));
```

## 2. Body Parsing Middleware

Express requires middleware to parse incoming request payloads into `req.body`:

```javascript
// Parse JSON payloads (Content-Type: application/json)
app.use(express.json());

// Parse URL-encoded bodies (Content-Type: application/x-www-form-urlencoded)
app.use(express.urlencoded({ extended: true }));
```

## 3. Custom Request Logging & Timing Middleware

Useful for debugging API requests and monitoring response latency:

```javascript
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.originalUrl} - ${res.statusCode} (${duration}ms)`);
  });
  next();
});
```

## 4. Input Validation Middleware

Reusable validation middleware prevents malformed data from reaching controllers:

```javascript
function validateRequestBody(requiredFields) {
  return (req, res, next) => {
    const missing = requiredFields.filter(field => req.body[field] === undefined || req.body[field] === '');
    if (missing.length > 0) {
      return res.status(400).json({
        error: 'Validation Failed',
        message: `Missing required fields: ${missing.join(', ')}`
      });
    }
    next();
  };
}

// Usage:
app.post('/api/items', validateRequestBody(['title', 'category']), (req, res) => {
  // Safe to proceed with req.body.title and req.body.category
});
```
