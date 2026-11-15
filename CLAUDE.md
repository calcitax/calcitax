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

**Rebates, grants and incentives (create awareness).** Government money people can claim is a core
topic, not filler. Treat a new or changed federal, B.C. or utility incentive (for example heat pump and
home-energy rebates, CleanBC/BC Hydro/FortisBC programs, benefit top-ups, small-business grants, hiring
credits) as priority-1 news. Also cover incentives that are **upcoming** (announced, portal not yet open)
and ones **closing soon** (a deadline in the next 30 days). Always state: who qualifies, how much,
key dates (start, retroactive date, deadline), how to apply, what records to keep, whether it stacks
with other programs (only if a source says so), and any tax effect (for example a rebate on rental
property reduces its capital cost). Use the category "Rebates & incentives". When an incentive article
is more than 60 days old and the program has changed, publish an update that links the earlier one.

**Questions from clients and visitors.** Questions people send to Calcitax are a strong signal of what
others are searching for. If a recent question (passed on by Varun or Priyanka) isn't already covered,
it moves to the top of the topic list for news (if it's about something current) or the guide backlog
(if it's evergreen). Never name or identify the person who asked.
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
Payroll, GST/HST, Newcomers, Accounting, Rebates & incentives.

**Slug.** Lowercase words joined by hyphens, describing the topic, ending with month and year,
for example `bank-of-canada-raises-rate-october-2026`.

## Services page reading lists

Each service on `public/services.html` has an auto-generated "Helpful reading" list (guides first, then
the newest matching news from the last 180 days). `tools/build_service_links.py` refreshes it and runs
automatically at the end of `build_guides.py` and `publish_article.py`. Never hand-edit the lists
between the `<!-- READING:... -->` markers; to link a new kind of article to a service, add a keyword
or category to `SERVICES` in that script.

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
- Bookkeeping and record-keeping basics for small businesses
- B.C. business licences, registrations and the transparency register for private companies
