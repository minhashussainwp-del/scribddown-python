"""Shortcode parser: [scribd_downloader], [contact_form], [latest_posts]."""
import re
from html import escape


def render_shortcodes(html: str, ctx: dict) -> str:
    """Replace known shortcodes in page/post HTML. ctx carries lang, helpers."""
    lang = ctx.get("lang", "en")

    def latest_posts(m):
        count = int(m.group(1) or 5)
        posts = ctx.get("latest_posts_fn", lambda n: [])(count)
        if not posts:
            return ""
        items = "".join(
            f'<li><a href="/{lang}/blog/{escape(p.slug)}">{escape(p.title)}</a></li>'
            for p in posts
        )
        return f'<div class="shortcode-latest-posts"><ul>{items}</ul></div>'

    html = re.sub(
        r"\[latest_posts(?:\s+count=(\d+))?\]",
        latest_posts,
        html,
    )
    html = html.replace(
        "[scribd_downloader]",
        '<div id="shortcode-downloader"></div>'
        '<script>document.getElementById("shortcode-downloader")'
        '.innerHTML = document.getElementById("main-downloader").innerHTML;</script>',
    )
    html = html.replace(
        "[contact_form]",
        f'<div class="shortcode-contact"><a href="/{lang}/contact">'
        f"{escape(ctx.get('contact_label', 'Contact us'))}</a></div>",
    )
    return html
