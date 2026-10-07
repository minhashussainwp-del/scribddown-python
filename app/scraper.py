"""Scribd document -> PDF scraper (research module).

Technique (verified against live scribd.com, Oct 2026):
  1. GET the document page with Chrome TLS impersonation (plain ``requests``
     is served Fastly's "Client Challenge" bot page; ``curl_cffi`` with
     ``impersonate="chrome131"`` passes through).
  2. The page HTML contains one ``contentUrl: "https://....jsonp"`` entry per
     document page (inside the script block that also has
     ``docManager.addPage``). All pages are listed up front, even for long
     documents (verified: 48/48).
  3. Each JSONP file is ``window.page<N>_callback(["<div ...>...</div>"])`` --
     the single JSON string argument is the page's HTML. It always contains
     ``<img class="absimg" orig="http://html.scribd.com/<asset>/images/<n>-<hash>.<jpg|png>"/>``
     with the full-page rendered image (JPG for scanned docs, PNG for
     text-layout docs).
  4. Download every page image (threads), normalise to JPEG/PNG for img2pdf
     (WebP -> PNG via Pillow when encountered), then ``img2pdf.convert``.

Only pip-installable, pure-Python dependencies: curl_cffi, beautifulsoup4,
img2pdf, Pillow. No browser, no system packages.
"""

from __future__ import annotations

import html as html_module
import json
import os
import re
import shutil
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import img2pdf
from bs4 import BeautifulSoup
from curl_cffi import requests as creq
from PIL import Image

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ScribdError(Exception):
    """Base class for all scraper errors."""


class ScribdNotFoundError(ScribdError):
    """The document URL does not exist (HTTP 404)."""


class ScribdAccessDeniedError(ScribdError):
    """Document is private / requires login; no public pages available."""


class ScribdChallengeError(ScribdError):
    """Scribd served its bot-protection challenge page; automated fetch blocked."""


class ScribdStructureError(ScribdError):
    """Page fetched but no page manifest found; Scribd changed its layout."""


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_IMPERSONATE = "chrome131"
_TIMEOUT = 30  # seconds; every request is bounded so we never hang
_WORKERS = 5  # concurrent page downloads
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.scribd.com/",
}

_DOC_ID_RE = re.compile(r"scribd\.com/(?:document|doc|embeds)/(\d+)", re.IGNORECASE)
_CONTENT_URL_RE = re.compile(r'contentUrl:\s*"(https://[^"]+\.jsonp)"')
_JSONP_RE = re.compile(r"window\.\w+_callback\(\s*(\[.*\])\s*\)\s*;?\s*$", re.DOTALL)

_thread_state = threading.local()


def _session() -> "creq.Session":
    sess = getattr(_thread_state, "sess", None)
    if sess is None:
        sess = creq.Session(impersonate=_IMPERSONATE, headers=_HEADERS)
        _thread_state.sess = sess
    return sess


def _clean_title(raw: str) -> str:
    text = html_module.unescape(raw or "").strip()
    # "<title>" looks like "What Is A Document | PDF | Information | Document"
    if " | " in text:
        text = text.split(" | ")[0].strip()
    return text or "scribd-document"


def _extract_doc_id(url: str) -> str:
    m = _DOC_ID_RE.search(url or "")
    if not m:
        raise ScribdError(
            f"Not a Scribd document URL (expected scribd.com/document/<id>/...): {url!r}"
        )
    return m.group(1)


def _fetch_document_page(url: str) -> tuple[str, str]:
    """Return (html, title). Raises a specific ScribdError on failure."""
    doc_id = _extract_doc_id(url)
    try:
        resp = _session().get(url, timeout=_TIMEOUT, allow_redirects=True)
    except Exception as exc:  # network-level failure (DNS, connect timeout, ...)
        raise ScribdError(f"Could not reach scribd.com: {exc}") from exc

    body = resp.text or ""

    if "<title>Client Challenge</title>" in body or "_fs-ch-" in body and "Client Challenge" in body:
        raise ScribdChallengeError(
            "Scribd served its bot-protection challenge page. "
            "Automated download is blocked from this network right now."
        )
    if resp.status_code == 404 or "<title>Page not found | Scribd</title>" in body:
        raise ScribdNotFoundError(
            f"Scribd document not found (HTTP 404): {url}"
        )

    title_m = re.search(r"<title>(.*?)</title>", body, re.DOTALL | re.IGNORECASE)
    title = _clean_title(title_m.group(1) if title_m else "")

    content_urls = _CONTENT_URL_RE.findall(body)
    if not content_urls:
        lowered = body.lower()
        login_markers = (
            "log in to continue",
            "sign up to",
            "log in to download",
            "this document is private",
            '"isprivate":true',
            "password protected",
        )
        if any(mk in lowered for mk in login_markers):
            raise ScribdAccessDeniedError(
                f"Document {doc_id} requires login or is private; "
                "no public pages are available to download."
            )
        raise ScribdStructureError(
            f"No page manifest (contentUrl entries) found for document {doc_id}; "
            "Scribd may have changed its page layout."
        )
    return body, title, content_urls


