# Express.js Authentication with JWT & Password Hashing

Stateless token-based authentication using JSON Web Tokens (JWT) and secure password hashing with `bcryptjs`.

## 1. Core Dependencies

```json
{
  "dependencies": {
    "express": "^4.19.2",
    "cors": "^2.8.5",
    "jsonwebtoken": "^9.0.2",
    "bcryptjs": "^2.4.3"
  }
}
```

## 2. Authentication Middleware (`auth.js`)

Protects private endpoints by verifying the incoming `Authorization: Bearer <token>` header:

```javascript
const jwt = require('jsonwebtoken');
const JWT_SECRET = process.env.JWT_SECRET || 'dev-super-secret-key-12345';

const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.startsWith('Bearer ') 
    ? authHeader.split(' ')[1] 
    : null;

  if (!token) {
    return res.status(401).json({
      success: false,
      error: 'Authentication Required: Access token missing'
    });
  }

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(403).json({
        success: false,
        error: 'Invalid or expired token'
      });
    }
    req.user = user;
    next();
  });
};

module.exports = { authenticateToken, JWT_SECRET };
```

## 3. Auth Routes (Signup, Login, Profile)

Complete auth controller implementations with in-memory or database user stores:

```javascript
const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { authenticateToken, JWT_SECRET } = require('./auth');

const app = express();
app.use(express.json());

// In-memory users table
const usersStore = [];

// POST /api/auth/signup - Register new user
app.post('/api/auth/signup', async (req, res) => {
  try {
    const { name, email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    // Check duplicate
    const existingUser = usersStore.find(u => u.email.toLowerCase() === email.toLowerCase());
    if (existingUser) {
      return res.status(409).json({ error: 'User with this email already exists' });
    }

    // Hash password (10 salt rounds)
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    const newUser = {
      id: Date.now().toString(),
      name: name || email.split('@')[0],
      email: email.toLowerCase(),
      password: hashedPassword,
      createdAt: new Date().toISOString()
    };

    usersStore.push(newUser);

    // Issue token
    const token = jwt.sign(
      { id: newUser.id, email: newUser.email, name: newUser.name },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    res.status(201).json({
      success: true,
      token,
      user: { id: newUser.id, name: newUser.name, email: newUser.email }
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to create user account' });
  }
});

// POST /api/auth/login - Authenticate credentials
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    const user = usersStore.find(u => u.email.toLowerCase() === email?.toLowerCase());
    if (!user) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    // Compare hash
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    const token = jwt.sign(
      { id: user.id, email: user.email, name: user.name },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    res.status(200).json({
      success: true,
      token,
      user: { id: user.id, name: user.name, email: user.email }
    });
  } catch (err) {
    res.status(500).json({ error: 'Login authentication failed' });
  }
});

// GET /api/auth/me - Protected user profile
app.get('/api/auth/me', authenticateToken, (req, res) => {
  const user = usersStore.find(u => u.id === req.user.id);
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }

  res.status(200).json({
    id: user.id,
    name: user.name,
    email: user.email,
    createdAt: user.createdAt
  });
});
```
