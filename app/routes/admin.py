"""Admin panel: session login, dashboard, CRUD, settings, inbox."""
import os
from datetime import datetime, timezone
from functools import wraps

import bcrypt
from flask import (
    Blueprint, render_template, request, g, redirect, session,
    current_app, abort,
)

from ..models import Post, Page, Category, Tag, MenuItem, ContactMessage, Setting
from .. import get_setting, set_setting

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin/login?next=" + request.path)
        return f(*args, **kwargs)
    return wrapper


def check_password(password: str) -> bool:
    pw_hash = os.environ.get("ADMIN_PASSWORD_HASH", "")
    if not pw_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode(), pw_hash.encode())
    except Exception:
        return False


@bp.get("/login")
def login():
    if session.get("admin"):
        return redirect("/admin/")
    return render_template("admin/login.html", error="")


@bp.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    want = os.environ.get("ADMIN_EMAIL", "admin@scribddown.local").strip().lower()
    if email == want and check_password(password):
        session["admin"] = True
        return redirect(request.args.get("next") or "/admin/")
    return render_template("admin/login.html", error="Invalid credentials."), 401


@bp.get("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin/login")


def admin_ctx(**kw):
    db = g.db
    unread = db.query(ContactMessage).filter(ContactMessage.is_read.is_(False)).count()
    base = {
        "unread": unread,
        "site_name": get_setting(db, "site.name", "ScribdDown"),
    }
    base.update(kw)
    return base


@bp.get("/")
@admin_required
def dashboard():
    db = g.db
    return render_template(
        "admin/dashboard.html",
        **admin_ctx(
            posts=db.query(Post).count(),
            pages=db.query(Page).count(),
            messages=db.query(ContactMessage).count(),
            recent=db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).limit(5).all(),
        ),
    )


# ---- Posts ----
@bp.get("/posts")
@admin_required
def post_list():
    db = g.db
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    return render_template("admin/posts.html", **admin_ctx(posts=posts))


@bp.get("/posts/new")
@admin_required
def post_new():
    db = g.db
    return render_template(
        "admin/post_form.html",
        **admin_ctx(post=None, categories=db.query(Category).all()),
    )


@bp.post("/posts/new")
@admin_required
def post_create():
    db = g.db
    f = request.form
    now = datetime.now(timezone.utc)
    post = Post(
        title=f.get("title", "").strip()[:255],
        slug=f.get("slug", "").strip()[:255] or slugify(f.get("title", "")),
        excerpt=f.get("excerpt", ""),
        content=f.get("content", ""),
        category_id=int(f.get("category_id") or 0) or None,
        featured_image=f.get("featured_image", "").strip()[:512],
        published=bool(f.get("published")),
        published_at=now if f.get("published") else None,
        meta_title=f.get("meta_title", "").strip()[:255],
        meta_description=f.get("meta_description", "").strip()[:512],
        lang=f.get("lang", "en")[:8],
    )
    db.add(post)
    db.flush()
    sync_tags(db, post, f.get("tags", ""))
    db.commit()
    return redirect("/admin/posts")


@bp.get("/posts/<int:pid>/edit")
@admin_required
def post_edit(pid):
    db = g.db
    post = db.get(Post, pid)
    if not post:
        abort(404)
    return render_template(
        "admin/post_form.html",
        **admin_ctx(post=post, categories=db.query(Category).all(),
                    tag_str=", ".join(t.name for t in post.tags)),
    )


@bp.post("/posts/<int:pid>/edit")
@admin_required
def post_update(pid):
    db = g.db
    post = db.get(Post, pid)
    if not post:
        abort(404)
    f = request.form
    was_pub = post.published
    post.title = f.get("title", "").strip()[:255]
    post.slug = f.get("slug", "").strip()[:255]
    post.excerpt = f.get("excerpt", "")
    post.content = f.get("content", "")
    post.category_id = int(f.get("category_id") or 0) or None
    post.featured_image = f.get("featured_image", "").strip()[:512]
    post.published = bool(f.get("published"))
    if post.published and not was_pub and not post.published_at:
        post.published_at = datetime.now(timezone.utc)
    post.meta_title = f.get("meta_title", "").strip()[:255]
    post.meta_description = f.get("meta_description", "").strip()[:512]
    post.lang = f.get("lang", "en")[:8]
    post.tags.clear()
    db.flush()
    sync_tags(db, post, f.get("tags", ""))
    db.commit()
    return redirect("/admin/posts")


@bp.post("/posts/<int:pid>/delete")
@admin_required
def post_delete(pid):
    db = g.db
    post = db.get(Post, pid)
    if post:
        db.delete(post)
        db.commit()
    return redirect("/admin/posts")


# ---- Pages ----
@bp.get("/pages")
@admin_required
def page_list():
    db = g.db
    pages = db.query(Page).order_by(Page.created_at.desc()).all()
    return render_template("admin/pages.html", **admin_ctx(pages=pages))


@bp.get("/pages/new")
@admin_required
def page_new():
    return render_template("admin/page_form.html", **admin_ctx(page=None))


