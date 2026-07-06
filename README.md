# TASA Website

Source code for the UC Berkeley [Taiwanese American Student Association](https://tasa.berkeley.edu)
website, hosted by the [Open Computing Facility](https://ocf.io).

**Stack:** Python 3.12+ / Flask 3 (app factory), Tailwind CSS v4 (compiled locally, committed),
Alpine.js (vendored). Content lives in a YAML file — **no database, no admin panel, no login.** No
Node and no CSS build step on the server — OCF only runs gunicorn and serves static files.

## Pages

Home `/`, About `/about`, Officers `/officers`, Families `/families`, Testimonials `/testimonials`.

## Updating site content

All officers, families, and testimonials live in **`tasa_website/content.yaml`** — edit that file to
change the site. No database or login involved.

- **Officers** are grouped into `executives`, `officers`, `interns`, and `senior_advisors`. The order
  you list people in is the order they appear on the page. To add someone, copy an existing entry and
  change the fields; to remove someone, delete their entry.
- **Photos** are just filenames. Put the image in `static/images/officers/`
  (or `/families/`, `/testimonials/`) and set `photo:` to the filename. If a photo is missing, a gray
  placeholder shows automatically.
- **Families** and **testimonials** are simple lists at the bottom of the file — same idea.

Example officer entry:

```yaml
officers:
  executives:
    - name: Jackson Lu
      position: President
      major: Economics
      year: Sophomore
      photo: jackson.jpg      # -> static/images/officers/jackson.jpg
      quote: "your shot quote"
      bio: A sentence or two about them.
```

Changes are picked up on the next page load (locally, just refresh).

## Developer setup

1. Clone the repo and create a virtualenv:
   - **Windows:** `py -m venv venv` then `venv\Scripts\pip install -e ".[dev]"`
   - **Linux/macOS:** `make venv`
2. Run the site: `python run.py` (Windows) or `make run` — serves at <http://127.0.0.1:5001>.

### CSS (Tailwind)

`tasa_website/static/css/app.css` is compiled from `input.css` and **committed**, so you only need
this when changing templates or styles:

1. Get the Tailwind v4 CLI, either the standalone binary from
   <https://github.com/tailwindlabs/tailwindcss/releases/latest> (`tailwindcss.exe` in the repo root,
   gitignored), or `npm install tailwindcss @tailwindcss/cli` (creates a gitignored `node_modules`).
2. Build: `.\tailwindcss.exe -i tasa_website/static/css/input.css -o tasa_website/static/css/app.css --minify`
   or `npx @tailwindcss/cli -i tasa_website/static/css/input.css -o tasa_website/static/css/app.css --minify`
   (add `--watch` while developing).
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

Officer/family/testimonial photos live in `static/images/<officers|families|testimonials>/` and are
**not** tracked in git (they're large and change often); `content.yaml` references them by filename.

## Deploying on OCF

```
git pull
make venv          # first time or when dependencies change
# restart gunicorn (e.g. systemctl --user restart tasa or OCF's usual mechanism), serving wsgi:app
```

## Conventions

1. Prefer `git add -u` plus explicit paths for new files over `git add .` / `-A`.
2. Never track secrets or uploaded member photos.
3. Keep it simple — this site is maintained by a rotating cast of webmasters.
4. Don't edit on the live server.
