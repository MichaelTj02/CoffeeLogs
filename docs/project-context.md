# CoffeeLogs — Session Handoff Context

Paste or attach this at the start of a new session to transfer full project context.
Written 2026-08-03. Repo: `C:\Users\mtj02\Desktop\CoffeeLogs` ·
`github.com/MichaelTj02/CoffeeLogs`

---

## What this is

A coffee tracker: record beans you buy, then log how you brewed them. Portfolio companion
to the author's CineScope project — same normalized-relational-schema signal, but this repo
adds the testing/CI pipeline CineScope lacked and swaps PHP for Python.

The author is **learning web development through this project** and has asked to build
things together rather than have them appear finished. Prefer explaining the reasoning
behind a choice over just making it.

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 ORM + Pydantic v2 |
| Database | MySQL 8.0 (InnoDB, utf8mb4), driver PyMySQL |
| Frontend | Next.js 14.2.18, **pages** router, plain CSS, no component library |
| CI | GitHub Actions — planned, not yet written |

---

## Current state

**The web app is complete and verified working end to end against real MySQL.**

| Piece | Status |
|---|---|
| Backend models, schemas, CRUD, routers | Done |
| All 10 API endpoints | Done, verified |
| Frontend: 3 pages + navbar + components | Done |
| MySQL database, tables created | Done, schema verified |
| `CLAUDE.md`, `docs/how-it-works.md`, this file | Done |
| **Automated tests (pytest)** | **Not started** |
| **GitHub Actions CI** | **Not started** |
| **README** | **Not started** — repo has a one-line stub |

### Git state

- `main` has the full app. PR #1 was **rebase-merged**, so main's commits have different
  SHAs than the original branch — beware, a diff against the old branch shows the whole
  project as "new".
- **PR #2 is open**: `chore/remove-env-example`, removing `backend/.env.example` (7 lines).
  That is the current branch.
- Uncommitted at time of writing: `docs/how-it-works.md`, `docs/project-context.md`,
  the `CLAUDE.md` comment-convention section, and a repo-wide comment-trimming pass.
  These should go on their own branch off `main`, not onto PR #2.
- All commits and PR titles follow **Conventional Commits v1.0.0**. This is
  non-negotiable — see CLAUDE.md for types, scopes, and examples.

---

## Data model — three tables, two FK levels

```
beans ──< brew_methods ──< brew_attempts
```

- **`beans`** — `id`, `name`, `roaster`, `origin`, `roast_date`, `price`, `notes`,
  `is_favourite`, `created_at`
- **`brew_methods`** — `id`, `bean_id` (FK), `name`, `created_at`. `UNIQUE (bean_id, name)`
- **`brew_attempts`** — `id`, `brew_method_id` (FK), `brewed_at`, `dose_grams`,
  `yield_grams`, `rating` (1–5), `notes`

**Why three tables, not a `method` string column on the log** — this was a deliberate
decision, don't "simplify" it away. A method is a real thing you own per bean: `"V60"` and
`"v60"` would otherwise split into separate groups, and a method you plan to try but
haven't brewed yet couldn't exist at all.

Deletes cascade **two levels**, configured in both places on purpose: `ondelete="CASCADE"`
on each FK (InnoDB enforces it) and `cascade="all, delete-orphan"` on each relationship
(the ORM enforces it). The ORM cascade only fires for `db.delete(obj)` — a bulk
`db.query(...).delete()` bypasses it entirely.

## API

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | |
| GET/POST | `/beans` | list favourites-first; POST → 201 |
| GET | `/beans/{id}` | nested methods → nested attempts |
| PATCH | `/beans/{id}/favourite` | body `{is_favourite}` |
| DELETE | `/beans/{id}` | 204, cascades two levels |
| GET/POST | `/beans/{id}/methods` | duplicate name → **409** |
| DELETE | `/methods/{id}` | 204, cascades to attempts |
| GET/POST | `/methods/{id}/attempts` | |
| DELETE | `/attempts/{id}` | 204 |

