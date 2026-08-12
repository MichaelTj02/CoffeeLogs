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
│  │  ├─ models.py     SQLAlchemy models, utcnow
│  │  ├─ schemas.py    Pydantic request/response models
│  │  ├─ crud.py       DB access functions
│  │  ├─ security.py   argon2 hashing, session tokens, cookie name + TTL
│  │  ├─ deps.py       get_current_user, the *_or_404 lookups
│  │  ├─ main.py       app assembly, CORS, /health
│  │  ├─ init_db.py    create tables (run explicitly, never on startup)
│  │  └─ routers/      auth.py, beans.py, methods.py, attempts.py
│  ├─ tests/           pytest suite — SQLite through a get_db override
│  ├─ requirements.txt
│  ├─ requirements-dev.txt   pytest, httpx, ruff
│  └─ pyproject.toml   ruff + pytest config
├─ frontend/           Next.js app — own toolchain, own lockfile
│  ├─ components/      Navbar, BeanCard, StarButton, AttemptForm, AuthGuard
│  ├─ lib/             api.js (single fetch wrapper), auth.js (AuthProvider/useAuth),
│  │                   format.js
│  ├─ pages/           _app.js, index.js, logs.js, login.js, register.js, beans/[id].js
│  ├─ __tests__/       page tests; component and lib tests sit beside their source
│  └─ styles/globals.css
├─ .github/workflows/  ci.yml — lint + test + build
└─ dev.ps1             starts both dev servers in their own windows
```

Backend and frontend are **independent siblings**. There is deliberately **no root
`package.json`** — `next lint` walks up the tree looking for ESLint config, and a root
manifest would make it resolve the wrong one.

## Data model

Five tables. Everything hangs off a user:

```
users ──< beans ──< brew_methods ──< brew_attempts
   └──< sessions
```

- **`users`** — `id`, `email` (unique, indexed, stored lowercase), `password_hash`,
  `created_at`
- **`sessions`** — `id`, `user_id` (FK), `token_hash` (unique, indexed), `created_at`,
  `expires_at`. The model class is `UserSession`, because `Session` is
  `sqlalchemy.orm.Session` everywhere else here.
- **`beans`** — `id`, `user_id` (FK), `name`, `roaster`, `origin`, `roast_date`, `price`,
  `notes`, `is_favourite`, `created_at`
- **`brew_methods`** — `id`, `bean_id` (FK), `name` ("V60", "AeroPress"), `created_at`.
  Unique on `(bean_id, name)`.
- **`brew_attempts`** — `id`, `brew_method_id` (FK), `brewed_at` (a `Date`, not a
  timestamp), `dose_grams`, `yield_grams`, `rating` (1–5), `notes`

`brewed_at` is a **calendar date on purpose.** The day you brewed is the same day in every
timezone, so there is nothing to convert, and the time of day carries no information worth
storing. It behaves exactly like `roast_date`: sent and received as a bare `YYYY-MM-DD`
string, never an instant. Because several attempts a day is the normal case, everything
ordering by `brewed_at DESC` **must** carry an `id DESC` tiebreaker — both `crud` and the
`BrewMethod.attempts` relationship do.

**Why a `brew_methods` table and not a `method` string column on the log?** Because a method
is a real thing you own per bean: you want to dial in a V60 recipe across several attempts and
see those attempts grouped. With a string column, `"V60"` and `"v60"` become separate
groups, and a method you plan to try but haven't brewed yet can't exist at all.

A session row stores `sha256(raw_token)`, never the raw token — the token is handed to the
browser once, at creation, and cannot be recovered from the database afterwards, so a dump
holds no usable credential. **sha256 and not argon2** is the right call here: the token is
256 bits of `secrets` entropy, so there is nothing to brute-force and no reason to pay
argon2's cost on every request. Passwords, which *are* guessable, use argon2.

Sessions get a **fixed 30-day TTL, no sliding renewal**. Expired rows are deleted lazily —
when the owner logs in, and when an expired cookie is presented — so they linger until
something touches them.

Datetime values are **naive UTC**, matching every other stored datetime here. Anything
computed against a loaded datetime (`expires_at`, the expiry check) must use the public
`models.utcnow` helper, never `datetime.now(UTC)`: comparing an aware `now` with a naive
column value raises `TypeError` and surfaces as a 500.

Deletes cascade **from the user down**: removing a user removes their sessions and their
beans, which removes those beans' methods, which removes their attempts. This is configured
in both places — `ondelete="CASCADE"` on each FK (enforced by InnoDB) and
`cascade="all, delete-orphan"` on each relationship (enforced by the ORM).

> The ORM cascade only fires for `db.delete(obj)`. A bulk `db.query(...).delete()` bypasses
> it entirely. Always load the object first.

## Conventions

Follow these when adding code — they are what the existing files do.

### Comments — sparse, and only where the code can't speak

Default to **no comment**. Well-named functions and variables carry the intent; a comment
that restates the code is noise that goes stale. This applies when editing existing code
too — delete a restating comment on sight rather than carrying it along.

Write one only when a reader who understands the language would still be surprised:

- Behaviour that contradicts what the code appears to do — a "useless" import that is
  actually load-bearing, a redundant-looking check that prevents a real failure
- A database or framework quirk that is invisible in the source (MySQL truncating
  sub-second precision, SQLite not enforcing foreign keys by default)
- A non-obvious algorithm, or a deliberate trade-off someone would otherwise "fix"

Never write:

- Docstrings or comments that restate the signature (`"""Bean endpoints."""`,
  `# returns the bean`)
