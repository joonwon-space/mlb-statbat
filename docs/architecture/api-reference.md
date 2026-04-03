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

Accepts a natural language baseball question, converts it to SQL via Anthropic Claude (claude-haiku-4-5), executes it against PostgreSQL, and returns the result with a human-friendly natural language answer.

Rate-limited to **10 requests per minute per IP address** (slowapi). Exceeding the limit returns HTTP 429.

- **Request body** (`QueryRequest`):
  ```json
  {
    "question": "string"
  }
  ```

  | Field | Type | Required | Constraints | Description |
  |-------|------|----------|-------------|-------------|
  | `question` | string | Yes | 3–500 characters | Natural language question about MLB stats |

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
  | 400 | SQL guard rejected the generated query (non-SELECT, multi-statement, SELECT INTO, or blocked function: `pg_sleep`, `dblink`, `lo_import`, `lo_export`, `pg_read_file`, `pg_write_file`, `pg_terminate_backend`, `pg_cancel_backend`) |
  | 422 | Request validation failed (`question` missing, too short (<3), or too long (>500)) |
  | 429 | Rate limit exceeded (10 req/min per IP) |
  | 500 | SQL execution failed — internal error, generic message returned to caller |
  | 501 | LLM integration not configured (`ANTHROPIC_API_KEY` absent) |
