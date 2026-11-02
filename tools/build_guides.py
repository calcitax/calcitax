#!/usr/bin/env python3
"""Build the Guides section of calcitax.com.

Usage:
    python3 tools/build_guides.py

Each guide lives in content/guides/<slug>.json:
{
  "slug": "rental-income-tax-guide",
  "title": "H1 title",
  "seo_title": "Browser/Google title (site name is added)",
  "description": "Meta description, max ~160 chars",
  "topic": "Short eyebrow label, e.g. Personal tax",
  "audience": "individuals" | "business",
  "updated": "YYYY-MM-DD",                       # date the content was last checked
  "lead": "Intro paragraph",
  "figures_for": "2026" | "",                    # shown as "Figures for 2026"
  "key_points": ["4-6 one-line takeaways"],
  "sections": [{"id": "kebab-id", "heading": "Heading", "html": "<p>...</p>"}],
  "cta_heading": "...", "cta_text": "...",
  "sources": [{"title": "...", "url": "https://..."}]
}
Section html may use p, h3, ul, ol, li, strong, em, a, br, table parts and <div class="callout">.

The script writes public/guides/<slug>.html for every JSON guide, regenerates public/guides/index.html
(which also lists hand-written guides already in public/guides/) and the guide entries in
public/sitemap.xml. Afterwards run `python3 tools/publish_article.py --rebuild` so News search
picks up the guides.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_article import (HEAD, FOOT, PUBLIC, SITE, esc, nice_date, is_official, sorted_sources,  # noqa: E402
                             replace_block, plain_text)

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "guides"
GUIDES = PUBLIC / "guides"
ALLOWED = {"p", "h3", "ul", "ol", "li", "strong", "em", "a", "br", "table", "thead", "tbody", "tr", "th", "td", "div"}
FORM_LINK = {"individuals": ("/t1-form.html", "Start your T1 form"),
             "business": ("/business-setup-form.html", "Business setup form")}


def fail(msg):
    sys.exit(f"ERROR: {msg}")


def guides_head(**kw):
    head = HEAD.format(**kw)
    return head.replace('<a href="/news/" aria-current="page">News</a>\n      <a href="/guides/">Guides</a>',
                        '<a href="/news/">News</a>\n      <a href="/guides/" aria-current="page">Guides</a>')


def validate(g, name):
    for key in ("slug", "title", "seo_title", "description", "topic", "audience", "updated", "lead",
                "key_points", "sections", "cta_heading", "cta_text", "sources"):
        if not g.get(key):
            fail(f"{name}: missing '{key}'")
    if g["audience"] not in FORM_LINK:
        fail(f"{name}: audience must be 'individuals' or 'business'")
    for s in g["sections"]:
        tags = {t.lower() for t in re.findall(r"</?\s*([a-zA-Z0-9]+)", s["html"])}
        if tags - ALLOWED:
            fail(f"{name}: section '{s['id']}' uses tags that aren't allowed: {sorted(tags - ALLOWED)}")
        if re.search(r"<\s*(script|style|iframe)|on[a-z]+\s*=|javascript:|style\s*=", s["html"], re.I):
            fail(f"{name}: section '{s['id']}' has scripts, styles or event handlers")
        for cls in re.findall(r'class="([^"]*)"', s["html"]):
            if cls != "callout":
                fail(f"{name}: only class=\"callout\" is allowed (found '{cls}')")
    if not any(is_official(s["url"]) for s in g["sources"]):
        fail(f"{name}: at least one official source is required")


def section_html(html):
    # Wrap tables so they scroll sideways on phones; open outside links in a new tab.
    html = re.sub(r"<table>", '<div class="table-scroll guide-table"><table>', html)
    html = html.replace("</table>", "</table></div>")
    html = re.sub(r'<a href="(https?://[^"]+)"(?![^>]*target=)', r'<a href="\1" rel="noopener" target="_blank"', html)
    return html


def guide_page(g):
    url = f"{SITE}/guides/{g['slug']}.html"
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": g["title"],
          "description": g["description"], "datePublished": g.get("published", g["updated"]),
          "dateModified": g["updated"],
          "author": {"@type": "Organization", "name": "Calcitax Advisors"},
          "publisher": {"@type": "Organization", "name": "Calcitax Advisors", "url": SITE + "/"},
          "mainEntityOfPage": url}
    extra = (f'<meta name="calcitax:audience" content="{g["audience"]}">\n'
             '<script type="application/ld+json">\n' + json.dumps(ld, indent=2).replace("</", "<\\/") + "\n</script>\n")
    toc = "\n".join(f'        <li><a href="#{esc(s["id"])}">{esc(s["heading"])}</a></li>' for s in g["sections"])
    keys = "\n".join(f"          <li>{esc(k)}</li>" for k in g["key_points"])
    body = "\n\n".join(f'      <h2 id="{esc(s["id"])}">{esc(s["heading"])}</h2>\n{section_html(s["html"])}'
                       for s in g["sections"])
    sources = "\n".join(
        f'        <li>{"<span class=\"src-badge\">Official</span> " if is_official(s["url"]) else ""}'
        f'<a href="{esc(s["url"])}" rel="noopener" target="_blank">{esc(s["title"])}</a></li>'
        for s in sorted_sources(g["sources"]))
    figures = f" · Figures for {esc(g['figures_for'])}" if g.get("figures_for") else ""
    form_href, form_label = FORM_LINK[g["audience"]]
    return (guides_head(title=esc(g["seo_title"]) + " | Calcitax Advisors", description=esc(g["description"]),
                        url=url, og_type="article", og_title=esc(g["title"]), extra_head=extra)
            + f"""
<main id="main">

