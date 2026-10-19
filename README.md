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

One-time, from a fresh clone, create `.env` in the repo root (it's gitignored). Avoid
`@ : / ? #` in `MYSQL_PASSWORD`, since it goes into a URL:

```
MYSQL_PASSWORD=pick-a-password
MYSQL_ROOT_PASSWORD=pick-another-one
```

Then:

```bash
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
