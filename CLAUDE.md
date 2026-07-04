# TASA Website — project notes

Rebuilt July 2026: Flask 3 app factory + blueprints, SQLAlchemy 2 (SQLite), Flask-WTF/CSRF,
Tailwind v4 (standalone CLI, compiled `app.css` committed), Alpine.js vendored. Hosted on OCF
(gunicorn + static files only — no Node on the server). Design: black & white with light-blue
`accent-*` tokens, DM Sans (self-hosted), per wireframes in `documents/`.

## Layout

- `tasa_website/__init__.py` — `create_app()`; context processor exposes `position_title`,
  `static_image`, `site_image`, `current_year` to all templates.
- `views/public.py` — the ONLY public pages: `/`, `/about`, `/officers`, `/families`, `/testimonials`.
- `views/admin.py` — `/admin` CRUD for officers, families, testimonials (form pages, no JS).
- `views/auth.py` — `/login`, `/logout`, `login_required` (302 → login, not 401).
- `models.py` — `Officer` (position = int index into `helpers.POSITIONS`), `Family`, `Testimonial`.
- `helpers.py` — `POSITIONS` (order is load-bearing, never reorder; append only),
  `officer_sections()` (Exec = indices 0–2 only; Senior Advisors; `*Intern` → Interns; rest →
  Officers), image pipeline (`save_image` resizes to 1024px JPEG, stores forward-slash URLs).
- `cli.py` — `flask init-db | import-legacy <old.db> | hash-password`.
- Config via `.env` (see `.env.example`); DB defaults to `instance/tasa_website.db`.
- Templates: `base.html` (+ `_navbar`, `_footer`, `_macros`), page templates, `admin/*`, `auth/login.html`.
- CSS: edit `static/css/input.css` → compile with the standalone Tailwind CLI → commit `app.css`
  (see README). Never hand-edit `app.css`.

## Commands (Windows dev)

- Run: `venv\Scripts\python run.py` (port 5001)
- Tests: `venv\Scripts\python -m pytest tests/ -q`
- CSS watch: `.\tailwindcss.exe -i tasa_website/static/css/input.css -o tasa_website/static/css/app.css --watch`

## Removed in the 2026 rebuild (do not resurrect)

Events page + Facebook importer, Join/FAQ + files, Donate, Scrapbook (Google Drive), Contact page
(contact info lives in `_footer.html`), the entire check-in/attendance/leaderboard system, jQuery,
Bootstrap, skrollr.

## Open items

- Real photos needed in `static/images/site/` (names listed in README) — placeholders render meanwhile.
- Production data migration from OCF (`flask import-legacy`, README runbook) not yet run.
- Footer president/webmaster emails carried over from the old site — confirm each semester.
- Home "View events »" links to the public Google Calendar; swap to Instagram if preferred (index.html).
- Animations/polish deliberately deferred — keep the framework clean.

## Conventions

- `git add -u` + explicit new paths; never `git add .`/`-A`. Never track secrets or uploads.
- Don't edit on the live server; don't drop tables in the production DB.
- Keep LICENSE untouched.
