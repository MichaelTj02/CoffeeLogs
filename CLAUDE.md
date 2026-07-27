# CoffeeLogs

A coffee tracker: record the beans you buy, then log how you brewed them. Portfolio
companion to CineScope — same normalized-relational-schema signal, but this repo adds the
testing and CI/CD pipeline CineScope was missing, and swaps PHP for Python.

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 ORM + Pydantic v2 |
| Database | MySQL 8 (InnoDB, utf8mb4), driver `PyMySQL` |
| Frontend | Next.js 14.2 (**pages** router), plain CSS, no component library |
| CI | GitHub Actions — lint + test + build, no Docker |

## Repo layout

```
CoffeeLogs/
├─ backend/            FastAPI app — own toolchain, rooted here for ruff/pytest
│  ├─ app/
│  │  ├─ database.py   engine, Base, get_db
│  │  ├─ models.py     SQLAlchemy models
│  │  ├─ schemas.py    Pydantic request/response models
│  │  ├─ crud.py       DB access functions
│  │  ├─ main.py       app assembly, CORS, /health
│  │  ├─ init_db.py    create tables (run explicitly, never on startup)
│  │  └─ routers/      beans.py, methods.py, attempts.py
│  ├─ requirements.txt
│  └─ pyproject.toml   ruff + pytest config
└─ frontend/           Next.js app — own toolchain, own lockfile
   ├─ components/      Navbar, BeanCard, StarButton
   ├─ lib/api.js       single fetch wrapper
   ├─ pages/           _app.js, index.js, logs.js, beans/[id].js
   └─ styles/globals.css
```

Backend and frontend are **independent siblings**. There is deliberately **no root
`package.json`** — `next lint` walks up the tree looking for ESLint config, and a root
manifest would make it resolve the wrong one.

## Data model

Three tables, two levels of foreign keys:

```
beans ──< brew_methods ──< brew_attempts
```

- **`beans`** — `id`, `name`, `roaster`, `origin`, `roast_date`, `price`, `notes`,
  `is_favourite`, `created_at`
- **`brew_methods`** — `id`, `bean_id` (FK), `name` ("V60", "AeroPress"), `created_at`.
  Unique on `(bean_id, name)`.
- **`brew_attempts`** — `id`, `brew_method_id` (FK), `brewed_at`, `dose_grams`,
  `yield_grams`, `rating` (1–5), `notes`

**Why three tables and not a `method` string column on the log?** Because a method is a
real thing you own per bean: you want to dial in a V60 recipe across several attempts and
see those attempts grouped. With a string column, `"V60"` and `"v60"` become separate
groups, and a method you plan to try but haven't brewed yet can't exist at all.

Deletes cascade **two levels**: removing a bean removes its methods, which removes their
attempts. This is configured in both places — `ondelete="CASCADE"` on each FK (enforced by
InnoDB) and `cascade="all, delete-orphan"` on each relationship (enforced by the ORM).

> The ORM cascade only fires for `db.delete(obj)`. A bulk `db.query(...).delete()` bypasses
> it entirely. Always load the object first.

## Conventions

Follow these when adding code — they are what the existing files do.

### SQLAlchemy — 2.0 style only

- `class Base(DeclarativeBase)`, not `declarative_base()`
- `Mapped[...]` + `mapped_column(...)`, not `Column(...)`
- `select()` + `.scalars()`, not `db.query()`; `db.get(Model, id)` for primary-key lookups

### Pydantic — v2 only

- `model_config = ConfigDict(from_attributes=True)`, not `class Config: orm_mode`
- `model_validate` / `model_dump`, not `from_orm` / `.dict()`
- `@field_validator`, not `@validator`

### MySQL-specific rules

- **Every `String` column needs an explicit length.** MySQL raises
  `CompileError: VARCHAR requires a length`; SQLite would accept it silently, so this only
  surfaces against the real database.