- Section-divider banners
- Explanations of standard language or framework idioms
- Design rationale that belongs in this file or in `docs/` — link the idea, don't inline
  an essay

Keep them to one or two lines. If it needs a paragraph, it belongs in documentation.

### SQLAlchemy — 2.0 style only

- `class Base(DeclarativeBase)`, not `declarative_base()`
- `Mapped[...]` + `mapped_column(...)`, not `Column(...)`
- `select()` + `.scalars()`, not `db.query()`; `db.get(Model, id)` for primary-key lookups —
  **except** `get_bean`, `get_method` and `get_attempt`, which use a filtered `select()`
  because a primary-key lookup cannot carry the ownership filter. "Restoring the convention"
  there would silently delete the ownership check.

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
  which makes two rows written in the same second tie under an `ORDER BY` on that column.
  This applies to the `created_at` columns; `brewed_at` is a plain `Date` and is exempt.
- **Schema `max_length` mirrors the column length.** MySQL runs `STRICT_TRANS_TABLES` and
  errors on over-length strings; validating at the API boundary turns a 500 into a 422.
- `price` is `Numeric(6,2)` in the model but typed `float` in the schema — Pydantic v2
  serializes `Decimal` to a JSON *string*, which would force `parseFloat` across the
  frontend. Storage stays exact; the wire format stays a number.

### Ownership

- Every data endpoint takes `user: User = Depends(get_current_user)` and threads `user.id`
  down. `/health` and the `/auth` routes are the exceptions — `/auth/me` still
  authenticates, it just has nothing to scope.
- **The filter is applied once, at the top-most lookup.** Scoped crud functions take
  `user_id` immediately after `db`; below an already-resolved bean, ids are trusted, and the
  crud functions that trust one carry a one-line comment saying so. Don't add a second
  filter deeper down, and don't drop the comment that explains why there isn't one.
- **Someone else's row is a 404, not a 403.** A 403 is an existence oracle over sequential
  ids.
- `user_id` appears in **no** Pydantic schema — it comes from the session, never the body.
- Methods and attempts have no `user_id` column; ownership derives by joining up to `beans`.

### API rules

- A `POST` that **creates a resource** returns **201**; `DELETE` returns **204** with no
  `response_model` and a `None` return (a 204 with a body is a protocol violation).
  `POST /auth/login` returning 200 and `POST /auth/logout` returning 204 are deliberate —
  neither creates a resource the client addresses afterwards
- Auth lives under `/auth`: `POST /register` (201 `UserRead` + `Set-Cookie`, auto-login;
  409 on a duplicate email), `POST /login` (200 `UserRead` + `Set-Cookie`; 401 with one
  detail string for both unknown email and wrong password), `POST /logout` (204, and never
  errors — it reads the cookie directly rather than through `get_current_user`, because
  logging out twice has to succeed), `GET /me` (200 `UserRead`, else 401)
- `get_current_user` reads the cookie as `Cookie(default=None, ...)`. The `None` default is
  what makes an anonymous 401 possible: a required cookie makes FastAPI answer **422** before
  the handler body ever runs
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
- **`AuthGuard` in `_app.js` is the single choke point** for "is this page reachable". Pages
  don't check auth themselves, which is also why page tests can render them directly.
- **`signIn(user)` stores the `UserRead` that login and register already return.** `_app.js`
  never remounts on client-side navigation, so without it the guard still sees
  `user === null` after a successful login and bounces straight back to `/login`.
- **`AuthGuard` renders the `.state` div in every non-final state**, not just while loading.
  `router.replace` is async, so falling through mounts the real page for a frame — its
  effects fire a burst of 401s, and the mirror case flashes the login form at a signed-in
  user.
- **Trim the email, never the password.** Trailing whitespace can be part of a password;
  trimming it silently mutates a valid credential.

### CSRF and the localhost/127.0.0.1 trap

`localhost:3000 → localhost:8000` is cross-origin but **same-site**, so the `Lax` session
cookie flows with `credentials: "include"`. That is also the protection: `Lax` blocks
cross-site non-GET requests, every body is JSON (so it is preflighted and fails CORS from a
foreign origin), and `Lax`'s top-level-GET carve-out only reaches read-only endpoints. No
CSRF token.

> Browse the app at **`http://localhost:3000`**, never `http://127.0.0.1:3000`. Against an
> API on `localhost:8000` that is cross-*site*, so the browser drops the cookie while CORS
> still succeeds — auth breaks with no error anywhere. `127.0.0.1:3000` is deliberately
> absent from the API's origin list so the failure is loud instead of silent.

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
<type>[!]: <description>

[optional body]

[optional footer(s)]
```

- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`,
  `chore`. `feat` is for new features, `fix` for bug fixes.
- **No scopes.** Parenthesized scopes after the type (`fix(frontend): ...`) are not
  allowed — write `fix: ...` and let the description name the area.
- **Description**: lowercase, imperative, no trailing period, immediately after `: `
- **Body**: optional, one blank line after the description
- **Footers**: optional, one blank line after the body; tokens use `-` for spaces
  (`Reviewed-by`, `Refs`)
- **Breaking changes**: `!` before the colon and/or a `BREAKING CHANGE: <description>`
  footer. `BREAKING CHANGE` must be uppercase; `BREAKING-CHANGE` is synonymous. With `!`,
  the footer may be omitted.

Examples:

```
feat: add brew method and attempt endpoints
fix: send null instead of empty string for blank roast date
docs: document the two-level cascade
feat!: address attempts by their own id

BREAKING CHANGE: attempts moved from /beans/{id}/methods/{mid}/attempts to /attempts
```
