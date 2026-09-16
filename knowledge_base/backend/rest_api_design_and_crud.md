# REST API Design, HTTP Status Codes & CRUD Standards

A standardized REST API provides clean, predictable contracts for web frontends to consume.

## 1. HTTP Verbs & Semantics

| HTTP Verb | Path Convention | Description | Success Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/resources` | List resources with filters/sorting | `200 OK` |
| `GET` | `/api/resources/:id` | Fetch single resource by primary key | `200 OK` |
| `POST` | `/api/resources` | Create a new resource | `201 Created` |
| `PUT` | `/api/resources/:id` | Replace / full update of resource | `200 OK` |
| `PATCH` | `/api/resources/:id` | Partial update of specific fields | `200 OK` |
| `DELETE` | `/api/resources/:id` | Remove a resource | `200 OK` or `204 No Content` |

## 2. Standard HTTP Status Codes

- `200 OK`: Request succeeded, response contains requested data.
- `201 Created`: New resource was successfully created. Response includes newly assigned ID.
- `204 No Content`: Action succeeded, no response body returned (common for DELETE).
- `400 Bad Request`: Invalid payload, missing required parameters, or schema validation failed.
- `401 Unauthorized`: Authentication token missing or invalid.
- `403 Forbidden`: Authenticated user lacks permission.
- `404 Not Found`: Requested resource or URL does not exist.
- `409 Conflict`: Resource state conflict (e.g. duplicate unique key).
- `500 Internal Server Error`: Unhandled server runtime exception.

## 3. Standard Response Envelope Design

Standardizing response envelopes makes client-side handling trivial:

### Success Response:
```json
{
  "success": true,
  "data": [
    { "id": "1", "title": "Buy Groceries", "completed": false }
  ],
  "meta": {
    "total": 1,
    "page": 1
  }
}
```

### Error Response:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Field 'title' cannot be empty."
  }
}
```

## 4. Query Parameters for Filtering & Sorting

Express route handlers should cleanly unpack and handle query options:

```javascript
app.get('/api/records', (req, res) => {
  const { 
    search = '', 
    status, 
    sortBy = 'createdAt', 
    order = 'desc',
    limit = 50 
  } = req.query;

  let filtered = dataStore.filter(item => {
    const matchesSearch = search ? item.name.toLowerCase().includes(search.toLowerCase()) : true;
    const matchesStatus = status ? item.status === status : true;
    return matchesSearch && matchesStatus;
  });

  // Sort
  filtered.sort((a, b) => {
    if (order === 'asc') return a[sortBy] > b[sortBy] ? 1 : -1;
    return a[sortBy] < b[sortBy] ? 1 : -1;
  });

  res.status(200).json(filtered.slice(0, Number(limit)));
});
```
