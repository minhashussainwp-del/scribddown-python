"""Public API: POST /api/download -> streams a PDF back."""
import os
import shutil
import tempfile
from urllib.parse import urlparse

from flask import Blueprint, request, jsonify, Response, stream_with_context

bp = Blueprint("api", __name__, url_prefix="/api")


def is_valid_scribd_url(u: str) -> bool:
    try:
        p = urlparse(u.strip())
        if p.scheme not in ("http", "https"):
            return False
        host = p.hostname or ""
        return host == "scribd.com" or host.endswith(".scribd.com")
    except Exception:
        return False


@bp.post("/download")
def download():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "")
    if not isinstance(url, str) or not url.strip() or len(url) > 500:
        return jsonify(error="Please provide a Scribd document URL."), 400
    if not is_valid_scribd_url(url):
        return jsonify(error="Only scribd.com document URLs are supported."), 400

    # Lazy import so the app boots even if scraper deps are missing.
    try:
        from ..scraper import scrape_scribd_to_pdf
    except Exception as e:
        return jsonify(error=f"Downloader engine unavailable: {e}"), 500

    tmpdir = tempfile.mkdtemp(prefix="scribd-")
    try:
        try:
            meta = scrape_scribd_to_pdf(url.strip(), os.path.join(tmpdir, "doc.pdf"))
        except Exception as e:
            return jsonify(error=str(e) or "Scraping failed."), 500

        pdf_path = os.path.join(tmpdir, "doc.pdf")
        if not os.path.exists(pdf_path):
            return jsonify(error="No PDF was produced. The document may be protected, removed, or unavailable."), 500

        size = os.path.getsize(pdf_path)
        title = (meta.get("title") or "document") if isinstance(meta, dict) else "document"
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in title)[:80] or "document"
        filename = f"{safe}.pdf"

        def generate():
            try:
                with open(pdf_path, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        yield chunk
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(size),
            "Cache-Control": "no-store",
        }
        return Response(
            stream_with_context(generate()),
            mimetype="application/pdf",
            headers=headers,
        )
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
