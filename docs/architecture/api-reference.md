# API Reference

Base URL: `http://localhost:8000`
Auth: None (public API)

Interactive docs (Swagger UI) available at `http://localhost:8000/docs` when the backend is running.

---

## Health

### GET /health

Returns the service health status.

- **Response** (200):
  ```json
  { "status": "ok" }
  ```

---

## Query

### POST /api/query

Accepts a natural language baseball question, converts it to SQL via an LLM, executes it, and returns the result with a human-friendly answer.

> **Note:** The LLM integration is currently a stub. This endpoint returns HTTP 501 until `generate_sql` in `backend/app/text_to_sql.py` is wired to a real LLM provider.

- **Request body** (`QueryRequest`):
  ```json
  {
    "question": "string"
  }
  ```

  | Field | Type | Required | Description |
  |-------|------|----------|-------------|
  | `question` | string | Yes | Natural language question about MLB stats |

- **Response** (200) (`QueryResponse`):
  ```json
  {
    "question": "string",
    "sql": "string",
    "result": [{ "column": "value" }],
    "answer": "string"
  }
  ```

  | Field | Type | Description |
  |-------|------|-------------|
  | `question` | string | The original question echoed back |
  | `sql` | string | The generated SQL SELECT query |
  | `result` | array of objects | Raw rows from the database |
  | `answer` | string | Human-friendly summary of results |

- **Error responses:**

  | Status | Condition |
  |--------|-----------|
  | 400 | SQL execution error (generated SQL was invalid) |
  | 501 | LLM integration not configured |
