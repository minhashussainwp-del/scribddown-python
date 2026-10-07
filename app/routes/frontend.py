"""Public frontend routes."""
import hashlib

from flask import (
    Blueprint, render_template, request, g, redirect, Response,
    abort, current_app,
)

from ..models import Post, Page, Category, ContactMessage, MenuItem
from ..i18n import t, get_lang, SUPPORTED
from ..shortcodes import render_shortcodes
from .. import get_setting

bp = Blueprint("frontend", __name__)


def ctx_base():
    db = g.db
    lang = g.lang
    menu_items = db.query(MenuItem).order_by(MenuItem.position).all()
    # Prefix menu URLs with lang if they start with /en/ etc. Keep simple:
    # menu URLs are stored lang-agnostic like /blog -> prepend /<lang>.
    nav = []
    for m in menu_items:
        url = m.url
        # rewrite /en/... or /<other-lang>/... to current lang
        for l in SUPPORTED:
            if url == f"/{l}" or url.startswith(f"/{l}/"):
                url = f"/{lang}" + url[len(f"/{l}"):] or f"/{lang}/"
                break
        else:
            if url.startswith("/") and not url.startswith("//"):
                url = f"/{lang}{url}"
        nav.append({"label": m.label, "url": url})
    return {
        "lang": lang, "t": lambda k: t(lang, k),
        "site_name": get_setting(db, "site.name", "ScribdDown"),
        "nav": nav,
        "app_url": current_app.config["APP_URL"],
    }


def latest_posts_fn(n=5):
    return (
        g.db.query(Post)
        .filter(Post.published.is_(True), Post.lang == g.lang)
        .order_by(Post.published_at.desc())
        .limit(n).all()
    )


def render_content(html: str) -> str:
    return render_shortcodes(
        html, {"lang": g.lang, "latest_posts_fn": latest_posts_fn,
               "contact_label": t(g.lang, "nav_contact")}
    )


@bp.get("/")
def root():
    return redirect(f"/{get_lang(None)}/")


@bp.get("/<lang>/")
def home(lang):
    lang = get_lang(lang)
    g.lang = lang
    db = g.db
    front_slug = get_setting(db, "reading.frontpage", "")
    if front_slug:
        page = (
            db.query(Page)
            .filter(Page.slug == front_slug, Page.published.is_(True))
            .first()
        )
        if page:
            return render_template(
                "page.html", **ctx_base(), page=page,
                content=render_content(page.content),
                title=page.meta_title or page.title,
                description=page.meta_description,
            )
    posts = latest_posts_fn(3)
    faqs = [
        ("Is it free?", "Yes — no account, no payment, no watermark."),
        ("Do I need to install anything?", "No. Everything runs in your browser."),
        ("Where is my file stored?",
         "Only on your device. The PDF is generated in temporary memory and streamed to your browser."),
    ]
    return render_template(
        "index.html", **ctx_base(), posts=posts, faqs=faqs,
        title=get_setting(db, "seo.home_title", "Scribd Downloader — Download Scribd PDFs Free | ScribdDown"),
        description=get_setting(db, "seo.home_description", ""),
        content="",
    )


@bp.get("/<lang>/blog")
def blog_index(lang):
    lang = get_lang(lang); g.lang = lang
    db = g.db
    posts = (
        db.query(Post)
        .filter(Post.published.is_(True), Post.lang == lang)
        .order_by(Post.published_at.desc()).all()
    )
    return render_template(
        "blog/index.html", **ctx_base(), posts=posts,
        title=get_setting(db, "seo.blog_title", "Blog — ScribdDown"),
        description="", content="",
    )


@bp.get("/<lang>/blog/<slug>")
def blog_post(lang, slug):
    lang = get_lang(lang); g.lang = lang
    db = g.db
    post = (
        db.query(Post)
        .filter(Post.slug == slug, Post.published.is_(True))
        .first()
    )
    if not post:
        abort(404)
    return render_template(
        "blog/post.html", **ctx_base(), post=post,
        content=render_content(post.content),
        title=post.meta_title or post.title,
        description=post.meta_description or post.excerpt,
    )


@bp.get("/<lang>/contact")
def contact(lang):
    lang = get_lang(lang); g.lang = lang
    db = g.db
    return render_template(
        "contact.html", **ctx_base(),
        title="Contact Us — " + get_setting(db, "site.name", "ScribdDown"),
        description="", content="", sent=False,
    )


@bp.post("/<lang>/contact")
def contact_submit(lang):
    lang = get_lang(lang); g.lang = lang
    db = g.db
    # Honeypot
    if request.form.get("website"):
        return render_template(
            "contact.html", **ctx_base(), title="Contact Us",
            description="", content="", sent=True,
        )
    name = request.form.get("name", "").strip()[:128]
    email = request.form.get("email", "").strip()[:255]
    subject = request.form.get("subject", "").strip()[:255]
    message = request.form.get("message", "").strip()
    if len(name) < 2 or "@" not in email or len(message) < 10:
        return render_template(
            "contact.html", **ctx_base(), title="Contact Us",
            description="", content="", sent=False,
            error="Please fill in all fields correctly.",
        )
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    db.add(ContactMessage(
        name=name, email=email, subject=subject, message=message,
        ip_hash=hashlib.sha256(ip.encode()).hexdigest()[:32],
    ))
    db.commit()
    return render_template(
        "contact.html", **ctx_base(), title="Contact Us",
        description="", content="", sent=True,
    )


@bp.get("/<lang>/<slug>")
def page_view(lang, slug):
    lang = get_lang(lang); g.lang = lang
    db = g.db
    # Don't shadow reserved paths
    if slug in ("blog", "contact", "api", "admin", "static"):
        abort(404)
    page = (
        db.query(Page)
        .filter(Page.slug == slug, Page.published.is_(True))
        .first()
    )
    if not page:
        abort(404)
    return render_template(
        "page.html", **ctx_base(), page=page,
        content=render_content(page.content),
        title=page.meta_title or page.title,
        description=page.meta_description,
    )


@bp.get("/sitemap.xml")
def sitemap():
    db = g.db
    app_url = current_app.config["APP_URL"]
    urls = []
    for lang in SUPPORTED:
        urls.append(f"{app_url}/{lang}/")
        urls.append(f"{app_url}/{lang}/blog")
        urls.append(f"{app_url}/{lang}/contact")
        for p in db.query(Post).filter(Post.published.is_(True)).all():
            urls.append(f"{app_url}/{lang}/blog/{p.slug}")
        for pg in db.query(Page).filter(Page.published.is_(True)).all():
            urls.append(f"{app_url}/{lang}/{pg.slug}")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{u}</loc></url>" for u in urls)
        + "</urlset>"
    )
    return Response(xml, mimetype="application/xml")


@bp.get("/robots.txt")
def robots():
    app_url = current_app.config["APP_URL"]
    return Response(
        f"User-agent: *\nAllow: /\nSitemap: {app_url}/sitemap.xml\n",
        mimetype="text/plain",
    )