@bp.post("/pages/new")
@admin_required
def page_create():
    db = g.db
    f = request.form
    page = Page(
        title=f.get("title", "").strip()[:255],
        slug=f.get("slug", "").strip()[:255] or slugify(f.get("title", "")),
        content=f.get("content", ""),
        published=bool(f.get("published")),
        meta_title=f.get("meta_title", "").strip()[:255],
        meta_description=f.get("meta_description", "").strip()[:512],
        lang=f.get("lang", "en")[:8],
    )
    db.add(page)
    db.commit()
    return redirect("/admin/pages")


@bp.get("/pages/<int:pid>/edit")
@admin_required
def page_edit(pid):
    db = g.db
    page = db.get(Page, pid)
    if not page:
        abort(404)
    return render_template("admin/page_form.html", **admin_ctx(page=page))


@bp.post("/pages/<int:pid>/edit")
@admin_required
def page_update(pid):
    db = g.db
    page = db.get(Page, pid)
    if not page:
        abort(404)
    f = request.form
    page.title = f.get("title", "").strip()[:255]
    page.slug = f.get("slug", "").strip()[:255]
    page.content = f.get("content", "")
    page.published = bool(f.get("published"))
    page.meta_title = f.get("meta_title", "").strip()[:255]
    page.meta_description = f.get("meta_description", "").strip()[:512]
    page.lang = f.get("lang", "en")[:8]
    db.commit()
    return redirect("/admin/pages")


@bp.post("/pages/<int:pid>/delete")
@admin_required
def page_delete(pid):
    db = g.db
    page = db.get(Page, pid)
    if page:
        db.delete(page)
        db.commit()
    return redirect("/admin/pages")


# ---- Categories ----
@bp.get("/categories")
@admin_required
def cat_list():
    db = g.db
    return render_template(
        "admin/categories.html", **admin_ctx(cats=db.query(Category).all()))


@bp.post("/categories")
@admin_required
def cat_create():
    db = g.db
    name = request.form.get("name", "").strip()
    if name:
        db.add(Category(name=name[:128], slug=slugify(name)[:128]))
        db.commit()
    return redirect("/admin/categories")


@bp.post("/categories/<int:cid>/delete")
@admin_required
def cat_delete(cid):
    db = g.db
    c = db.get(Category, cid)
    if c:
        db.delete(c)
        db.commit()
    return redirect("/admin/categories")


# ---- Menus ----
@bp.get("/menus")
@admin_required
def menu_list():
    db = g.db
    items = db.query(MenuItem).order_by(MenuItem.position).all()
    return render_template("admin/menus.html", **admin_ctx(items=items))


@bp.post("/menus")
@admin_required
def menu_add():
    db = g.db
    label = request.form.get("label", "").strip()
    url = request.form.get("url", "").strip()
    if label and url:
        pos = db.query(MenuItem).count()
        db.add(MenuItem(label=label[:128], url=url[:512], position=pos))
        db.commit()
    return redirect("/admin/menus")


@bp.post("/menus/<int:mid>/delete")
@admin_required
def menu_delete(mid):
    db = g.db
    m = db.get(MenuItem, mid)
    if m:
        db.delete(m)
        db.commit()
    return redirect("/admin/menus")


# ---- Inbox ----
@bp.get("/inbox")
@admin_required
def inbox():
    db = g.db
    msgs = db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin/inbox.html", **admin_ctx(msgs=msgs))


@bp.get("/inbox/<int:mid>")
@admin_required
def inbox_view(mid):
    db = g.db
    m = db.get(ContactMessage, mid)
    if not m:
        abort(404)
    m.is_read = True
    db.commit()
    return render_template("admin/message.html", **admin_ctx(m=m))


@bp.post("/inbox/<int:mid>/delete")
@admin_required
def inbox_delete(mid):
    db = g.db
    m = db.get(ContactMessage, mid)
    if m:
        db.delete(m)
        db.commit()
    return redirect("/admin/inbox")


# ---- Settings ----
SETTING_FIELDS = [
    ("site.name", "Site name"),
    ("site.tagline", "Tagline"),
    ("seo.home_title", "Homepage title"),
    ("seo.home_description", "Homepage meta description"),
    ("seo.blog_title", "Blog index title"),
    ("permalink.blog", "Blog permalink (e.g. /blog/<slug>)"),
    ("permalink.page", "Page permalink (e.g. /<slug>)"),
    ("reading.frontpage", "Homepage: page slug (empty = downloader tool)"),
]


@bp.get("/settings")
@admin_required
def settings():
    db = g.db
    vals = {k: get_setting(db, k, "") for k, _ in SETTING_FIELDS}
    pages = db.query(Page).filter(Page.published.is_(True)).all()
    return render_template(
        "admin/settings.html", **admin_ctx(fields=SETTING_FIELDS, vals=vals, pages=pages))


@bp.post("/settings")
@admin_required
def settings_save():
    db = g.db
    for k, _ in SETTING_FIELDS:
        if k in request.form:
            set_setting(db, k, request.form.get(k, "").strip())
    return redirect("/admin/settings")


# ---- helpers ----
def slugify(s: str) -> str:
    import re
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:120] or "untitled"


def sync_tags(db, post, tag_str: str):
    for name in [t.strip() for t in tag_str.split(",") if t.strip()]:
        slug = slugify(name)[:64]
        tag = db.query(Tag).filter_by(slug=slug).first()
        if not tag:
            tag = Tag(name=name[:64], slug=slug)
            db.add(tag)
            db.flush()
        if tag not in post.tags:
            post.tags.append(tag)