Methods and attempts are created under their parent but addressed by their **own id** for
deletion — ids are globally unique, so deeper nesting adds path noise for nothing.

## Frontend pages

- `/` (`pages/index.js`) — add-bean form + 5 most recent beans. No brew fields here.
- `/logs` (`pages/logs.js`) — all beans, favourites first, optimistic star toggle, delete.
- `/beans/[id]` — bean header, add-method form, one section per method with its attempts
  and its own attempt form.

Navbar (`CoffeeLogs` → `/`, `Logs` → `/logs`) is in `_app.js`, so it wraps every page.

Data is fetched **client-side**, deliberately: `next build` then has no build-time
dependency on a running backend, and the browser genuinely makes cross-origin requests so
the CORS config is exercised rather than being dead configuration.

---

## Environment — verified facts, not assumptions

- **Node is exactly v18.17.0**, which is Next 14.2's exact minimum. Next 15 requires
  ≥18.18.0 and hard-fails. **Never run `create-next-app@latest`.** `next` and `eslint` are
  pinned without carets; ESLint must stay 8.x because `eslint-config-next@14.2` targets the
  `.eslintrc` format.
- **Use `py -3.12`, not bare `python`** — `python` on PATH is 3.10.0; the `py` launcher
  defaults to 3.12. The venv at `backend/.venv` is 3.12.6.
- **MySQL 8.0** runs as Windows service `MySQL80`. `mysql.exe` is at
  `C:\Program Files\MySQL\MySQL Server 8.0\bin` and is **not on PATH**.
- DB user `coffeelogs` / database `coffeelogs`. Credentials live in `backend/.env`
  (gitignored). The password is weak and localhost-only by choice.
- **PowerShell**: no `export` (use `.env`), and no `curl -X` — `curl` aliases to
  `Invoke-WebRequest`, which rejects `-X`. Use `Invoke-RestMethod`.
- `gh` CLI is installed at `C:\Program Files\GitHub CLI\gh.exe` and authenticated.
- Desktop is **not** OneDrive-redirected, so no file-lock issues with `.next`/`node_modules`.

### Running it

```powershell
# Terminal 1 — backend (from backend/)
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000     # docs at /docs

# Terminal 2 — frontend (from frontend/)
npm run dev                                    # http://localhost:3000
```

Backend first; the frontend fetches on load.

---

## Verified against real MySQL — do not re-litigate these

| Check | Result |
|---|---|
| `ENGINE=InnoDB`, `ON DELETE CASCADE` on both FKs | confirmed via `SHOW CREATE TABLE` |
| `price` DECIMAL exactness | `18.50` in, `18.50` out |
| `datetime(6)` microseconds | two attempts at `.104609` and `.113730` |
| Two-level cascade | beans/methods/attempts `1/1/2` → `0/0/0` |
| `caching_sha2_password` via PyMySQL + `cryptography` | works |
| Duplicate method name | 409 |
| CORS preflight for `PATCH` | 200 with correct headers |
| API behaviour | 38 assertions across all 10 endpoints |
| `ruff check`, `next lint`, `next build` | all clean |

**Not verified: the browser click-through.** The preview pane was never displayed, so the
tab reported `document.hidden` and `requestAnimationFrame` never fired; React never
hydrated and both pages sat on their initial loading markup. Confirmed environmental
(`#__next` had no React container while manual fetches from the same page returned 200),
not a code fault. If the pane can be displayed, this is worth completing.

---

## Traps that already bit, or nearly did

1. **`DATETIME(6) DEFAULT now()` is MySQL error 1067** — `CURRENT_TIMESTAMP` precision must
   match the column's. Fixed by dropping `server_default` from `created_at`; the
   Python-side default covers every insert. *This was caught by compiling the schema
   against the MySQL dialect before MySQL was even installed.*
2. **Plain `DateTime` becomes MySQL `DATETIME(0)`** and silently truncates sub-second
   precision. Every datetime column uses
   `.with_variant(mysql.DATETIME(fsp=6), "mysql")`. Real attempts landed 9 ms apart —
   without this they'd have tied under `ORDER BY brewed_at DESC`.
