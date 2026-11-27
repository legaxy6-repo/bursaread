# Daily Desk website

Plain HTML pages built from the daily reads, served at https://dailydesk.win.

- `site/data/` holds the reads exported from the Daily Desk app (editions, reads, closes).
- `python3 site/build.py` writes the site to `docs/` (no dependencies).
- `site/config.json` sets the domain and, later, the newsletter form's address.

Hosting: Cloudflare Pages, connected to this repo, with no build command and `docs` as the output folder.

Live check (home page and each area's latest page) calls Alpha Vantage straight from the browser. The API key is typed into the page once and kept in that browser's local storage; it is never in the code, the repo or the built pages.
