# ScribdDown (Python)

Scribd PDF downloader with a full CMS — built in Python (Flask) for hosting on Botkeep.

**How it works:** paste a public Scribd document URL → the app fetches the public pages, builds a PDF in temporary memory, and streams it straight to your browser as a download. **No file is ever saved on the server.**

## Features

- **Scribd downloader** (`POST /api/download`) — validates scribd.com URLs, scrapes public documents, streams PDF back with `Content-Disposition: attachment`
- **Blog** — posts with categories, tags, featured images, drafts, SEO meta, 6 languages
- **Pages** — static pages with raw HTML content blocks
- **Shortcodes** — `[scribd_downloader]`, `[contact_form]`, `[latest_posts]` in page/post content
- **Permalinks** — admin-configurable URL patterns
- **SEO** — global meta templates + per-post/page overrides, sitemap.xml, robots.txt, canonicals
- **Multi-language** — en, ur, hi, es, fr, de via `/<lang>/` URL prefix
- **Homepage selection** — admin can set any page as the homepage
- **Contact form** — honeypot anti-spam, saves to DB, shows in admin inbox
- **Admin panel** (`/admin`) — session login (bcrypt), dashboard, posts/pages/categories/menus CRUD, settings, inbox

## Local development

```bash
cp .env.example .env
python -m venv .venv && .venv/bin/pip install -r requirements.txt
# set ADMIN_PASSWORD_HASH: python -c "import bcrypt; print(bcrypt.hashpw(b'YOURPASS', bcrypt.gensalt()).decode())"
.venv/bin/python main.py
# → http://localhost:8000/en/
```

## Deploy on Botkeep

1. Create a **Python** application, import this repo (branch `main`)
2. Create a **PostgreSQL** database
3. Environment variables:
   - `DATABASE_URL` — Postgres connection string
   - `ADMIN_EMAIL` — admin login email
   - `ADMIN_PASSWORD_HASH` — bcrypt hash of admin password
   - `SECRET_KEY` — long random string
   - `APP_URL` — public app URL (for canonicals/sitemap)
4. Start command: `python main.py` (reads `PORT`, binds `0.0.0.0`)

No file storage needed — PDFs stream directly to visitors' browsers.
Database tables + seed content (3 blog posts, pages, menus) are created automatically on first start.

## Stack

Flask · SQLAlchemy · Jinja2 · Gunicorn · PostgreSQL (SQLite for local dev) · curl_cffi · img2pdf
