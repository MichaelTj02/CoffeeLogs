# CoffeeLogs

Track the coffee beans you buy, the methods you brew them with, and how every attempt
turned out. Log a bag of Ethiopia Yirgacheffe, add a V60 and an AeroPress to it, then
record each brew's dose, yield, and rating so you can see a recipe get dialled in over
time.

FastAPI + MySQL on the back, Next.js on the front, with a test suite and CI pipeline.

---

## Why three tables

```
beans ──< brew_methods ──< brew_attempts
```

The obvious shortcut is a single `method` text column on each log entry. This schema uses a
real table instead, because a brew method is a thing you *own* per bean rather than a label
you retype:

- `"V60"` and `"v60"` would silently become separate groups
- A method you plan to try but haven't brewed yet couldn't exist at all
- Grouping attempts under a method is what makes "am I improving?" answerable

Deletes cascade two levels — removing a bean removes its methods, which removes their
attempts. That's configured in both the database (`ON DELETE CASCADE`) and the ORM
(`cascade="all, delete-orphan"`), so it holds whether a row is deleted through the API or
by hand in SQL.

| Table | Columns |
|---|---|
| `beans` | `id`, `name`, `roaster`, `origin`, `roast_date`, `price`, `notes`, `is_favourite`, `created_at` |
| `brew_methods` | `id`, `bean_id` → `beans`, `name`, `created_at` · unique on `(bean_id, name)` |
| `brew_attempts` | `id`, `brew_method_id` → `brew_methods`, `brewed_at`, `dose_grams`, `yield_grams`, `rating` (1–5), `notes` |

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI 0.115 · SQLAlchemy 2.0 ORM · Pydantic v2 |
| Database | MySQL 8 (InnoDB, utf8mb4) via PyMySQL |
| Frontend | Next.js 14.2 (pages router) · plain CSS, no component library |
| Tests | pytest (backend, SQLite) · Jest + Testing Library (frontend) |
| CI | GitHub Actions — lint, test, build for both apps |

---

## Requirements

- **Python 3.12** — on Windows use `py -3.12`; a bare `python` may resolve to an older one
- **Node 18.17.0** — Next 14.2's minimum. Do not run `create-next-app@latest`; Next 15
  requires ≥18.18.0 and will hard-fail
- **MySQL 8**, running. There is no SQLite fallback — only the test suite uses SQLite

## Setup

One-time, from a clone.

**1. Create the database and user.** On Windows `mysql.exe` is usually not on `PATH`; it
lives in `C:\Program Files\MySQL\MySQL Server 8.0\bin`.

```sql
CREATE DATABASE coffeelogs CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'coffeelogs'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON coffeelogs.* TO 'coffeelogs'@'localhost';
FLUSH PRIVILEGES;
```

**2. Backend.**

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `backend/.env` (gitignored):

```
DATABASE_URL=mysql+pymysql://coffeelogs:your-password@localhost:3306/coffeelogs?charset=utf8mb4
```

Then create the tables. This is deliberately explicit — the app never runs DDL on startup:

```powershell
python -m app.init_db
```

**3. Frontend.**

```powershell
cd frontend
npm install
```

No env file is needed for local work: the API client defaults to `http://localhost:8000`.
To point it elsewhere, copy `.env.local.example` to `.env.local` and set
`NEXT_PUBLIC_API_URL`.

## Running

With MySQL running, from the repo root:

```powershell
.\dev.ps1
```

That opens both dev servers in their own windows and prints their URLs. Stop either with
Ctrl+C in its window. The script warns if the `MySQL80` service isn't running, but can't
start it for you — that needs an elevated shell (`Start-Service MySQL80`).

To run them by hand instead:

```powershell
# backend, from backend/
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

# frontend, from frontend/
npm run dev
```

Activating the venv first is optional. `Activate.ps1` only puts `.venv\Scripts` on `PATH`;
naming the executable inside it does the same job in one line.

| | |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |

### Pages

- `/` — add a bean, and the five most recently added
- `/logs` — every bean, favourites first, with a star toggle and delete
- `/beans/[id]` — one bean, its methods, and each method's attempts

Data is fetched client-side on purpose: `next build` then has no build-time dependency on a
running backend, and the browser genuinely exercises the CORS configuration.

---

## API

