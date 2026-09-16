# Backend Data Store, In-Memory Persistence & Models

Data persistence layer designs for full-stack prototypes and production microservices.

## 1. In-Memory Data Store with Seed Data

For prototypes, sandbox environments, and rapid testing, an in-memory data store with realistic seed data allows instant full CRUD operation without external database prerequisites.

```javascript
// In-memory collection with rich domain seed items
let tasksStore = [
  {
    id: "1",
    title: "Configure CI/CD Pipeline",
    description: "Automate build and deployment checks on pull requests.",
    category: "DevOps",
    priority: "High",
    status: "in-progress",
    dueDate: "2026-09-20",
    createdAt: new Date().toISOString()
  },
  {
    id: "2",
    title: "Implement API Rate Limiting",
    description: "Protect endpoints against denial of service with express-rate-limit.",
    category: "Security",
    priority: "Medium",
    status: "pending",
    dueDate: "2026-09-25",
    createdAt: new Date().toISOString()
  },
  {
    id: "3",
    title: "Refactor State Management",
    description: "Migrate client state to lightweight custom hooks.",
    category: "Frontend",
    priority: "Low",
    status: "completed",
    dueDate: "2026-09-15",
    createdAt: new Date().toISOString()
  }
];

// Helper for atomic unique ID generation
const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
};
```

## 2. CRUD Utility Functions

Encapsulating operations keeps route handlers clean and modular:

```javascript
const TaskModel = {
  findAll: (query = {}) => {
    let result = [...tasksStore];
    if (query.category) result = result.filter(t => t.category === query.category);
    if (query.status) result = result.filter(t => t.status === query.status);
    return result;
  },

  findById: (id) => {
    return tasksStore.find(t => String(t.id) === String(id)) || null;
  },

  create: (data) => {
    const newTask = {
      id: generateId(),
      ...data,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    tasksStore.push(newTask);
    return newTask;
  },

  update: (id, updates) => {
    const index = tasksStore.findIndex(t => String(t.id) === String(id));
    if (index === -1) return null;
    
    tasksStore[index] = {
      ...tasksStore[index],
      ...updates,
      updatedAt: new Date().toISOString()
    };
    return tasksStore[index];
  },

  delete: (id) => {
    const index = tasksStore.findIndex(t => String(t.id) === String(id));
    if (index === -1) return false;
    tasksStore.splice(index, 1);
    return true;
  }
};
```

## 3. SQLite Persistence Pattern

When persistent disk storage is preferred, SQLite provides zero-configuration ACID compliance:

```javascript
// Example using better-sqlite3 or sqlite3
const Database = require('better-sqlite3');
const db = new Database('./data.db');

// Initialize schema
db.exec(`
  CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT,
    priority TEXT,
    status TEXT DEFAULT 'pending',
    createdAt TEXT
  )
`);
```
