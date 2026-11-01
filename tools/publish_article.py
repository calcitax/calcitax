#!/usr/bin/env python3
"""Publish a news article to calcitax.com.

Usage:
    python3 tools/publish_article.py path/to/article.json        # add or replace one article
    python3 tools/publish_article.py --rebuild                    # regenerate all pages from the registry

The article JSON looks like:
{
  "slug": "bank-of-canada-raises-rate-october-2026",      # lowercase, digits, hyphens
  "title": "Bank of Canada raises its rate to 2.5%: what it means for you",
  "description": "One or two sentences for Google and the news list (max ~160 chars).",
  "date": "2026-10-31",                                   # YYYY-MM-DD (Pacific)
  "category": "Economy",                                  # Personal tax | Business tax | Economy | CRA updates | Deadlines | ...
  "body_html": "<p>...</p><h2>...</h2>...",                # article body: p, h2, h3, ul, ol, li, strong, em, a, table
  "sources": [{"title": "Bank of Canada press release", "url": "https://..."}]
}

The script:
  * validates the article,
  * stores it in content/news.json (the registry, newest first),
  * writes public/news/<slug>.html,
  * regenerates public/news/index.html, public/news/feed.xml,
    the "Latest news" block on public/index.html and the news entries in public/sitemap.xml.
"""
import datetime as dt
import html
import json
import re
import sys
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
REGISTRY = ROOT / "content" / "news.json"
SITE = "https://calcitax.com"

ALLOWED_TAGS = {"p", "h2", "h3", "ul", "ol", "li", "strong", "em", "b", "i", "a", "table", "thead",
                "tbody", "tr", "th", "td", "blockquote", "br"}


def fail(msg):
    sys.exit(f"ERROR: {msg}")


def esc(s):
    return html.escape(str(s), quote=True)


def nice_date(d):
    return dt.date.fromisoformat(d).strftime("%B %-d, %Y")


def validate(a):
    for key in ("slug", "title", "description", "date", "category", "body_html", "sources"):
        if not a.get(key):
            fail(f"missing '{key}'")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a["slug"]) or len(a["slug"]) > 90:
        fail("slug must be lowercase words joined by hyphens (max 90 chars)")
    try:
        dt.date.fromisoformat(a["date"])
    except ValueError:
        fail("date must be YYYY-MM-DD")
    if len(a["title"]) > 120:
        fail("title too long (max 120 chars)")
    if len(a["description"]) > 200:
        fail("description too long (max 200 chars)")
    tags = set(t.lower() for t in re.findall(r"</?\s*([a-zA-Z0-9]+)", a["body_html"]))
    bad = tags - ALLOWED_TAGS
    if bad:
        fail(f"body_html uses tags that aren't allowed: {sorted(bad)}")
    if re.search(r"<\s*(script|style|iframe)|on[a-z]+\s*=|javascript:", a["body_html"], re.I):
        fail("body_html must not contain scripts, styles, iframes or event handlers")
    if len(re.sub(r"<[^>]+>", " ", a["body_html"]).split()) < 250:
        fail("body is too short (aim for 450-900 words)")
    if not isinstance(a["sources"], list) or not a["sources"]:
        fail("at least one source is required")
    for s in a["sources"]:
        if not s.get("title") or not str(s.get("url", "")).startswith("https://"):
            fail("each source needs a title and an https:// url")


# ---------------------------------------------------------------------------
# Shared page pieces
# ---------------------------------------------------------------------------

HEAD = """<!doctype html>
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="Calcitax Advisors News" href="/news/feed.xml">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css">
{extra_head}</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<header class="site-header">
  <div class="wrap header-row">
    <a class="brand" href="/" aria-label="Calcitax Advisors home">
      <span class="brand-mark" aria-hidden="true">C</span>
      <span class="brand-name">Calcitax <span>Advisors</span></span>
    </a>
    <nav class="nav" aria-label="Main">
      <a href="/">Home</a>
      <a href="/services.html">Services</a>
      <a href="/about.html">About</a>
      <a href="/tax-dates.html">Tax Dates</a>
      <a href="/forms.html">Client Forms</a>
      <a href="/news/" aria-current="page">News</a>
      <a class="btn btn-primary" href="/contact.html">Free consultation</a>
    </nav>
  </div>
</header>
"""

FOOT = """
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <div class="footer-brand">Calcitax Advisors</div>
        <div class="footer-tag">We calculate. You save.</div>
        <p>Tax returns, bookkeeping and payroll for individuals and small businesses in Surrey, Vancouver, Burnaby and across Metro Vancouver, and online across Canada.</p>
      </div>
      <div>
        <h2>Pages</h2>
        <ul>
          <li><a href="/services.html">Services</a></li>
          <li><a href="/about.html">About</a></li>
          <li><a href="/tax-dates.html">Tax dates</a></li>
          <li><a href="/forms.html">Client forms</a></li>
          <li><a href="/news/">News</a></li>
          <li><a href="/contact.html">Contact</a></li>
        </ul>
      </div>
      <div>
        <h2>Contact</h2>
        <ul>
          <li><a href="mailto:info@calcitax.com">info@calcitax.com</a></li>
          <li>Surrey, British Columbia</li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>Information on this site is general in nature and is not professional advice. Contact us about your own situation.</p>
      <p>© {year} Calcitax Advisors</p>
    </div>
  </div>
</footer>
</body>
</html>
"""