def _page_image_url(jsonp_url: str) -> str:
    """Fetch one JSONP page manifest and return its full-page image URL."""
    resp = _session().get(jsonp_url, timeout=_TIMEOUT)
    if resp.status_code != 200:
        raise ScribdError(f"Page manifest request failed (HTTP {resp.status_code}): {jsonp_url}")
    text = resp.text.strip()
    m = _JSONP_RE.match(text)
    if not m:
        raise ScribdError(f"Unexpected page manifest format: {jsonp_url}")
    try:
        page_html = json.loads(m.group(1))[0]
    except (json.JSONDecodeError, IndexError, TypeError) as exc:
        raise ScribdError(f"Could not parse page manifest JSON: {jsonp_url}") from exc

    soup = BeautifulSoup(page_html, "html.parser")
    img = (
        soup.select_one("img.absimg[orig]")
        or soup.select_one("img[orig]")
        or soup.select_one("img.absimg")
        or soup.select_one("img")
    )
    if img is None:
        raise ScribdError(f"No page image found in manifest: {jsonp_url}")
    src = (img.get("orig") or img.get("src") or "").strip()
    if not src:
        raise ScribdError(f"Page image has no URL in manifest: {jsonp_url}")
    return src


def _download_image(image_url: str, dest_path: str) -> None:
    """Download one page image; convert to PNG when img2pdf can't take it.

    img2pdf accepts JPEG and PNG. Scribd serves JPG/PNG, but WebP shows up
    for some assets, so anything else is converted to PNG via Pillow.
    """
    last_exc: Exception | None = None
    for attempt in (1, 2):
        try:
            resp = _session().get(image_url, timeout=60)
            if resp.status_code != 200:
                raise ScribdError(
                    f"Page image request failed (HTTP {resp.status_code}): {image_url}"
                )
            data = resp.content
            if not data:
                raise ScribdError(f"Empty page image response: {image_url}")
            with open(dest_path, "wb") as fh:
                fh.write(data)
            try:
                with Image.open(dest_path) as im:
                    fmt = (im.format or "").upper()
                if fmt not in ("JPEG", "JPG", "PNG"):
                    # e.g. WEBP -> convert losslessly to PNG for img2pdf
                    with Image.open(dest_path) as im:
                        im.save(dest_path, "PNG")
            except ScribdError:
                raise
            except Exception as exc:
                raise ScribdError(f"Downloaded file is not a valid image: {image_url}") from exc
            return
        except ScribdError:
            raise
        except Exception as exc:  # transient network error -> one retry
            last_exc = exc
    raise ScribdError(f"Failed to download page image after retry: {image_url} ({last_exc})")


def _fetch_page(index: int, jsonp_url: str, tmpdir: str) -> str:
    """Download page ``index`` (0-based); return the local image path."""
    image_url = _page_image_url(jsonp_url)
    # keep original extension when sane so img2pdf sees a proper file
    ext = ".jpg" if ".jpg" in image_url.lower() or ".jpeg" in image_url.lower() else ".png"
    dest = os.path.join(tmpdir, f"page-{index:04d}{ext}")
    _download_image(image_url, dest)
    return dest


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scrape_scribd_to_pdf(url: str, output_path: str) -> dict:
    """Download a public Scribd document and save it as a PDF.

    Args:
        url: Any scribd.com document URL
             (``/document/<id>/...``, ``/doc/<id>/...`` or ``/embeds/<id>/content``).
        output_path: Where to write the resulting PDF file.

    Returns:
        ``{"pages": <int>, "title": <str>}``.

    Raises:
        ScribdNotFoundError: document does not exist (HTTP 404).
        ScribdAccessDeniedError: document is private / needs login.
        ScribdChallengeError: Scribd's bot protection blocked the request.
        ScribdStructureError: page layout changed and no manifest was found.
        ScribdError: any other failure (network, bad image, PDF build, ...).
    """
    _extract_doc_id(url)  # validate early
    _, title, content_urls = _fetch_document_page(url)
    total = len(content_urls)

    parent = os.path.dirname(os.path.abspath(output_path))
    if parent:
        os.makedirs(parent, exist_ok=True)

    tmpdir = tempfile.mkdtemp(prefix="scribd_pages_")
    try:
        ordered: list[str | None] = [None] * total
        failures: dict[int, str] = {}
        with ThreadPoolExecutor(max_workers=min(_WORKERS, total)) as pool:
            future_to_index = {
                pool.submit(_fetch_page, i, jurl, tmpdir): i
                for i, jurl in enumerate(content_urls)
            }
            for future in as_completed(future_to_index):
                i = future_to_index[future]
                try:
                    ordered[i] = future.result()
                except Exception as exc:  # noqa: BLE001 - reported below
                    failures[i] = str(exc)
        if failures:
            bad = ", ".join(f"page {i + 1}: {msg}" for i, msg in sorted(failures.items()))
            raise ScribdError(
                f"Failed to download {len(failures)}/{total} page(s): {bad}"
            )
        image_paths = [p for p in ordered if p is not None]
        pdf_bytes = img2pdf.convert(image_paths)
        with open(output_path, "wb") as fh:
            fh.write(pdf_bytes)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    return {"pages": total, "title": title}
