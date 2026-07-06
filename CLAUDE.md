# TASA Website — project notes

Flask 3 app factory, Tailwind v4 (standalone CLI, compiled `app.css` committed), Alpine.js vendored.
Hosted on OCF (gunicorn + static files only — no Node on the server). Design: black & white with
light-blue `accent-*` tokens, DM Sans (self-hosted), per wireframes in `documents/`.

**Content is code, not a database.** All officer/family/testimonial content lives in
`tasa_website/content.yaml`. A webmaster updates the site by editing that file (and dropping photos
in `static/images/`) — there is no database, no admin panel, and no login.

## Layout

- `tasa_website/content.yaml` — the single source of truth for site content. `officers` is grouped
  into `executives` / `officers` / `interns` / `senior_advisors` (order within each list is the
  display order); `families` and `testimonials` are flat lists. Photo fields are **filenames** inside
  `static/images/<officers|families|testimonials>/`.
- `tasa_website/content.py` — loads/caches `content.yaml` (re-reads on file change); exposes
  `officer_sections()` (adds a page-unique `id` per officer; the `Interns` section always renders so
  the page can show a recruitment placeholder), `families()`, `testimonials()`, `photo_url()`,
  `site_image()`.
- `tasa_website/__init__.py` — `create_app()`; context processor exposes `photo_url`, `site_image`,
  `current_year` to all templates.
- `views/public.py` — the ONLY blueprint: `/`, `/about`, `/officers`, `/families`, `/testimonials`.
- `config.py` — minimal (`SECRET_KEY` only, unused unless flashing/sessions are added).
- Templates: `base.html` (+ `_navbar`, `_footer`, `_macros`), and the five page templates. The
  officers/families pages use Alpine.js for hover-lift cards that open an overlay modal (bio/photo).
- CSS: edit `static/css/input.css` → recompile `app.css` → commit it. Never hand-edit `app.css`.

## Commands (Windows dev)

- Run: `venv\Scripts\python run.py` (port 5001)
- Tests: `venv\Scripts\python -m pytest tests/ -q`
- Rebuild CSS (after editing templates or `input.css`): the standalone `tailwindcss` CLI, or
  `npx @tailwindcss/cli -i tasa_website/static/css/input.css -o tasa_website/static/css/app.css --minify`
  (needs `tailwindcss` + `@tailwindcss/cli` in a local `node_modules`; both are gitignored).

## Editing content (for webmasters)

- Add/edit/remove a person → edit `tasa_website/content.yaml`. To add someone, copy an existing entry
  and change the fields; put them under the right section (their position in the list = order on the
  page). Add their photo to `static/images/officers/` and set `photo:` to the filename.
- No photo yet → a gray placeholder renders automatically.
- Families/testimonials work the same way in their lists.

## Removed / not present (do not resurrect)

Database + SQLAlchemy, the `/admin` panel, `/login` auth, WTForms, the image-upload pipeline, the
`flask` CLI (init-db/import-legacy/hash-password). Also long gone from the old site: Events + Facebook
importer, Donate, Scrapbook, Contact page (contact info lives in `_footer.html`),
the check-in/attendance/leaderboard system, jQuery, Bootstrap, skrollr.

(The `/join` page — a static FAQ accordion + useful links, no `files` DB — was re-added; it mirrors
the old join page's copy minus the membership-prices question.)

## Open items

- Some `static/images/site/` photos (home/about) are still gray placeholders — names listed in README.
- Footer president/webmaster emails carried over from the old site — confirm each semester.
- Home "View events »" links to the public Google Calendar; swap to Instagram if preferred (index.html).

## Conventions

- `git add -u` + explicit new paths; never `git add .`/`-A`. Never track secrets.
- Keep LICENSE untouched.
