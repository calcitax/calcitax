#!/usr/bin/env python3
"""Refresh the "Helpful reading" lists under each service on public/services.html.

Usage:
    python3 tools/build_service_links.py

Runs automatically at the end of tools/build_guides.py and tools/publish_article.py, so the lists
stay current whenever a guide or news article is added. You normally never run it by hand.

How links are chosen: each service in SERVICES below has keywords (matched against a guide's or
article's slug, title and topic, lower-case) and news categories. Matching guides are listed first,
then the newest matching news articles from the last NEWS_MAX_AGE_DAYS days.
To link a new kind of content to a service, add a keyword or category here, not in the HTML.
The list on the page sits between <!-- READING:<id>:START --> and <!-- READING:<id>:END --> markers.
"""
import datetime as dt
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SERVICES_PAGE = PUBLIC / "services.html"
NEWS = ROOT / "content" / "news.json"

MAX_GUIDES = 5
MAX_NEWS = 4
NEWS_MAX_AGE_DAYS = 180

# id on services.html -> (heading, keywords, news categories)
SERVICES = {
    "personal": ("Helpful reading for personal tax (T1)",
                 ["rrsp", "tfsa", "fhsa", "credit", "child-benefit", "family-benefit", "resp", "rdsp",
                  "retirement", "oas", "rrif", "instalment", "capital-gains", "separation", "divorce",
                  "pre-filled", "tax-deadline", "what-it-means-for-you", "benefit-payment",
                  "year-end-tax-checklist", "foreign-income", "heat-pump", "rebate"],
                 ["Personal tax", "Rebates & incentives"]),
    "self-employed": ("Helpful reading for self-employed people and landlords",
                      ["self-employed", "t2125", "gig", "ride-share", "rental", "instalment",
                       "sole-proprietor", "gst"],
                      []),
    "corporate": ("Helpful reading for corporations (T2)",
                  ["corporation", "paying-yourself", "incorporation", "mega-deduction", "small-businesses",
                   "prescribed-interest", "tariff"],
                  ["Business tax"]),
    "trusts": ("Helpful reading for trusts and estates (T3)",
               ["final-return", "estate", "trust", "capital-gains"],
               []),
    "t5": ("Helpful reading on dividends and interest",
           ["dividend", "paying-yourself", "prescribed-interest"],
           []),
    "business-setup": ("Helpful reading for starting a business",
                       ["incorporation", "sole-proprietor", "worksafebc", "registration", "licence",
                        "gst-hst-pst", "hiring-first-employee"],
                       []),
    "bookkeeping": ("Helpful reading on bookkeeping",
                    ["bookkeeping", "record-keeping", "self-employed-expenses", "small-businesses",
                     "mega-deduction"],
                    ["Accounting"]),
    "payroll": ("Helpful reading on payroll",
                ["payroll", "hiring", "worksafebc", "t4a", "cpp-ei", "employee"],
                ["Payroll"]),
    "gst": ("Helpful reading on GST/HST and PST",
            ["gst", "hst", "pst", "ride-share"],
            ["GST/HST"]),
    "newcomers": ("Helpful reading for newcomers",
                  ["newcomer", "international-students", "work-permit", "foreign-income", "leaving-canada",
                   "moving-from-canada", "child-benefit"],
                  ["Newcomers"]),
    "cra": ("Helpful reading on CRA letters and late returns",
            ["cra-letters", "audit", "instalment", "prescribed-interest", "pre-filled"],
            ["CRA updates"]),
}


def esc(s):
    return html.escape(str(s), quote=True)


def text(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def guide_metas():
    out = []
    for p in sorted((PUBLIC / "guides").glob("*.html")):
        if p.name == "index.html":
            continue
        page = p.read_text(encoding="utf-8")
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
        topic = re.search(r'<p class="eyebrow"><a href="/guides/">Guides</a> · (.*?)</p>', page)
        title = text(h1.group(1)) if h1 else p.stem
        out.append({"href": f"/guides/{p.name}", "title": title,
                    "hay": f"{p.stem} {title} {text(topic.group(1)) if topic else ''}".lower()})
    return out


def news_items():
    if not NEWS.exists():
        return []
    cutoff = dt.date.today() - dt.timedelta(days=NEWS_MAX_AGE_DAYS)
    items = []
    for a in json.loads(NEWS.read_text(encoding="utf-8")):
        if dt.date.fromisoformat(a["date"]) < cutoff:
            continue
        items.append({"href": f"/news/{a['slug']}.html", "title": a["title"], "date": a["date"],
                      "category": a["category"], "hay": f"{a['slug']} {a['title']}".lower()})
    items.sort(key=lambda x: x["date"], reverse=True)
    return items


def matches(item, keywords, categories):
    return item.get("category") in categories or any(k in item["hay"] for k in keywords)


def block(heading, guides, news):
    if not guides and not news:
        return "\n"
    lis = [f'            <li><a href="{g["href"]}">{esc(g["title"])}</a> <span class="read-tag">Guide</span></li>'
           for g in guides]
    lis += [f'            <li><a href="{n["href"]}">{esc(n["title"])}</a> <span class="read-tag news">News</span></li>'
            for n in news]
    return ("\n          <div class=\"svc-reading\">\n"
            f"            <h3>{esc(heading)}</h3>\n"
            "            <ul>\n" + "\n".join("  " + li for li in lis) + "\n            </ul>\n          </div>\n          ")


def main():
    page = SERVICES_PAGE.read_text(encoding="utf-8")
    guides, news = guide_metas(), news_items()
    filled = 0
    for sid, (heading, kws, cats) in SERVICES.items():
        start, end = f"<!-- READING:{sid}:START -->", f"<!-- READING:{sid}:END -->"
        pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
        if not pat.search(page):
            continue
        rank = lambda x: min((i for i, k in enumerate(kws) if k in x["hay"]), default=len(kws))
        g = sorted((x for x in guides if matches(x, kws, [])), key=rank)[:MAX_GUIDES]
        n = [x for x in news if matches(x, kws, cats)][:MAX_NEWS]
        page = pat.sub(lambda _m: start + block(heading, g, n) + end, page)
        filled += bool(g or n)
    SERVICES_PAGE.write_text(page, encoding="utf-8")
    print(f"OK: services page reading lists refreshed ({filled} service(s) with links).")


if __name__ == "__main__":
    main()