- **Every datetime column uses `.with_variant(mysql.DATETIME(fsp=6), "mysql")`.** Plain
  `DateTime` compiles to MySQL `DATETIME(0)` and silently discards sub-second precision,
  which makes two attempts logged in the same second tie under `ORDER BY brewed_at DESC`.
- **Schema `max_length` mirrors the column length.** MySQL runs `STRICT_TRANS_TABLES` and
  errors on over-length strings; validating at the API boundary turns a 500 into a 422.
- `price` is `Numeric(6,2)` in the model but typed `float` in the schema — Pydantic v2
  serializes `Decimal` to a JSON *string*, which would force `parseFloat` across the
  frontend. Storage stays exact; the wire format stays a number.

### API rules

- `POST` returns **201**; `DELETE` returns **204** with no `response_model` and a `None`
  return (a 204 with a body is a protocol violation)
- Ids that come from the URL path (`bean_id`, `brew_method_id`) **never** appear in
  `*Create` schemas — otherwise a client could POST to `/beans/1/methods` with
  `bean_id: 2`
- A duplicate brew-method name returns **409**, not a raw `IntegrityError` 500

### Frontend rules

- **Normalize empty strings to `null` before POST.** An empty `<input type="date">` yields
  `""`, which Pydantic rejects for `date | None` with a 422. Same for empty number inputs.
  This is the most common source of mystery 422s here.
- **Guard dynamic routes with `router.isReady`.** `router.query` is empty on first render,
  so an unguarded fetch hits `/beans/undefined`.
- **Global CSS may only be imported from `_app.js`** — importing it from a page is a hard
  build error in the pages router.
- Re-fetch after a mutation rather than patching local state; one code path, server-truth
  ordering. The favourite toggle is the deliberate exception — it updates optimistically so
  the star responds instantly.

## Environment

- **Node is 18.17.0** — *exactly* Next 14.2's minimum. Next 15 requires ≥18.18.0, so never
  run `create-next-app@latest`. `next` and `eslint` are pinned without carets; ESLint must
  stay on 8.x because `eslint-config-next@14.2` targets the `.eslintrc` format.
- **Use `py -3.12`, not bare `python`** — `python` on PATH is 3.10.0 here, while the `py`
  launcher defaults to 3.12.
- **MySQL must be running** (`Get-Service MySQL80`). The app has no SQLite fallback; only
  the test suite uses SQLite, via a dependency override.
- **PowerShell**, so: no `export` (use `.env` or `$env:VAR`), and no `curl -X` (`curl`
  aliases to `Invoke-WebRequest`, which rejects `-X` — use `Invoke-RestMethod`).

## Commands

```powershell
# Backend (from backend/)
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.init_db                              # create tables
uvicorn app.main:app --reload --port 8000          # docs at /docs

# Frontend (from frontend/)
npm install
npm run dev                                        # http://localhost:3000
```

## Commit convention

All commits and PR titles follow **Conventional Commits v1.0.0**:

```
<type>[(scope)][!]: <description>

[optional body]

[optional footer(s)]
```

- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`,
  `chore`. `feat` is for new features, `fix` for bug fixes.
- **Scopes**: `backend`, `frontend`, `db`, `api`, `beans`, `methods`, `attempts`, `ui`,
  `ci`, `deps`
- **Description**: lowercase, imperative, no trailing period, immediately after `: `
- **Body**: optional, one blank line after the description
- **Footers**: optional, one blank line after the body; tokens use `-` for spaces
  (`Reviewed-by`, `Refs`)
- **Breaking changes**: `!` before the colon and/or a `BREAKING CHANGE: <description>`
  footer. `BREAKING CHANGE` must be uppercase; `BREAKING-CHANGE` is synonymous. With `!`,
  the footer may be omitted.

Examples:

```
feat(api): add brew method and attempt endpoints
fix(frontend): send null instead of empty string for blank roast date
docs: document the two-level cascade
feat(api)!: address attempts by their own id

BREAKING CHANGE: attempts moved from /beans/{id}/methods/{mid}/attempts to /attempts
```
