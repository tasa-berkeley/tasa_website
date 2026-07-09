# TASA Website

Source code for the UC Berkeley Taiwanese American Student Association (TASA) website,
hosted on the Open Computing Facility (OCF).

**Stack:** Python 3.12+ / Flask 3 (app factory) · SQLite + SQLAlchemy · Flask-WTF · Alpine.js
(vendored) · Tailwind CSS v4 (compiled locally, `app.css` committed). Runs under gunicorn on OCF.

## How the site works

- **Home** (`/`) and **About** (`/about`) are static templates. Their photos are hand-placed files in
  `tasa_website/static/images/site/` — drop in a correctly named image and it appears (a gray
  placeholder shows until then).
- **Officers** (`/officers`), **Families** (`/families`), and **Testimonials** (`/testimonials`) live in
  a **database** and are edited through the **admin panel** at `/admin` (login required). No code edits
  or redeploys are needed to change this content.
- **Join** (`/join`) and **Donate** (`/donate`) are static informational pages.
- `content.yaml` is a **seed file**, not the live source. The Flask CLI uses it to first populate the
  testimonials table and to bulk-refresh officer titles/majors/years. Day-to-day content edits happen in
  `/admin`, not in this file.

## Admin panel

`/admin` (behind `/login`) lets a webmaster add / edit / delete officers, families, and testimonials,
including photo uploads. Credentials come from `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` in a local
`.env` file — see **[MAINTAINING.md](MAINTAINING.md)**.

## Project layout

- `tasa_website/__init__.py` — `create_app()`; registers the `public`, `auth`, and `admin` blueprints.
- `tasa_website/models.py` — SQLAlchemy models: `Officer`, `Family`, `Testimonial`.
- `tasa_website/views/` — `public.py` (site pages), `auth.py` (login/logout), `admin.py` (CRUD dashboard).
- `tasa_website/forms.py` — WTForms (login + officer/family/testimonial forms with photo upload).
- `tasa_website/helpers.py` — image save/delete pipeline, officer grouping, position titles.
- `tasa_website/cli.py` — Flask CLI: `init-db`, `import-legacy`, `seed-testimonials`, `sync-officers`,
  `hash-password`.
- `tasa_website/content.py` — loads `content.yaml`; provides the home/about `site_image()` helper.
- `tasa_website/templates/` — `base.html` (+ `_navbar`/`_footer`/`_macros`), the public pages,
  `admin/*`, and `auth/login.html`.
- `tasa_website/static/css/` — edit `input.css` → recompile `app.css` (committed) → never hand-edit
  `app.css`.

## Quick start (developers)

    py -m venv venv
    venv\Scripts\pip install -e ".[dev]"      # Linux/macOS: make venv
    # create .env (see MAINTAINING.md), then:
    venv\Scripts\flask init-db                # create the database tables
    venv\Scripts\python run.py                # http://127.0.0.1:5001

Tests: `venv\Scripts\python -m pytest tests/ -q`

Full setup, how to update site content, and OCF deployment live in **[MAINTAINING.md](MAINTAINING.md)**.

## Conventions

- Tailwind: edit `input.css`, recompile `app.css`, commit the compiled file. No Node on the server.
- `git add -u` + explicit new paths; never `git add .` / `-A`. Never commit `.env`, the database, or
  uploaded photos.
- Keep LICENSE untouched.
