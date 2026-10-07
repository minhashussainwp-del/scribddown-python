"""Seed default settings, pages, and launch blog posts on first run."""
from datetime import datetime, timezone

from .models import Setting, Category, Post, Page, MenuItem

DEFAULT_SETTINGS = {
    "site.name": "ScribdDown",
    "site.tagline": "Download Scribd documents as PDF — free, no signup.",
    "seo.home_title": "Scribd Downloader — Download Scribd PDFs Free | ScribdDown",
    "seo.home_description": (
        "Download any public Scribd document as a PDF for free. No account, "
        "no watermark — paste the link and get your file straight in your browser."
    ),
    "seo.blog_title": "Blog — ScribdDown",
    "permalink.blog": "/blog/<slug>",
    "permalink.page": "/<slug>",
    "reading.frontpage": "",  # page slug to use as homepage; empty = tool homepage
}

PAGES = [
    {
        "title": "About",
        "slug": "about",
        "content": """<h2>About ScribdDown</h2>
<p>ScribdDown is a free online tool that lets you download public Scribd documents as PDF files. No account, no subscription, no watermark.</p>
<h3>How it works</h3>
<p>Paste the link of any public Scribd document into the downloader on our homepage. We fetch the publicly available pages, assemble them into a PDF, and send the file straight to your browser. Nothing is stored on our servers — your download lives only on your device.</p>
<h3>What we don't do</h3>
<p>We can't download documents that Scribd keeps behind a login or paywall. If a document isn't publicly visible, our tool will tell you so instead of pretending otherwise.</p>""",
        "meta_title": "About — ScribdDown",
        "meta_description": "ScribdDown is a free tool to download public Scribd documents as PDF. No account needed.",
    },
    {
        "title": "Privacy Policy",
        "slug": "privacy-policy",
        "content": """<h2>Privacy Policy</h2>
<p><strong>Last updated: October 2026</strong></p>
<p>ScribdDown does not store your downloaded files. When you download a document, the PDF is generated in temporary memory and streamed directly to your browser. No copies are kept on our servers.</p>
<h3>What we collect</h3>
<ul><li>Contact form messages (name, email, message) so we can reply to you.</li><li>Basic anonymous usage logs for keeping the service running.</li></ul>
<h3>What we don't collect</h3>
<ul><li>We don't ask you to create an account.</li><li>We don't track you across the web.</li><li>We don't sell any data — there is nothing to sell.</li></ul>""",
        "meta_title": "Privacy Policy — ScribdDown",
        "meta_description": "ScribdDown privacy policy: no file storage, no accounts, no tracking.",
    },
    {
        "title": "Terms of Service",
        "slug": "terms",
        "content": """<h2>Terms of Service</h2>
<p>By using ScribdDown you agree to use the tool only for documents you have the right to download. Only public Scribd documents can be processed.</p>
<p>We are not affiliated with Scribd. Document copyrights belong to their respective owners.</p>""",
        "meta_title": "Terms of Service — ScribdDown",
        "meta_description": "ScribdDown terms of service.",
    },
]

