# CoffeeLogs

Track the coffee beans you buy, the methods you brew them with, and how every attempt
turned out. Log a bag of Ethiopia Yirgacheffe, add a V60 and an AeroPress to it, then
record each brew's dose, yield, and rating so you can watch a recipe get dialled in over
time.

**Stack** — FastAPI · SQLAlchemy 2.0 · Pydantic v2 · MySQL 8 · Next.js 14.2 (pages
router) · pytest + Jest · Docker Compose · GitHub Actions.

## Running with Docker

The default way to run it, on any OS. You only need **Docker** with Compose v2 (Docker
Desktop on macOS/Windows, Docker Engine on Linux) — no local Python, Node or MySQL.

One-time, from a fresh clone:

```bash
cp .env.example .env    # then set real passwords; avoid @ : / ? # (they go into a URL)
docker compose up -d --build
docker compose run --rm backend python -m app.init_db
```

`init_db` creates the tables — deliberately explicit, the app never runs DDL on startup.
It only needs running once per database, and re-running it is harmless.

| | |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 (this machine only) |
| API docs | http://localhost:8000/docs |

**From a phone or another device** on the same network, open `http://<host-ip>:3000`.
Find the IP with `ipconfig getifaddr en0` on macOS or `ipconfig` on Windows, and allow
the firewall prompt the first time. The browser only ever talks to port 3000 — the
frontend proxies `/api` to the backend — so nothing else needs opening.

Day to day:

```bash
docker compose up -d --build     # start, rebuilding anything that changed
docker compose down              # stop; your data is kept
docker compose logs -f backend   # follow one service's logs
```

> `docker compose down -v` also deletes the `mysql-data` volume — every bean you've logged.

## Native development

Running the apps directly on the host, e.g. for hot reload.

### Requirements

- **Python 3.12** — on Windows use `py -3.12`; a bare `python` may resolve to an older one
- **Node 18.17.0** — Next 14.2's minimum. Don't run `create-next-app@latest`; Next 15
  needs ≥18.18.0 and will hard-fail
- **MySQL 8**, running. There's no SQLite fallback — only the tests use SQLite

### Setup

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

Then create the tables:

```powershell
python -m app.init_db
```

**Frontend.**

```powershell
cd frontend
npm install
```

No env file is needed locally. The browser calls `/api/...` on the frontend's own origin,
and Next.js proxies it to `http://localhost:8000`. To proxy somewhere else, set
`BACKEND_URL` before `next build` / `next dev` (it is baked in at build time); to skip the
proxy and call an API directly, create `frontend/.env.local` with
`NEXT_PUBLIC_API_URL=<url>`.

### Running

On Windows, with MySQL running, from the repo root:

```powershell
.\dev.ps1
```

That starts both dev servers in their own windows. Stop either with Ctrl+C in its window.
The script warns if the `MySQL80` service is down but can't start it for you — that needs
an elevated shell (`Start-Service MySQL80`).

To run them by hand instead (URLs as in the table above):

```powershell
# from backend/
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

# from frontend/
npm run dev
```

Activating the venv first is optional — `Activate.ps1` only puts `.venv\Scripts` on `PATH`,
so naming the executable inside it does the same job. On macOS/Linux the venv lives under
`.venv/bin` instead.

## CI

GitHub Actions runs three jobs on every push and PR: backend (ruff + pytest), frontend
(lint + Jest + build), and `docker`, which builds both images, starts the Compose stack,
runs `init_db` against real MySQL, and smoke-tests the API directly and through the
frontend's `/api` proxy. The unit tests use SQLite, so that job is the only place
MySQL-specific schema errors surface.
