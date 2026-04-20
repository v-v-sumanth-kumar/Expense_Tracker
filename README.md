# Expense Tracker (React + FastAPI)

Minimal full-stack expense tracker with retry-safe expense creation and basic filtering/sorting.

## Tech Stack

- **Frontend:** React (Vite)
- **Backend:** FastAPI + SQLAlchemy
- **Persistence:** SQLite

## Why SQLite

SQLite gives durable storage with low setup overhead, which is practical for this exercise and local development. It is safer than an in-memory store for refresh/restart scenarios and keeps the implementation small while still using relational constraints and typed columns.

## Key Design Decisions

- **Money handling:** Expense `amount` is stored as `Numeric(12,2)` and validated as decimal in API schemas to avoid float rounding errors.
- **Retry safety / idempotency:** `POST /expenses` supports `Idempotency-Key` request header. Reusing the same key returns the already-created expense (instead of creating duplicates).  
  There is also a best-effort fallback dedupe by request hash in a short time window for cases where a key is missing but the same request is retried.
- **Query behavior:** `GET /expenses` supports:
  - `category=<value>` for filtering
  - `sort=date_desc` for newest-first date sorting
- **Frontend correctness:** UI prevents duplicate submit clicks while in-flight, shows loading/error states, and computes total from the currently visible list.

## Project Structure

- `backend/` FastAPI app
- `frontend/` React app

## Run Locally

### 1) Backend

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000`.

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://127.0.0.1:5173` and calls backend at `http://127.0.0.1:8000` by default.

Optional: set `VITE_API_BASE_URL` if backend is hosted elsewhere.

## API Contract

### `POST /expenses`

Create expense with JSON body:

```json
{
  "amount": "120.50",
  "category": "Food",
  "description": "Lunch",
  "date": "2026-04-20"
}
```

Optional header:

`Idempotency-Key: <unique-string>`

### `GET /expenses`

Query params:

- `category` (optional)
- `sort=date_desc` (optional)

## Tests

Backend tests include:

- idempotent create behavior
- list filtering and date descending sort

Run:

```bash
cd backend
pytest
```

## Timebox Trade-offs

- Kept auth/multi-user support out of scope (single-user exercise assumption).
- Implemented only the required list and total views (no advanced analytics UI).
- Used SQLite without migration tooling to keep setup minimal.

## Intentionally Not Done

- Authentication and authorization
- Pagination for large datasets
- Full E2E frontend tests
- Rich category summary charts