| Method | Path | Notes |
|---|---|---|
| `GET` | `/health` | |
| `GET` | `/beans` | favourites first; `?sort=recent` for pure recency, `?limit=n` to cap |
| `POST` | `/beans` | → 201 |
| `GET` | `/beans/{id}` | nested methods, each with its attempts |
| `PATCH` | `/beans/{id}/favourite` | body `{"is_favourite": true}` |
| `DELETE` | `/beans/{id}` | → 204, cascades two levels |
| `GET` | `/beans/{id}/methods` | |
| `POST` | `/beans/{id}/methods` | duplicate name for the same bean → 409 |
| `DELETE` | `/methods/{id}` | → 204, cascades to attempts |
| `GET` | `/methods/{id}/attempts` | |
| `POST` | `/methods/{id}/attempts` | |
| `DELETE` | `/attempts/{id}` | → 204 |

Methods and attempts are created under their parent but addressed by their own id for
deletion — ids are globally unique, so deeper nesting would add path noise for nothing.

### Datetimes

Timestamps are stored as naive `DATETIME(6)` holding UTC. The API accepts `brewed_at` with
any offset and normalizes it; naive input is assumed to already be UTC. Every datetime in a
response carries an explicit offset:

```json
{ "created_at": "2026-07-27T20:45:44.006437Z" }
```

Microsecond precision survives the round trip, which is what keeps two attempts logged in
the same second from tying under `ORDER BY brewed_at DESC`.

---

## Tests

```powershell
# backend, from backend/
pip install -r requirements-dev.txt
ruff check .
pytest

# frontend, from frontend/
npm run lint
npm test
npm run build
```

The backend suite runs against in-memory SQLite through a `get_db` dependency override, so
it needs no database and no network. That's a deliberate trade: it keeps CI free of a MySQL
service, at the cost of not catching MySQL-dialect-only errors such as a missing `VARCHAR`
length.

CI runs all of the above on every pull request and every push to `main`, as two parallel
jobs.

## Configuration

| Variable | Where | Default |
|---|---|---|
| `DATABASE_URL` | `backend/.env` | `mysql+pymysql://coffeelogs:coffeelogs@localhost:3306/coffeelogs?charset=utf8mb4` |
| `CORS_ORIGINS` | `backend/.env` | `http://localhost:3000,http://127.0.0.1:3000` |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | `http://localhost:8000` |

`NEXT_PUBLIC_API_URL` is inlined at build time, not read at runtime — changing it requires
a restart or rebuild.

## Troubleshooting

**"Could not reach the API. Is the backend running on port 8000?"** — the backend isn't up,
or it started and then died because MySQL is unreachable. Check its window.

**`Invoke-RestMethod http://localhost:8000/health` times out while the browser works.**
Uvicorn binds IPv4 only, and PowerShell resolves `localhost` to IPv6 `::1` without falling
back. Use `http://127.0.0.1:8000/...` from PowerShell. Also note `curl` is an alias for
`Invoke-WebRequest`, which rejects `-X` — use `Invoke-RestMethod -Method`.

**A form returns 422 on an empty optional field.** An empty `<input type="date">` submits
`""`, which is not a valid `date | None`. Blank inputs must be normalized to `null` before
posting.

**`npm install` warns `EBADENGINE`.** A transitive lint dependency asks for Node ≥18.18.0.
The warnings are harmless — nothing sets `engine-strict`, and the pinned direct
dependencies all support 18.17.0.

**Port already in use.** Find the owner with
`Get-NetTCPConnection -State Listen -LocalPort 8000`.

---

## Repository layout

`backend/` and `frontend/` are independent siblings with their own toolchains and
lockfiles. There is deliberately **no root `package.json`** — `next lint` walks up the tree
looking for ESLint config, and a root manifest makes it resolve the wrong one.

```
backend/
  app/
    database.py   engine, Base, get_db
    models.py     SQLAlchemy models
    schemas.py    Pydantic request/response models
    crud.py       database access
    deps.py       shared 404 lookups
    main.py       app assembly, CORS, /health
    init_db.py    create tables (run explicitly)
    routers/      beans.py, methods.py, attempts.py
  tests/
frontend/
  components/     Navbar, BeanCard, StarButton, AttemptForm
  lib/            api.js (fetch wrapper), format.js
  pages/          _app.js, index.js, logs.js, beans/[id].js
  styles/
```

Conventions for contributors — SQLAlchemy 2.0 style, Pydantic v2 only, the comment policy,
and Conventional Commits without scopes — are documented in [CLAUDE.md](CLAUDE.md).
