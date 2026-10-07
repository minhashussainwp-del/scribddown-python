# Scribd → PDF scraper — research notes

**Status: WORKING.** Tested against live scribd.com on 2026-10-07.
Module: `scraper.py` in this directory. Public API: `scrape_scribd_to_pdf(url: str, output_path: str) -> dict`
returns `{"pages": int, "title": str}`, raises `ScribdError` subclasses on failure.

## The exact technique

1. **Fetch the document page with Chrome TLS impersonation.**
   Plain `requests`/`urllib3` is served Fastly's *Client Challenge* bot page
   (3 KB, `<title>Client Challenge</title>`, JS proof-of-work at `/_fs-ch-...`).
   `curl_cffi` with `impersonate="chrome131"` passes straight through with HTTP 200
   and the full ~1.1 MB document HTML. This is the single most important finding:
   **no headless browser needed, but `requests` alone does NOT work.**
2. **Page manifest lives in the document HTML.** One entry per page, inside the
   `<script>` block that also contains `docManager.addPage`:
   `contentUrl: "https://html.scribdassets.com/<assetPrefix>/pages/<n>-<pagehash>.jsonp"`.
   Regex: `contentUrl:\s*"(https://[^"]+\.jsonp)"`. **All** pages are listed up
   front — a 48-page doc had all 48 URLs in the initial HTML (no pagination,
   no scrolling needed).
3. **Each JSONP is `window.page<N>_callback(["<div …>…</div>"])`.** The single
   JSON-string argument *is* valid JSON — parse with `json.loads`, no manual
   unescaping. The page HTML always contains
   `<img class="absimg" orig="http://html.scribd.com/<asset>/images/<n>-<hash>.<jpg|png>"/>`
   — the full-page image.
4. **Two page types:**
   - *Scanned/image docs* → `orig` is an opaque **JPEG** (e.g. 835×956, 904×1199).
     Download as-is → straight into the PDF.
   - *Text-layout docs* → `orig` is a tiny **palette PNG with a tRNS transparency
     chunk** — a background *stencil*, not the content (looks blank; the real
     content is the `.text_layer` divs in the same JSONP). Detection: PNG +
     mode `P` + `transparency` in info. For these, extract text lines in DOM
     order (`span.a` line spans, nested fragments joined) and render a clean
     text page with Pillow at the `.newpage` div's dimensions.
5. **Assemble with `img2pdf`.** All page images are flattened to RGB on white
   first (raw alpha-channel PNGs otherwise produce *blank PDF pages* via a
   broken img2pdf soft-mask — verified failure mode). JPEGs stay JPEG;
   everything else → PNG. WebP (seen on `imgv2-*-f.scribdassets.com` poster
   URLs) would be converted via Pillow the same way.

## pip packages (all pure-Python wheels, no system deps)

```
curl_cffi      # Chrome TLS/JA3 impersonation — REQUIRED, requests alone is bot-blocked
beautifulsoup4 # parse JSONP page HTML
img2pdf        # lossless image → PDF assembly (JPEG/PNG only)
Pillow         # flatten alpha/transparency, WebP→PNG, text-page rendering
```

`requirements.txt` for the Flask app needs exactly these four.

## Test results (all run for real, PDFs visually verified page-by-page)

| # | URL | Type | Pages | PDF | Time |
|---|-----|------|-------|-----|------|
| 1 | https://www.scribd.com/document/701972896/What-is-a-document | text-layout (PNG stencils → rendered text pages) | 2 | 127 KB, valid, readable | ~3 s |
| 2 | https://www.scribd.com/document/478637377/30505-fill-in-pdf | scanned (full-page JPEGs) | 2 | 181 KB, valid, renders the form | ~3 s |
| 3 | https://www.scribd.com/document/450009743/10-Day-Detox-Ebook-Download | 48-page ebook (full-page JPEGs) | 48 | 8.2 MB, 48/48 pages, spot-checked p.7 renders in full color | ~12 s |

Also verified: `/embeds/<id>/content` and legacy `/doc/<id>/…` URL inputs
(auto-canonicalised to `/document/<id>/`), HTTP 404 → `ScribdNotFoundError`,
non-Scribd URL → `ScribdError`, 5 download threads, every request has a
timeout (nothing hangs), temp page images cleaned up after each run.

## Known limitations

- **Bot protection can still bite.** If Scribd escalates to an unsolvable
  challenge for the host IP, the scraper raises `ScribdChallengeError` with a
  clear message instead of hanging. (Observed: `requests` always challenged;
  `curl_cffi` chrome131 passed from our network on 2026-10-07.)
- **Login-walled / private docs** raise `ScribdAccessDeniedError` (detected via
  missing page manifest + login markers). No real login-walled `/document/`
  URL was available to test against — the marker list may need extending.
- **Text pages are re-rendered, not pixel-faithful.** Text-layout pages become
  clean flowing-text pages (correct reading order, auto-fit font) — they do
  *not* reproduce Scribd's exact typography/layout. Scanned/image pages are
  pixel-identical.
- **Page images are ~900 px wide** (Scribd's web resolution), not print
  resolution. Fine for screen reading.
- **Rate limits untested at scale.** 48 pages ≈ 100 requests in ~12 s was fine;
  hammering many documents back-to-back may trigger throttling — the Flask app
  should queue/pace jobs.
- **Fragile to Scribd redesigns.** If `contentUrl`/`absimg[orig]` disappear,
  the scraper raises `ScribdStructureError` naming the layout change.
- **Text rendering font** prefers system DejaVu/Liberation/Noto, else Pillow's
  built-in scalable font — works with zero system fonts installed.

## For the Flask app builder

- `from research.scraper import scrape_scribd_to_pdf, ScribdError` (plus the
  specific subclasses for user-facing error messages).
- Catch `ScribdError` → show `str(e)` to the user; all messages are written
  for end users.
- The function is thread-safe (thread-local HTTP sessions) and blocks for the
  whole download — run it in a background worker/thread, not the request
  handler, for multi-page docs.
- A test venv used for this research lives at `research/venv/` (recreate with
  `pip install curl_cffi beautifulsoup4 img2pdf Pillow`).
