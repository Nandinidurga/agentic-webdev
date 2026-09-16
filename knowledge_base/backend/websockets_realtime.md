# Real-Time Full-Stack Applications with Socket.io & Express

Building bidirectional, event-based real-time communication for live chat, instant notifications, live feeds, and collaborative dashboards.

## 1. Core Dependencies

```json
{
  "dependencies": {
    "express": "^4.19.2",
    "cors": "^2.8.5",
    "socket.io": "^4.7.5"
  }
}
```

## 2. Server Architecture with HTTP & Socket.io

Socket.io attaches to an underlying Node `http.Server` that wraps the Express `app`:

```javascript
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Create HTTP server wrapping Express
const server = http.createServer(app);

// Initialize Socket.io with CORS configuration
const io = new Server(server, {
  cors: {
    origin: '*', // Allow frontend client connection
    methods: ['GET', 'POST']
  }
});

// Real-Time Event Handlers
io.on('connection', (socket) => {
  console.log(`[Socket Connected] Client ID: ${socket.id}`);

  // 1. Join a specific topic or chat room
  socket.on('join_room', (roomName) => {
    socket.join(roomName);
    console.log(`Client ${socket.id} joined room: ${roomName}`);
    // Notify others in room
    socket.to(roomName).emit('user_joined', { userId: socket.id, timestamp: new Date().toISOString() });
  });

  // 2. Broadcast message within a room
  socket.on('send_message', (data) => {
    const { room, text, sender } = data;
    const messagePayload = {
      id: Date.now().toString(),
      text,
      sender: sender || 'Anonymous',
      timestamp: new Date().toISOString()
    };

    // Emit to everyone in the room (including sender)
    io.to(room).emit('new_message', messagePayload);
  });

  // 3. Global Notification Broadcast
  socket.on('send_notification', (notification) => {
    // Broadcast to all connected clients
    io.emit('broadcast_notification', {
      ...notification,
      receivedAt: new Date().toISOString()
    });
  });

  // 4. Handle Disconnect
  socket.on('disconnect', () => {
    console.log(`[Socket Disconnected] Client ID: ${socket.id}`);
  });
});

// Combined HTTP and WebSocket listen call
const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  console.log(`Full-Stack Server (HTTP + WebSockets) running on http://localhost:${PORT}`);
});
```

## 3. Frontend Client Integration Pattern (`React`)

Client-side integration using `socket.io-client`:

```javascript
import React, { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

const socket = io('http://localhost:5000', {
  autoConnect: true,
  reconnection: true
});

export default function ChatWidget() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  useEffect(() => {
    // Listen for incoming live messages
    socket.on('new_message', (msg) => {
      setMessages(prev => [...prev, msg]);
    });

    return () => {
      socket.off('new_message');
    };
  }, []);

  const sendMessage = () => {
    if (!input.trim()) return;
    socket.emit('send_message', {
      room: 'general',
      text: input,
      sender: 'User'
    });
    setInput('');
  };

  return (
    <div className="p-4 bg-gray-900 rounded-xl text-white">
      <div className="h-64 overflow-y-auto space-y-2">
        {messages.map(m => (
          <div key={m.id} className="p-2 rounded bg-gray-800 text-sm">
            <span className="font-bold text-blue-400">{m.sender}: </span>
            <span>{m.text}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-2 mt-2">
        <input 
          value={input} 
          onChange={e => setInput(e.target.value)} 
          className="flex-1 bg-gray-800 p-2 rounded text-sm" 
        />
        <button onClick={sendMessage} className="px-4 py-2 bg-blue-600 rounded text-sm font-semibold">
          Send
        </button>
      </div>
    </div>
  );
}
```
