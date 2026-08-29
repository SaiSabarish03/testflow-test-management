# TestFlow — API Documentation

The TestFlow REST API is documented via FastAPI's built-in OpenAPI interface.

When the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Base URL

```
http://localhost:8000/api
```

---

## Authentication

All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <token>
```

Obtain a token via:

```
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@testflow.dev",
  "password": "Admin123!"
}
```

---

## HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 204 | No Content (delete) |
| 400 | Bad Request |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient role) |
| 404 | Not Found |
| 409 | Conflict (duplicate key, etc.) |
| 422 | Validation Error |
| 500 | Internal Server Error |

---

## Endpoints Summary

Full request/response schemas are available in the Swagger UI.

### Auth
- `POST /api/auth/login`
- `GET /api/auth/me`

### Users
- `GET /api/users`
- `POST /api/users`
- `GET /api/users/{id}`
- `PUT /api/users/{id}`
- `DELETE /api/users/{id}`

### Projects
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{id}`
- `PUT /api/projects/{id}`
- `DELETE /api/projects/{id}`

### Test Suites
- `GET /api/projects/{id}/suites`
- `POST /api/projects/{id}/suites`
- `GET /api/suites/{id}`
- `PUT /api/suites/{id}`
- `DELETE /api/suites/{id}`

### Test Cases
- `GET /api/suites/{id}/test-cases`
- `POST /api/suites/{id}/test-cases`
- `GET /api/test-cases/{id}`
- `PUT /api/test-cases/{id}`
- `DELETE /api/test-cases/{id}`

### Test Runs
- `GET /api/projects/{id}/runs`
- `POST /api/projects/{id}/runs`
- `GET /api/runs/{id}`
- `PUT /api/runs/{id}`

### Test Results
- `GET /api/runs/{id}/results`
- `POST /api/runs/{id}/results`

### Defects
- `GET /api/defects`
- `POST /api/defects`
- `GET /api/defects/{id}`
- `PUT /api/defects/{id}`
- `DELETE /api/defects/{id}`
