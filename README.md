# TASA Website

Source code for the UC Berkeley [Taiwanese American Student Association](https://tasa.berkeley.edu)
website, hosted by the [Open Computing Facility](https://ocf.io).

**Stack:** Python 3.12+ / Flask 3 (app factory + blueprints), SQLAlchemy 2 (SQLite), Flask-WTF (CSRF),
Tailwind CSS v4 (compiled locally, committed), Alpine.js (vendored). No Node and no CSS build step on
the server — OCF only runs gunicorn and serves static files.

## Pages

Public: Home `/`, About `/about`, Officers `/officers`, Families `/families`, Testimonials `/testimonials`.
Admin CMS at `/admin` (login at `/login`) manages officers, families, and testimonials.

## Developer setup

1. Clone the repo and create a virtualenv:
   - **Windows:** `py -m venv venv` then `venv\Scripts\pip install -e ".[dev]"`
   - **Linux/macOS:** `make venv`
2. Copy `.env.example` to `.env` and fill it in. Generate the admin password hash with
   `flask hash-password` (the `flask` CLI picks up `.env` automatically).
3. Create the database: `flask init-db`
4. Run the site: `python run.py` (Windows) or `make run` — serves at <http://127.0.0.1:5001>.

### CSS (Tailwind)

`tasa_website/static/css/app.css` is compiled from `input.css` and **committed**, so you only need
this when changing templates or styles:

1. Download the standalone Tailwind CLI (no Node needed) from
   <https://github.com/tailwindlabs/tailwindcss/releases/latest> —
   `tailwindcss-windows-x64.exe` (save as `tailwindcss.exe` in the repo root, it's gitignored) or
   the Linux binary as `tailwindcss`.
2. Build: `.\tailwindcss.exe -i tasa_website/static/css/input.css -o tasa_website/static/css/app.css --minify`
   (add `--watch` while developing). On Linux: `make build-css`.
3. Commit the updated `app.css` together with your template changes.

Design tokens (DM Sans, the light-blue `accent` palette) live in `input.css` under `@theme`.

### Tests

`venv\Scripts\python -m pytest tests/ -q` (or `make test`).

## Site photos

Hand-picked photos for the home and about pages go in `tasa_website/static/images/site/` with these
names (gray placeholders render until a file exists):

- Home gallery: `gallery-1.jpg` … `gallery-6.jpg`
- Home sections: `food.jpg`, `activities.jpg`, `welcome.jpg`, `events.jpg`, `tasa-bear.png`
- About: `about-why-1.jpg`/`-2.jpg`, `about-mission-1.jpg`/`-2.jpg`, `about-families-1.jpg`/`-2.jpg`,
  `about-cabinet-1.jpg`/`-2.jpg`

Officer/family/testimonial photos are uploaded through the admin panel instead and are **not**
tracked in git.

## Migrating data from the old site

The pre-2026 site's data lives only on OCF. One-time runbook:

1. From the OCF server, download the old `tasa_website/tasa_website.db` plus the
   `static/images/officers/` and `static/images/families/` folders.
2. Drop the image folders into the same paths in this repo (stored image URLs keep resolving).
3. `flask init-db` then `flask import-legacy path/to/old_tasa_website.db` — copies officers and
   families, validates position values, and prints a summary. Use `--wipe` to replace existing rows.
4. Re-enter testimonials through the admin panel (they were previously hardcoded HTML).

## Deploying on OCF

```
git pull
make venv          # first time or when dependencies change
flask init-db      # first time only
# restart gunicorn (e.g. systemctl --user restart tasa or OCF's usual mechanism), serving wsgi:app
```

Set the production `.env` on the server (strong `SECRET_KEY`, real `ADMIN_PASSWORD_HASH`,
`FLASK_DEBUG=0`). Never commit `.env`.

## Conventions

1. Prefer `git add -u` plus explicit paths for new files over `git add .` / `-A`.
2. Never track secrets (`.env`, password hashes, API keys) or uploaded member photos.
3. Keep it simple — this site is maintained by a rotating cast of webmasters.
4. Don't edit on the live server, and don't drop tables in the production database.
