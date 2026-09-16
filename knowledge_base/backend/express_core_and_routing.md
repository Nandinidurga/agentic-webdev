# Express.js Core Architecture & Routing Guide

Express is the standard minimal and flexible Node.js web application framework providing a robust set of features for web and mobile applications.

## 1. Server Initialization & Structure

A production-ready Express server follows a clean, predictable structure:

```javascript
const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 5000;

// Core Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Health Check Endpoint
app.get('/api/health', (req, res) => {
  res.status(200).json({
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  });
});

// Mount Routes
// ...

// Start Server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
```

## 2. RESTful Routing Patterns

Express uses HTTP method verbs matching REST conventions:

```javascript
// GET: Retrieve all resources (with optional query filters)
app.get('/api/items', (req, res) => {
  const { category, search, sortBy } = req.query;
  let results = [...itemsStore];

  if (category) {
    results = results.filter(item => item.category.toLowerCase() === category.toLowerCase());
  }
  if (search) {
    results = results.filter(item => item.title.toLowerCase().includes(search.toLowerCase()));
  }

  res.status(200).json(results);
});

// GET by ID: Retrieve single resource
app.get('/api/items/:id', (req, res) => {
  const item = itemsStore.find(i => String(i.id) === String(req.params.id));
  if (!item) {
    return res.status(404).json({ error: 'Item not found' });
  }
  res.status(200).json(item);
});

// POST: Create a new resource
app.post('/api/items', (req, res) => {
  const { title, description, category, price } = req.body;

  // Validation
  if (!title || title.trim() === '') {
    return res.status(400).json({ error: 'Title is required' });
  }

  const newItem = {
    id: Date.now().toString(),
    title: title.trim(),
    description: description || '',
    category: category || 'General',
    price: Number(price) || 0,
    createdAt: new Date().toISOString()
  };

  itemsStore.push(newItem);
  res.status(201).json(newItem);
});

// PUT / PATCH: Update an existing resource
app.put('/api/items/:id', (req, res) => {
  const index = itemsStore.findIndex(i => String(i.id) === String(req.params.id));
  if (index === -1) {
    return res.status(404).json({ error: 'Item not found' });
  }

  const updatedItem = {
    ...itemsStore[index],
    ...req.body,
    updatedAt: new Date().toISOString()
  };

  itemsStore[index] = updatedItem;
  res.status(200).json(updatedItem);
});

// DELETE: Remove a resource
app.delete('/api/items/:id', (req, res) => {
  const index = itemsStore.findIndex(i => String(i.id) === String(req.params.id));
  if (index === -1) {
    return res.status(404).json({ error: 'Item not found' });
  }

  const deletedItem = itemsStore.splice(index, 1)[0];
  res.status(200).json({ message: 'Item deleted successfully', id: deletedItem.id });
});
```