def card(a, heading="h2"):
    return f"""      <a class="card news-card" href="/news/{a['slug']}.html">
        <p class="news-meta"><span>{esc(a['category'])}</span> · <time datetime="{a['date']}">{nice_date(a['date'])}</time></p>
        <{heading}>{esc(a['title'])}</{heading}>
        <p>{esc(a['description'])}</p>
        <span class="more">Read more →</span>
      </a>"""


def article_page(a, related):
    url = f"{SITE}/news/{a['slug']}.html"
    ld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": a["title"],
        "description": a["description"],
        "datePublished": a["date"],
        "dateModified": a.get("updated", a["date"]),
        "mainEntityOfPage": url,
        "author": {"@type": "Organization", "name": "Calcitax Advisors"},
        "publisher": {"@type": "Organization", "name": "Calcitax Advisors", "url": SITE},
    }
    extra_head = ('<script type="application/ld+json">\n'
                  + json.dumps(ld, indent=2).replace("</", "<\\/") + "\n</script>\n")
    sources = "\n".join(
        f'          <li><a href="{esc(s["url"])}" rel="noopener" target="_blank">{esc(s["title"])}</a></li>'
        for s in a["sources"])
    related_html = ""
    if related:
        related_html = ("\n<section class=\"section tint\" aria-labelledby=\"more-news\">\n  <div class=\"wrap\">\n"
                        "    <h2 class=\"h2\" id=\"more-news\">More news</h2>\n    <div class=\"grid-3 news-grid\">\n"
                        + "\n".join(card(r, "h3") for r in related)
                        + "\n    </div>\n  </div>\n</section>\n")
    updated = ""
    if a.get("updated") and a["updated"] != a["date"]:
        updated = f' · Updated <time datetime="{a["updated"]}">{nice_date(a["updated"])}</time>'
    return (HEAD.format(title=esc(a["title"]) + " | Calcitax Advisors", description=esc(a["description"]),
                        url=url, og_type="article", og_title=esc(a["title"]), extra_head=extra_head)
            + f"""
<main id="main">

<article>
  <header class="page-hero article-hero">
    <div class="wrap narrow">
      <p class="eyebrow"><a href="/news/">News</a> · {esc(a['category'])}</p>
      <h1>{esc(a['title'])}</h1>
      <p class="news-meta">By Calcitax Advisors · <time datetime="{a['date']}">{nice_date(a['date'])}</time>{updated}</p>
    </div>
  </header>

  <div class="section article-section">
    <div class="wrap narrow">
      <div class="prose article-body">
{a['body_html']}
      </div>

      <aside class="article-cta">
        <h2>Questions about how this affects you?</h2>
        <p>Calcitax Advisors helps individuals and small businesses across Metro Vancouver with tax, bookkeeping and payroll. Book a free consultation.</p>
        <a class="btn btn-primary" href="/contact.html">Contact us</a>
      </aside>

      <div class="article-sources">
        <h2>Sources</h2>
        <ul>
{sources}
        </ul>
      </div>
      <p class="notice">This article is general information based on sources available on {nice_date(a.get('updated', a['date']))}. It isn't professional advice. Rules and figures can change, so contact us about your own situation.</p>
    </div>
  </div>
</article>
{related_html}
</main>
""" + FOOT.format(year=a["date"][:4]))


def news_index(articles):
    cards = "\n".join(card(a) for a in articles) or '      <p class="lead">Articles are coming soon.</p>'
    return (HEAD.format(title="Accounting, Tax &amp; Finance News | Calcitax Advisors",
                        description="Plain-language news on Canadian tax, CRA updates, interest rates and the economy, and what it means for individuals and small businesses in Metro Vancouver.",
                        url=f"{SITE}/news/", og_type="website", og_title="News | Calcitax Advisors", extra_head="")
            + f"""
<main id="main">

<section class="page-hero">
  <div class="wrap">
    <p class="eyebrow">News</p>
    <h1>Accounting, tax &amp; finance news</h1>
    <p class="lead">What's happening with Canadian tax, the CRA, interest rates and the economy, explained in plain language with what it means for you and your business.</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="grid-3 news-grid">
{cards}
    </div>
    <p class="notice">Want new articles as soon as they're published? <a href="/news/subscribe.html">See how to follow our news</a>.</p>
  </div>
</section>

</main>
""" + FOOT.format(year=dt.date.today().year))