3. **Every `String` column needs an explicit length** or MySQL raises
   `CompileError: VARCHAR requires a length`. SQLite accepts it silently, so this only
   surfaces against the real database.
4. **`from app import models` in `init_db.py` is load-bearing** — `create_all` iterates
   `Base.metadata`, which is only populated as a side effect of the class definitions.
   Without it, `create_all` succeeds and creates **zero tables**.
5. **`ignore = ["B008"]` in ruff config is required** — B008 flags "function call in
   default argument", which is exactly `db: Session = Depends(get_db)` on every endpoint.
6. **Empty strings must be normalized to `null` before POST** — an empty
   `<input type="date">` yields `""`, which Pydantic rejects for `date | None` with a 422.
   The single most common source of mystery 422s here.
7. **`router.isReady` guard is mandatory** in `pages/beans/[id].js` — `router.query` is
   empty on first render, so an unguarded fetch hits `/beans/undefined`.
8. **A 204 has no body** — calling `res.json()` on it throws `Unexpected end of JSON
   input`. Every delete hits this.
9. **FastAPI has two error shapes** — `detail` is a string for `HTTPException` but an
   **array** of objects for 422. Handle only one and the UI renders `[object Object]`.
10. **Global CSS may only be imported from `_app.js`** — a hard build error otherwise.
11. **`cache-dependency-path` in GitHub Actions is repo-root-relative** and unaffected by
    `working-directory`. Relevant when the CI workflow gets written.

---

## Conventions (full detail in CLAUDE.md)

- **SQLAlchemy 2.0 style only** — `DeclarativeBase`, `Mapped[]`/`mapped_column`,
  `select()` + `.scalars()`. Never `declarative_base()`, `Column()`, or `db.query()`.
- **Pydantic v2 only** — `ConfigDict(from_attributes=True)`, `model_validate`,
  `model_dump`. Never `orm_mode`, `from_orm`, `.dict()`.
- `POST` → 201; `DELETE` → 204 with no `response_model` and a `None` return.
- Path-derived ids (`bean_id`, `brew_method_id`) never appear in `*Create` schemas.
- `price` is `Numeric(6,2)` in the model but typed `float` in the schema — Pydantic v2
  serializes `Decimal` to a JSON *string*, which would force `parseFloat` across the
  frontend.
- **Comments are sparse by design.** Default to none; write one only where a competent
  developer would still be surprised. No docstrings restating signatures, no section
  banners, no inline design essays. Max 1–2 lines. This was applied repo-wide
  deliberately — do not "helpfully" re-add explanatory comments.

---

## Next steps, in order

1. **pytest suite** — `backend/tests/` with in-memory SQLite via `dependency_overrides`,
   so tests need no MySQL. Requires `poolclass=StaticPool` (so the `:memory:` DB survives
   across connections) and `connect_args={"check_same_thread": False}` (TestClient runs the
   app on another thread), plus a `PRAGMA foreign_keys=ON` event listener — SQLite ships
   with FK enforcement **off**, so the cascade would otherwise go untested. Cover: health,
   bean CRUD, 404s, rating/name validation, duplicate-method 409, favourite toggle, and the
   two-level cascade asserted against the session.
2. **A MySQL DDL compile test** — compile every table against `mysql.dialect()` on a runner
   with no database. Catches a missing VARCHAR length in milliseconds. Cheapest insurance
   available.
3. **GitHub Actions CI** — two jobs: `ruff check` + `pytest`, and `npm run lint` +
   `npm run build`. Pin Node to `"18.17.0"`. `npm ci` needs the committed lockfile. Linux
   runners are case-sensitive where Windows isn't.
4. **README** — setup, API table, env vars, troubleshooting, design notes.

Dev dependencies not yet in a requirements file: `pytest`, `httpx==0.27.2` (pin matters —
0.28 removed the `app=` shortcut `TestClient` relies on), `ruff==0.8.4`. `httpx` and `ruff`
are already installed in the venv; a `requirements-dev.txt` should be created.
