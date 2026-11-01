# Calcitax Advisors website (calcitax.com)

Static site in `public/` served by a Cloudflare Worker (`src/worker.js`, `wrangler.jsonc`).
Every push to `main` deploys automatically through Cloudflare's Git integration (about 1-2 minutes).
The site belongs to Calcitax Advisors, a small accounting and tax practice in Surrey, BC,
run by Varun Arora and Priyanka Puri (both qualified Chartered Accountants in India, ICAI).

Do not change the forms, the Worker or other pages unless the task asks for it.

## Publishing a news article

1. Write the article as JSON (see the docstring in `tools/publish_article.py` for the format)
   in a scratch location outside `public/`.
2. Run `python3 tools/publish_article.py path/to/article.json`. It validates the article and
   regenerates `public/news/`, the RSS feed, the home page "Latest news" block and the sitemap.
   Never hand-edit those generated files; change `content/news.json` and run `--rebuild` instead.
3. Commit with a clear message and push to `main`.
4. After 2-3 minutes, confirm `https://calcitax.com/news/<slug>.html` returns the new article.

## Editorial rules (these matter: articles go out under the firm's name)

**Audience.** Individuals, families, newcomers and small-business owners in Metro Vancouver.
Plain, friendly Canadian English. Explain jargon. No hype, no clickbait.

**Topic choice, in priority order.**
1. News from the last few days that changes something for Canadian taxpayers or small businesses:
   CRA announcements, federal or BC budget and tax measures, Bank of Canada decisions,
   inflation or jobs data that affects borrowers, new limits (TFSA, RRSP, CPP, EI), deadlines.
2. Major world finance or accounting news only when it clearly affects Canadians
   (for example US tariffs, global rates, IFRS or accounting-standard changes for businesses).
3. If nothing new and solid happened, write a timely, evergreen piece tied to the calendar
   (an upcoming deadline, year-end planning, an often-missed credit). Never pad or invent news.
Check `content/news.json` first and don't repeat a topic covered in the last 14 days unless
there is a genuinely new development (then say what changed and link the earlier article).

**Accuracy.**
- Every fact, number, rate, limit and date must come from a source you actually read today.
  Prefer primary sources: canada.ca (CRA, Finance Canada), bankofcanada.ca, statcan.gc.ca,
  gov.bc.ca, laws-lois.justice.gc.ca, then reputable news outlets.
- If sources disagree or a measure is only proposed (not law yet), say so plainly
  ("proposed", "announced but not yet passed").
- Never guess figures. If you can't confirm something, leave it out.
- No personalised investment advice and no predictions presented as fact.

**Originality and copyright.** Write in your own words. No copying of sentences from sources;
at most one short quotation (under 15 words) per article, in quotation marks with attribution.
List every source used in `sources` with its real URL. At least one source must be an official government
page (canada.ca, bankofcanada.ca, statcan.gc.ca, gov.bc.ca and similar); the publishing tool
rejects articles without one and labels official links on the page.

**Shape.** 500-900 words. A headline that says what happened (max ~90 characters).
`description` is one or two sentences (max 160 characters). Structure:
- an opening paragraph with the news in one or two sentences,
- `<h2>` sections such as "What happened", "What it means for you",
  "What it means for small businesses", "What to do now" (use the ones that fit),
- short paragraphs and bullet lists; dates written like "March 2, 2027".
Do not add a disclaimer or contact box in the body: the template adds both.

**Categories.** Use one of: Personal tax, Business tax, CRA updates, Economy, Deadlines,
Payroll, GST/HST, Newcomers, Accounting.

**Slug.** Lowercase words joined by hyphens, describing the topic, ending with month and year,
for example `bank-of-canada-raises-rate-october-2026`.
