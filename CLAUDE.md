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
   regenerates `public/news/` (including the `search.json` index used by the News page search), the RSS feed, the home page "Latest news" block and the sitemap.
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

## Guides

Evergreen guides live in `content/guides/<slug>.json` (format in the docstring of `tools/build_guides.py`).
After adding or editing one, run `python3 tools/build_guides.py` (it also refreshes the six newest guides on the home page) and then
`python3 tools/publish_article.py --rebuild` (so News search includes it). The same accuracy and
originality rules as news apply; set `updated` to the date the content was re-checked.

**Guide shape.** 1,300-2,200 words in 5-9 sections, written for a Grade 8 reading level, with every
term explained the first time it appears. Include 4-6 `key_points`, 1-3 `<div class="callout">` tips or warnings, a table
only where a comparison really helps, and a closing "Checklist" or "Common mistakes" section.
`audience` is `individuals` or `business`. Year-specific figures must name the year, and `figures_for`
says which year. Simple made-up examples are fine if they use round numbers and are clearly illustrations.
Link to related guides with relative links (`/guides/<slug>.html`) where helpful.

**Choosing a guide topic.** Check `content/guides/` first and never duplicate a guide. Pick the backlog
topic people are most likely searching for right now: the backlog below is ordered by estimated
Google search demand in Canada, but move a topic up when it is seasonal (for example T4A/T5018 slips in
January-February, tax filing and benefits topics in February-April, RRSP and year-end planning in
November-February). If a keyword-research connector (such as Semrush, Ahrefs or Ubersuggest) is
available in the run, use its Canadian search volumes to confirm the order. A topic suggested by current
news can also jump the queue. Remove the chosen topic from the backlog in the same commit. If the backlog
is empty, refresh the guide with the oldest `updated` date instead: re-check every figure against
today's sources and update it.

**News tie-breaker.** When two news topics are equally solid and new, choose the one more people are
likely to search for (benefit payments, CPP/OAS, TFSA/RRSP limits and deadlines usually draw the most).

**Guide backlog** (ordered by estimated search demand, highest first):
- Retirement income: OAS, CPP, RRIFs and pension splitting
- RESPs and education grants for your children
- International students and work-permit holders: taxes and benefits
- Gig and ride-share drivers: income, GST and expenses
- Income from India (or abroad) while living in Canada: foreign income, foreign tax credits, T1135
- Paying yourself from your corporation: salary, dividends and shareholder loans
- Tax instalments for individuals: who pays and when
- Dealing with CRA letters, reviews and audits
- Hiring contractors: T4A, T5018 and contractor vs employee
- Separation and divorce: tax and benefit changes
- When a family member dies: final return and estate basics
- Bookkeeping and record-keeping basics for small businesses
- B.C. business licences, registrations and the transparency register for private companies
