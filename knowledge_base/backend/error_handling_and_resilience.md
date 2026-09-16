# Express.js Error Handling, Health Checks & Resilience

Robust error handling and monitoring ensure server stability and prevent crashes from unexpected exceptions.

## 1. Global Error Handling Middleware

In Express, error-handling middleware functions are defined with **four arguments**: `(err, req, res, next)`:

```javascript
// Global error handling middleware (must be registered AFTER all routes)
app.use((err, req, res, next) => {
  console.error(`[SERVER ERROR] ${err.stack || err.message}`);

  const statusCode = err.status || err.statusCode || 500;
  res.status(statusCode).json({
    success: false,
    error: {
      message: err.message || 'Internal Server Error',
      statusCode: statusCode
    }
  });
});
```

## 2. 404 Route Fallback

Any request that doesn't match an existing endpoint should return a clean 404 JSON response rather than default HTML:

```javascript
// 404 Catch-all handler (placed right before global error handler)
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: {
      message: `Cannot ${req.method} ${req.originalUrl} - Route not found.`,
      statusCode: 404
    }
  });
});
```

## 3. Asynchronous Error Wrapper Pattern

In Express 4, unhandled promise rejections in async routes will not automatically pass to error middleware unless caught:

```javascript
// Async wrapper utility to avoid repetitive try/catch blocks
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

// Usage:
app.get('/api/async-data', asyncHandler(async (req, res) => {
  const data = await fetchExternalData();
  res.json(data);
}));
```

## 4. Production Health Check Endpoint

Health checks allow container orchestrators (Docker, Kubernetes) and uptime monitors to check server vitality:

```javascript
app.get('/api/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    uptime: Math.floor(process.uptime()),
    timestamp: new Date().toISOString(),
    memoryUsage: process.memoryUsage().rss
  });
});
```