POSTS = [
    {
        "title": "How to Download Scribd Documents Free (2026 Guide)",
        "slug": "how-to-download-scribd-documents-free",
        "excerpt": "A simple step-by-step guide to downloading public Scribd documents as PDF files — free, no account needed.",
        "category": "Guides",
        "tags": ["scribd downloader", "pdf", "guide"],
        "meta_title": "How to Download Scribd Documents Free — ScribdDown",
        "meta_description": "Download any public Scribd document as a PDF for free. Step-by-step guide, no account or subscription needed.",
        "content": """<p>Scribd hosts millions of documents — books, presentations, research papers, manuals. But downloading them usually means paying for a subscription. Here's how to get the public ones as PDFs for free.</p>
<h2>Step 1: Find your document</h2>
<p>Open the document on scribd.com and copy its URL from your browser's address bar. It looks like <code>scribd.com/document/123456789/document-title</code>.</p>
<h2>Step 2: Paste it into ScribdDown</h2>
<p>Go to the <a href="/">ScribdDown homepage</a>, paste the URL into the downloader box, and hit Download. No account, no email, nothing to install.</p>
<h2>Step 3: Wait a moment</h2>
<p>Fetching the pages takes a little while — usually under a minute for short documents, a few minutes for long ones. You'll see a progress indicator.</p>
<h2>Step 4: Save the PDF</h2>
<p>Your browser downloads the PDF directly. The file is generated in temporary memory and streamed to you — we never store it on our servers.</p>
<h2>What if it fails?</h2>
<p>Some documents can't be downloaded: ones behind Scribd's login wall, removed documents, or private uploads. The tool will tell you plainly instead of hanging.</p>
<h2>Tips</h2>
<ul>
<li><strong>Check it's public first:</strong> open the link in a private browser window. If you can read it without logging in, it can be downloaded.</li>
<li><strong>Long documents take longer:</strong> a 200-page document needs a few minutes. Be patient.</li>
<li><strong>Respect copyright:</strong> download for personal use — study, research, offline reading.</li>
</ul>
<h2>Frequently asked questions</h2>
<h3>Is it really free?</h3>
<p>Yes. No account, no trial, no payment. The tool is free to use.</p>
<h3>Do I need to install anything?</h3>
<p>No. Everything runs in your browser.</p>
<h3>Where is my file stored?</h3>
<p>Only on your device. We generate the PDF in temporary memory and stream it to your browser, then wipe it.</p>
<h3>Can I download any Scribd document?</h3>
<p>Any <em>public</em> one. Documents behind Scribd's paywall or login can't be downloaded — and any tool claiming otherwise isn't being honest.</p>""",
    },
    {
        "title": "Scribd Downloader Without Login: Get PDFs Free",
        "slug": "scribd-downloader-without-login",
        "excerpt": "You don't need a Scribd account to download public documents. Here's how to do it without logging in.",
        "category": "Guides",
        "tags": ["scribd downloader", "no login", "pdf"],
        "meta_title": "Scribd Downloader Without Login — Free PDFs | ScribdDown",
        "meta_description": "Download Scribd documents without an account. Free tool, no login, PDF straight to your browser.",
        "content": """<p>Scribd wants you to create an account — or pay — before downloading. But public documents are publicly visible, which means they can be fetched without logging in. Here's the honest breakdown.</p>
<h2>Why no login is needed</h2>
<p>A public Scribd document loads its pages for any visitor, logged in or not. A downloader simply collects those same public pages and packages them as a PDF. No credentials, no session, no tricks.</p>
<h2>How to do it</h2>
<ol>
<li>Copy the document URL from scribd.com.</li>
<li>Paste it into the <a href="/">ScribdDown downloader</a>.</li>
<li>Download the PDF when it's ready.</li>
</ol>
<p>That's it. No email address, no password, no "free trial" that bills you later.</p>
<h2>What "without login" can't do</h2>
<p>Let's be clear about the limits:</p>
<ul>
<li><strong>Paywalled documents:</strong> if Scribd only shows a preview and hides the rest behind a subscription, those hidden pages aren't public — no tool can get them without an account.</li>
<li><strong>Private documents:</strong> unlisted or private uploads aren't accessible at all.</li>
<li><strong>Removed documents:</strong> deleted is deleted.</li>
</ul>
<h2>Is it safe?</h2>
<p>Using ScribdDown is as safe as browsing the web: you paste a link, you get a file. We don't store your files, we don't ask for personal details, and the PDF is generated fresh for each request.</p>
<h2>Frequently asked questions</h2>
<h3>Will Scribd know I downloaded it?</h3>
<p>No account is involved, so there's nothing tying the download to you.</p>
<h3>Is there a download limit?</h3>
<p>No artificial limits. Long documents just take longer to process.</p>
<h3>Does it work on mobile?</h3>
<p>Yes — paste the link in your phone's browser and the PDF downloads like any other file.</p>
<h3>Why do some tools ask for login?</h3>
<p>Usually to harvest accounts or push subscriptions. A public document never requires your Scribd credentials.</p>""",
    },
    {
        "title": "Is It Legal to Download From Scribd?",
        "slug": "is-it-legal-to-download-from-scribd",
        "excerpt": "The honest answer about downloading Scribd documents: what the law says and what actually matters.",
        "category": "Guides",
        "tags": ["scribd", "legal", "copyright"],
        "meta_title": "Is It Legal to Download From Scribd? — ScribdDown",
        "meta_description": "Is downloading Scribd documents legal? An honest look at copyright, fair use, and personal downloads.",
        "content": """<p>This is the question everyone asks and most downloader sites dodge. Here's the straight answer.</p>
<h2>The short version</h2>
<p>Downloading a document you have the right to access — for personal use, study, or research — is generally fine. Redistributing copyrighted work as your own is not. The tool doesn't change the rules; <em>what you do with the file</em> does.</p>
<h2>What the law actually cares about</h2>
<ul>
<li><strong>Personal use:</strong> downloading a public manual to read offline, a paper for your thesis, a template for your own project — this is what most people do, and it's the lowest-risk category.</li>
<li><strong>Fair use (US):</strong> commentary, criticism, teaching, and research have explicit protections. Quoting a document in your work with attribution is classic fair use.</li>
<li><strong>Redistribution:</strong> re-uploading someone's book to sell it, or posting paywalled content publicly — that's infringement, with or without a downloader.</li>
</ul>
<h2>Public doesn't mean public domain</h2>
<p>A document being publicly <em>visible</em> on Scribd doesn't mean it's free of copyright. The author still owns it. Think of it like a library book: you can read it and take notes, but you can't print copies and sell them.</p>
<h2>Our position</h2>
<p>ScribdDown only processes documents Scribd serves publicly. We don't bypass paywalls or logins. What you download is between you and the copyright holder — use common sense and keep it personal.</p>
<p><em>We're not lawyers, and this isn't legal advice. If you're unsure about a specific use, check with someone qualified.</em></p>
<h2>Frequently asked questions</h2>
<h3>Can I get in trouble for downloading?</h3>
<p>For personal use of public documents, this is extremely unlikely to be an issue. Problems arise from redistribution, not downloading.</p>
<h3>Does Scribd allow downloading?</h3>
<p>Scribd's own download feature requires a subscription for many documents. Third-party tools exist in a gray area — which is why we stick strictly to public content.</p>
<h3>What about documents I uploaded myself?</h3>
<p>Downloading your own uploads is unambiguously fine.</p>""",
    },
]


