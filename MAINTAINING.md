# Maintaining the TASA Website

A practical guide for two audiences: **developers** setting up the codebase, and **webmasters**
updating site content. Also covers deploying to OCF.

---

## Part 1 — Set up the codebase (developers)

### Prerequisites
- Python 3.12+
- Git
- (For CSS changes only) the Tailwind v4 standalone CLI or Node — see "Rebuilding CSS" below.

### Steps
1. Clone and create a virtual environment:

       git clone <repo-url> tasa_website
       cd tasa_website
       py -m venv venv                          # Linux/macOS: python3 -m venv venv

2. Install dependencies:

       venv\Scripts\pip install -e ".[dev]"     # Linux/macOS: make venv

3. Create a `.env` file in the repo root (copy `.env.example`) and fill it in:

       FLASK_APP=tasa_website
       SECRET_KEY=<any long random string>
       ADMIN_USERNAME=<your admin username>
       ADMIN_PASSWORD_HASH=<generate with: venv\Scripts\flask hash-password>
       FLASK_DEBUG=1                             # 1 for local dev, 0 in production

   Generate the password hash and paste the output into `ADMIN_PASSWORD_HASH`:

       venv\Scripts\flask hash-password

4. Create the database tables:

       venv\Scripts\flask init-db

5. Run the site:

       venv\Scripts\python run.py               # http://127.0.0.1:5001

6. Run the tests:

       venv\Scripts\python -m pytest tests/ -q

### Rebuilding CSS
`static/css/app.css` is compiled from `input.css` and **committed**. Only rebuild when you change
templates or `input.css`:

    .\tailwindcss.exe -i tasa_website/static/css/input.css -o tasa_website/static/css/app.css --minify

(or `npx @tailwindcss/cli ...` with a local `node_modules`). Commit `app.css` with your template changes.
The Tailwind binary / `node_modules` are gitignored.

---

## Part 2 — Update the website (webmasters)

### Officers, Families, Testimonials → use the admin panel (no code needed)
1. Go to `/login` and sign in with the admin username/password (from `.env`).
2. Go to `/admin`. Pick Officers, Families, or Testimonials.
3. **Add**: click "Add …", fill the form, upload a photo, save. **Edit / Delete / Preview**: use the
   buttons on each row. Photos are uploaded through the form (no need to touch files directly).
- If a photo is missing, a gray placeholder shows automatically.
- Changes appear on the live site immediately — no redeploy.

### Home & About photos → drop files in a folder
These two pages are static; their images are hand-placed files in
`tasa_website/static/images/site/`. Add a photo with the **exact expected filename** and it appears
(gray placeholder until then). Keep images web-sized (≤ ~2000 px wide, a few hundred KB) so pages load
fast.

### Contact info, links, footer
Edit `tasa_website/templates/_footer.html` (club email, social links, archive links). Confirm the
club/officer emails each semester.

### content.yaml + CLI (advanced / bulk)
`content.yaml` is a seed/sync source, not the live site. Use it only for bulk operations via the CLI:
- `flask seed-testimonials` — populate the testimonials table from `content.yaml` (first-time seeding).
- `flask sync-officers` — refresh existing officers' title/major/year/quote/bio from `content.yaml`
  (matched by name; does not add or delete rows).

Everyday edits should go through `/admin` instead.

---

## Part 3 — Deploy to OCF

The site runs as `gunicorn wsgi:app`. The database and `.env` live only on the server (both gitignored),
so a code update is a `git pull` + restart, but a **first-time** deploy needs setup.

### First-time deploy
1. On the server, pull the code and build the venv:

       git pull
       make venv

2. **Create `.env` on the server** (it is NOT in git). Use a **freshly generated** `SECRET_KEY` and a
   **new** admin password (`flask hash-password`); set `FLASK_DEBUG=0`.
3. **Back up** any existing database first, then create/seed the database (in order):

       flask init-db
       flask import-legacy <path-to-old.db>     # officers + families from the previous DB
       flask seed-testimonials
       flask sync-officers

   Never run the destructive `--drop` / `--wipe` flags against live data.
4. **Ensure photo files exist on the server.** Officer/family/testimonial photos and any banner images
   referenced from `static/images/officers|families|testimonials/` are gitignored, so they arrive via the
   admin uploads or must be copied over — otherwise they 404 to gray placeholders.
5. Point the `tasa.studentorg.berkeley.edu` virtual host at the gunicorn app and restart gunicorn.

### Routine update (code / template changes)
    git pull
    make venv        # only if dependencies changed
    # restart gunicorn (e.g. systemctl --user restart tasa, or OCF's mechanism)

The database is preserved across `git pull` (it lives in the gitignored `instance/` folder). The archive
links `~tasa/old_site2/` and `~tasa/old_site/` are static and unaffected by the app.

---

## Conventions
- Never commit `.env`, the database (`*.db`), or uploaded member photos (all gitignored).
- `git add -u` + explicit new paths; never `git add .` / `-A`.
- Rebuild and commit `app.css` whenever you change templates/styles.
- Keep LICENSE untouched.
