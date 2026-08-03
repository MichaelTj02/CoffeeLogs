# CoffeeLogs

Track the coffee beans you buy, the methods you brew them with, and how every attempt
turned out. Log a bag of Ethiopia Yirgacheffe, add a V60 and an AeroPress to it, then
record each brew's dose, yield, and rating so you can watch a recipe get dialled in over
time.

```
beans ──< brew_methods ──< brew_attempts
```

A brew method is a thing you own per bean rather than a label you retype, which is what
makes attempts group under it and "am I improving?" answerable.

**Stack** — FastAPI · SQLAlchemy 2.0 · Pydantic v2 · MySQL 8 · Next.js 14.2 (pages
router) · pytest + Jest · GitHub Actions.

## Requirements

- **Python 3.12** — on Windows use `py -3.12`; a bare `python` may resolve to an older one
- **Node 18.17.0** — Next 14.2's minimum. Don't run `create-next-app@latest`; Next 15
  needs ≥18.18.0 and will hard-fail
- **MySQL 8**, running. There's no SQLite fallback — only the tests use SQLite

## Setup

One-time, from a fresh clone.

**Database.** On Windows `mysql.exe` usually isn't on `PATH`; it's in
`C:\Program Files\MySQL\MySQL Server 8.0\bin`.

```sql
CREATE DATABASE coffeelogs CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'coffeelogs'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON coffeelogs.* TO 'coffeelogs'@'localhost';
FLUSH PRIVILEGES;
```

**Backend.**

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

Then create the tables — deliberately explicit, the app never runs DDL on startup:

```powershell
python -m app.init_db
```

**Frontend.**

```powershell
cd frontend
npm install
```

No env file is needed locally; the API client defaults to `http://localhost:8000`. To point
it elsewhere, create `frontend/.env.local` with `NEXT_PUBLIC_API_URL=<url>`.

## Running

With MySQL running, from the repo root:

```powershell
.\dev.ps1
```

That starts both dev servers in their own windows. Stop either with Ctrl+C in its window.
The script warns if the `MySQL80` service is down but can't start it for you — that needs
an elevated shell (`Start-Service MySQL80`).

| | |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

To run them by hand instead:

```powershell
# from backend/
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

# from frontend/
npm run dev
```

Activating the venv first is optional — `Activate.ps1` only puts `.venv\Scripts` on `PATH`,
so naming the executable inside it does the same job.

## Tests

```powershell
cd backend;  pip install -r requirements-dev.txt;  ruff check .;  pytest
cd frontend; npm run lint;  npm test;  npm run build
```

Conventions for contributors are in [CLAUDE.md](CLAUDE.md).
