# Frontend Guide

Stack: Next.js (TypeScript), Tailwind CSS, shadcn/ui.

Source: `frontend/src/`

## Page Routing Map

| Route | File | Description |
|-------|------|-------------|
| `/` | `frontend/src/app/page.tsx` | Home page — natural language query form, displays answer, generated SQL, and result table |

## How to Add a New Page

1. Create `frontend/src/app/{name}/page.tsx` with a default export React component.
2. Update the routing map in this doc.

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/app/layout.tsx` | Root layout (fonts, global wrappers) |
| `frontend/src/app/page.tsx` | Home page |
| `frontend/src/app/globals.css` | Global styles (Tailwind base) |
| `frontend/src/lib/api.ts` | API client — `queryStats()` calls `POST /api/query` |
| `frontend/src/components/ui/` | shadcn/ui component primitives |

## Home Page Behaviour

The home page (`/`) presents:
- Example question chip buttons that pre-fill the textarea when clicked.
- A textarea for entering a plain-English baseball question (Enter to submit).
- An "Ask" button that calls `queryStats()` from `frontend/src/lib/api.ts`.
- While loading: a skeleton placeholder replaces the results area.
- On success: an **Answer** card, a **Generated SQL** code block, and a **Results** table.
- On error: a red error card with the message from the API.

## Environment Variables

| Variable | Where used | Purpose |
|----------|-----------|---------|
| `NEXT_PUBLIC_API_URL` | `frontend/src/lib/api.ts` | Backend base URL (defaults to `http://localhost:8000`) |

Set in `docker-compose.yml` for container deployments or in `frontend/.env.local` for local dev.