<article>
<header class="page-hero article-hero">
  <div class="wrap narrow">
    <p class="eyebrow"><a href="/guides/">Guides</a> · {esc(g['topic'])}</p>
    <h1>{esc(g['title'])}</h1>
    <p class="lead">{esc(g['lead'])}</p>
    <p class="news-meta">By Calcitax Advisors · Updated <time datetime="{g['updated']}">{nice_date(g['updated'])}</time>{figures}</p>
  </div>
</header>

<div class="section article-section">
  <div class="wrap narrow">

    <div class="key-box">
      <p class="key-title">In short</p>
      <ul>
{keys}
      </ul>
    </div>

    <nav class="toc" aria-label="On this page">
      <p class="toc-title">On this page</p>
      <ol>
{toc}
      </ol>
    </nav>

    <div class="prose article-body guide-body">
{body}
    </div>

    <aside class="article-cta">
      <h2>{esc(g['cta_heading'])}</h2>
      <p>{esc(g['cta_text'])}</p>
      <div class="btn-row">
        <a class="btn btn-primary" href="/contact.html">Book a free consultation</a>
        <a class="btn btn-secondary" href="{form_href}">{form_label}</a>
      </div>
    </aside>

    <div class="article-sources">
      <h2>Sources</h2>
      <p class="src-note">Official government pages are listed first. Click any link to read the original.</p>
      <ul>
{sources}
      </ul>
    </div>
    <p class="notice">This guide is general information based on sources checked on {nice_date(g['updated'])}. It isn't tax, legal or financial advice for your situation. Rules and figures change, so contact us before making decisions.</p>

  </div>
</div>
</article>

</main>
""" + FOOT.format(year=g["updated"][:4]))


def read_guide_meta(path):
    """Card details for any guide page in public/guides/, generated or hand-written."""
    page = path.read_text()
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', page)
    topic = re.search(r'<p class="eyebrow"><a href="/guides/">Guides</a> · (.*?)</p>', page)
    upd = re.search(r'Updated <time datetime="(\d{4}-\d{2}-\d{2})"', page)
    aud = re.search(r'<meta name="calcitax:audience" content="(\w+)"', page)
    return {"href": f"/guides/{path.name}", "title": plain_text(h1.group(1)) if h1 else path.stem,
            "description": desc.group(1) if desc else "", "topic": plain_text(topic.group(1)) if topic else "Guide",
            "updated": upd.group(1) if upd else "", "audience": aud.group(1) if aud else "individuals"}


def index_card(m):
    upd = f' · <time datetime="{m["updated"]}">Updated {nice_date(m["updated"])}</time>' if m["updated"] else ""
    return f"""      <a class="card news-card" href="{m['href']}">
        <p class="news-meta"><span>{esc(m['topic'])}</span>{upd}</p>
        <h3>{esc(m['title'])}</h3>
        <p>{m['description']}</p>
        <span class="more">Read the guide →</span>
      </a>"""


def guides_index(metas):
    def group(aud, heading, hid):
        items = [m for m in metas if m["audience"] == aud]
        if not items:
            return ""
        return (f'<section class="section{" tint" if aud == "business" else ""}" aria-labelledby="{hid}">\n  <div class="wrap">\n'
                f'    <h2 class="h2" id="{hid}">{heading}</h2>\n    <div class="grid-3 news-grid">\n'
                + "\n".join(index_card(m) for m in items) + "\n    </div>\n  </div>\n</section>\n")
    return (guides_head(title="Guides: Tax &amp; Savings Explained | Calcitax Advisors",
                        description="Plain-language guides from Calcitax Advisors on Canadian tax, savings accounts and running a small business.",
                        url=f"{SITE}/guides/", og_type="website", og_title="Guides | Calcitax Advisors", extra_head="")
            + """
<main id="main">

<section class="page-hero">
  <div class="wrap">
    <p class="eyebrow">Guides</p>
    <h1>Tax &amp; savings, explained</h1>
    <p class="lead">In-depth, plain-language guides to help you make better decisions about your taxes, savings and business. For the latest updates, see our <a href="/news/">news</a>.</p>
  </div>
</section>

""" + group("individuals", "For individuals and families", "for-individuals")
            + group("business", "For small businesses", "for-business") + """
</main>
""" + FOOT.format(year=max((m["updated"] for m in metas if m["updated"]), default="2026")[:4]))


def main():
    built = []
    for path in sorted(CONTENT.glob("*.json")):
        g = json.loads(path.read_text())
        validate(g, path.name)
        (GUIDES / f"{g['slug']}.html").write_text(guide_page(g))
        built.append(g["slug"])
    pages = [p for p in sorted(GUIDES.glob("*.html")) if p.name != "index.html"]
    metas = [read_guide_meta(p) for p in pages]
    metas.sort(key=lambda m: (m["updated"], m["title"]), reverse=False)
    order = {"rrsp-tfsa-fhsa.html": 0}
    metas.sort(key=lambda m: order.get(Path(m["href"]).name, 1))
    (GUIDES / "index.html").write_text(guides_index(metas))

    sitemap = PUBLIC / "sitemap.xml"
    last = max((m["updated"] for m in metas if m["updated"]), default="")
    entries = [f"  <url><loc>{SITE}/guides/</loc><lastmod>{last}</lastmod></url>"]
    entries += [f"  <url><loc>{SITE}{m['href']}</loc><lastmod>{m['updated']}</lastmod></url>" for m in metas]
    sitemap.write_text(replace_block(sitemap.read_text(), "<!-- GUIDES:START -->", "<!-- GUIDES:END -->",
                                     "\n" + "\n".join(entries) + "\n  ", sitemap))
    print(f"OK: built {len(built)} guide(s); index lists {len(metas)}.")


if __name__ == "__main__":
    main()