def run_seed(db):
    # Settings
    for k, v in DEFAULT_SETTINGS.items():
        db.add(Setting(key=k, value=v))

    # Categories
    cats = {}
    for name in ["Guides", "News"]:
        slug = name.lower()
        c = Category(name=name, slug=slug)
        db.add(c)
        db.flush()
        cats[name] = c

    # Menu
    for i, (label, url) in enumerate(
        [("Home", "/en/"), ("Blog", "/en/blog"), ("Contact", "/en/contact")]
    ):
        db.add(MenuItem(label=label, url=url, position=i))
    db.flush()

    # Pages
    for p in PAGES:
        db.add(Page(
            title=p["title"], slug=p["slug"], content=p["content"],
            published=True, meta_title=p["meta_title"],
            meta_description=p["meta_description"], lang="en",
        ))
    db.flush()

    # Posts
    for p in POSTS:
        post = Post(
            title=p["title"], slug=p["slug"], excerpt=p["excerpt"],
            content=p["content"], category_id=cats[p["category"]].id,
            published=True, meta_title=p["meta_title"],
            meta_description=p["meta_description"], lang="en",
            published_at=datetime.now(timezone.utc),
        )
        db.add(post)
        db.flush()
        for tname in p["tags"]:
            from .models import Tag
            slug = tname.lower().replace(" ", "-")
            tag = db.query(Tag).filter_by(slug=slug).first()
            if not tag:
                tag = Tag(name=tname, slug=slug)
                db.add(tag)
                db.flush()
            post.tags.append(tag)

    db.commit()
