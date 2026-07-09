# TASA Website — project notes

Flask 3 app factory, Tailwind v4 (standalone CLI, compiled `app.css` committed), Alpine.js vendored.
SQLite + SQLAlchemy database, an admin panel, and a single-admin login. Hosted on OCF (gunicorn +
static files only — no Node on the server). Design: black & white with light-blue `accent-*` tokens,
DM Sans (self-hosted), per wireframes in `documents/`.

See **README.md** for the overview and **MAINTAINING.md** for setup / content-editing / deploy.

## How content works

- **Officers / Families / Testimonials** are stored in the **database** (`models.py`) and edited via the
  **admin panel** at `/admin` (login required). These pages read the DB — not `content.yaml`.
- **Home / About** are static templates; their photos are hand-placed files in
  `static/images/site/`, resolved by `content.site_image()`.
- **Join / Donate** are static informational pages.
- `content.yaml` is a **seed/sync file**, not the live source: `cli.py` uses it for `seed-testimonials`
  and `sync-officers`. It is not read at request time.

## Layout

- `tasa_website/__init__.py` — `create_app()`; registers the `public`, `auth`, and `admin` blueprints;
  context processor exposes `position_title`, `static_image`, `photo_url`, `site_image`, `current_year`.
- `tasa_website/models.py` — SQLAlchemy models `Officer`, `Family`, `Testimonial`. `extensions.py` holds
  the shared `db` and `csrf` objects.
- `tasa_website/views/` — `public.py` (`/`, `/about`, `/officers`, `/families`, `/testimonials`, `/join`,
  `/donate`), `auth.py` (`/login`, `/logout`), `admin.py` (`/admin` CRUD; every route `login_required`).
- `tasa_website/forms.py` — WTForms; `helpers.py` — image save/delete pipeline (Pillow re-encode, random
  filename), officer grouping (`officer_sections`), position titles.
- `tasa_website/cli.py` — Flask CLI: `init-db`, `import-legacy`, `seed-testimonials`, `sync-officers`,
  `hash-password`.
- `tasa_website/content.py` — loads `content.yaml`; provides `testimonials()` (CLI), `site_image()` /
  `photo_url()` (home/about).
- `config.py` — `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, upload folders, `database_uri()`
  (all from env / `.env`).
- Templates: `base.html` (+ `_navbar`, `_footer`, `_macros`), the public pages, `admin/*`, and
  `auth/login.html`. Officers/families use Alpine.js hover-lift cards that open an overlay modal.
- CSS: edit `static/css/input.css` → recompile `app.css` → commit it. Never hand-edit `app.css`.

## Commands (Windows dev)

- Run: `venv\Scripts\python run.py` (port 5001)
- Tests: `venv\Scripts\python -m pytest tests/ -q`
- Create DB: `venv\Scripts\flask init-db`
- Rebuild CSS: the standalone `tailwindcss` CLI, or
  `npx @tailwindcss/cli -i tasa_website/static/css/input.css -o tasa_website/static/css/app.css --minify`
  (needs `tailwindcss` + `@tailwindcss/cli` in a local `node_modules`; both gitignored).

## Editing content

Officers/families/testimonials → `/admin` (not `content.yaml`). Home/about photos → drop correctly named
files in `static/images/site/`. Full webmaster + deploy steps live in **MAINTAINING.md**.

## Open items

- Some `static/images/site/` photos (home/about) may still be gray placeholders.
- Footer club/officer emails carried over from the old site — confirm each semester.
- `Scrapbook` is a nav dropdown placeholder ("Coming soon!") with no route yet.
- Home "View events »" links to the public Google Calendar; swap to Instagram if preferred (index.html).

## Conventions

- `git add -u` + explicit new paths; never `git add .`/`-A`. Never track secrets, the DB, or uploaded photos.
- Keep LICENSE untouched.