def subscribe_page():
    feed = f"{SITE}/news/feed.xml"
    return (HEAD.format(title="Follow Our News | Calcitax Advisors",
                        description="How to get Calcitax Advisors' tax and finance articles as soon as they're published.",
                        url=f"{SITE}/news/subscribe.html", og_type="website", og_title="Follow our news | Calcitax Advisors",
                        extra_head="")
            + f"""
<main id="main">

<section class="page-hero">
  <div class="wrap narrow">
    <p class="eyebrow"><a href="/news/" style="color:inherit;text-decoration:none">News</a></p>
    <h1>Follow our news</h1>
    <p class="lead">We publish a new plain-language article on Canadian tax and finance most days. Here are the easiest ways to keep up.</p>
  </div>
</section>

<section class="section">
  <div class="wrap narrow prose">
    <h2>1. Bookmark our news page</h2>
    <p>Save <a href="/news/">calcitax.com/news</a> to your browser's bookmarks or your phone's home screen and check back any time.</p>

    <h2>2. Use a news reader app (RSS)</h2>
    <p>If you use a news reader such as Feedly, Inoreader or NetNewsWire, add our feed address and new articles will appear there automatically:</p>
    <div class="copy-row">
      <input id="feed-url" type="text" value="{feed}" readonly aria-label="News feed address">
      <button class="btn btn-primary" type="button" id="copy-feed">Copy address</button>
    </div>
    <p class="muted" id="copy-note" role="status" aria-live="polite"></p>
    <p>The feed is designed for news reader apps. Opening it in a browser shows a simple list of our latest articles.</p>

    <h2>3. Have a question instead?</h2>
    <p>If an article raises a question about your own taxes or business, <a href="/contact.html">send us a message</a> and we'll get back to you.</p>
  </div>
</section>

</main>
<script>
  document.getElementById('copy-feed').addEventListener('click', function () {{
    var input = document.getElementById('feed-url');
    var note = document.getElementById('copy-note');
    input.select();
    (navigator.clipboard ? navigator.clipboard.writeText(input.value) : Promise.reject())
      .then(function () {{ note.textContent = 'Copied! Paste it into your news reader.'; }})
      .catch(function () {{ document.execCommand('copy'); note.textContent = 'Copied! Paste it into your news reader.'; }});
  }});
</script>
""" + FOOT.format(year=dt.date.today().year))


def rss(articles):
    items = []
    for a in articles[:30]:
        pub = dt.datetime.fromisoformat(a["date"] + "T06:00:00-08:00")
        items.append(f"""  <item>
    <title>{esc(a['title'])}</title>
    <link>{SITE}/news/{a['slug']}.html</link>
    <guid isPermaLink="true">{SITE}/news/{a['slug']}.html</guid>
    <pubDate>{format_datetime(pub)}</pubDate>
    <category>{esc(a['category'])}</category>
    <description>{esc(a['description'])}</description>
  </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="/news/feed.xsl"?>
<rss version="2.0">
<channel>
  <title>Calcitax Advisors News</title>
  <link>{SITE}/news/</link>
  <description>Canadian tax, accounting and finance news in plain language.</description>
  <language>en-ca</language>
{chr(10).join(items)}
</channel>
</rss>
"""


def replace_block(text, start, end, inner, path):
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        fail(f"markers {start} / {end} not found in {path}")
    return pattern.sub(lambda _m: start + inner + end, text)


def rebuild(articles):
    news_dir = PUBLIC / "news"
    news_dir.mkdir(exist_ok=True)
    for i, a in enumerate(articles):
        related = [r for r in articles if r["slug"] != a["slug"]][:3]
        (news_dir / f"{a['slug']}.html").write_text(article_page(a, related))
    (news_dir / "index.html").write_text(news_index(articles))
    (news_dir / "feed.xml").write_text(rss(articles))
    (news_dir / "subscribe.html").write_text(subscribe_page())

    home = PUBLIC / "index.html"
    latest = "\n".join(card(a, "h3") for a in articles[:3]) or '      <p class="lead">Articles are coming soon.</p>'
    home.write_text(replace_block(home.read_text(), "<!-- NEWS:START -->", "<!-- NEWS:END -->",
                                  "\n" + latest + "\n      ", home))

    sitemap = PUBLIC / "sitemap.xml"
    entries = [f"  <url><loc>{SITE}/news/</loc><lastmod>{articles[0]['date'] if articles else dt.date.today()}</lastmod></url>"]
    entries += [f"  <url><loc>{SITE}/news/{a['slug']}.html</loc><lastmod>{a.get('updated', a['date'])}</lastmod></url>"
                for a in articles]
    sitemap.write_text(replace_block(sitemap.read_text(), "<!-- NEWS:START -->", "<!-- NEWS:END -->",
                                     "\n" + "\n".join(entries) + "\n  ", sitemap))


def load():
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text())
    return []


def save(articles):
    REGISTRY.parent.mkdir(exist_ok=True)
    REGISTRY.write_text(json.dumps(articles, indent=2, ensure_ascii=False) + "\n")


def main():
    if len(sys.argv) != 2:
        fail(__doc__)
    articles = load()
    if sys.argv[1] != "--rebuild":
        a = json.loads(Path(sys.argv[1]).read_text())
        validate(a)
        articles = [x for x in articles if x["slug"] != a["slug"]]
        articles.append(a)
    articles.sort(key=lambda x: (x["date"], x.get("order", 0)), reverse=True)
    save(articles)
    rebuild(articles)
    print(f"OK: {len(articles)} article(s) published. Newest: {articles[0]['title'] if articles else '-'}")


if __name__ == "__main__":
    main()
