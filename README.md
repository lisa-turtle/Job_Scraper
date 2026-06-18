# 🧪 Job Scraper + Triage Dashboard

GitHub Actions pipelines that scrape job boards (LinkedIn, Indeed, USAJOBS,
NEOGOV, CalOpps, CalCareers) on a schedule, commit the results to the repo, and
surface them in a single filterable [`triage.html`](#interactive-triage-dashboard--triagehtml)
dashboard hosted **free** on GitHub Pages — with a map, salary harmonization,
cross-source de-duplication, save/applied/dismiss triage, and optional phone
notifications. **No server, no paid services, and no API keys required.**

**Everything you search for lives in one file: [`config.json`](config.json)** —
point it at your field and locations (or generate it from your CV with an LLM)
and you have your own tracker. Live example:
[scottcoff.in/Job_Scraper/triage.html](https://scottcoff.in/Job_Scraper/triage.html).

![The triage dashboard in action — filtering, salary distribution, map, and triage](triage.gif)

> This repo ships configured for **environmental / toxicology** roles (Dr. Scott
> Coffin's field — [scottcoff.in](https://scottcoff.in)) as a worked example, and
> began as [Ernesto Diaz](https://github.com/ernestod1998)'s Bay Area ML-engineer
> scraper. The walkthrough below sets up your own copy from scratch.

---

# Set up your own (full walkthrough) 🚀

You only need a free **[GitHub account](https://github.com/signup)**. Everything
runs on GitHub's servers (Actions + Pages) — **you don't have to install anything
or keep a computer on.** (Local install is optional; see [Running locally](#running-locally).)

## Step 1 — Get your own copy of the repo

**Easiest (recommended): "Use this template."**
1. Go to the repository page on GitHub and click the green **Use this template →
   Create a new repository**.
2. Name it (e.g. `job-tracker`), keep it **Public** (GitHub Pages is free for
   public repos), and click **Create repository**.

That's it — you now have your own independent copy with no shared history.

<details>
<summary>Alternative: fork, or clone to your computer</summary>

- **Fork:** click **Fork** at the top of the repo (keeps a link to the original).
- **Clone (for local editing):**
  ```bash
  git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
  cd YOUR-REPO
  ```
  Replace `YOUR-USERNAME/YOUR-REPO` with your repo. You don't need to clone just
  to configure it — you can edit files directly on github.com.
</details>

## Step 2 — Set what you search for (`config.json`)

This is the only file you need to change. Pick one:

**A. Generate it from your CV (no coding).** Open
[`docs/cv-to-config-prompt.md`](docs/cv-to-config-prompt.md), copy the prompt,
and paste it into **[ChatGPT](https://chat.openai.com)**,
**[Claude](https://claude.ai)**, or any chatbot together with your CV and your
target locations. It returns a finished `config.json`. In your repo on GitHub,
open `config.json` → click the **✏️ pencil** → paste → **Commit changes**.

**B. Edit `config.json` by hand.** It's self-documenting. The two things almost
everyone changes:
- `keywords.include` + `search_terms` — **what roles** (job-title words/phrases).
- `locations` — **where** (one entry per place; LinkedIn `geoId` can be left `""`).

Optional knobs: `profile` (dashboard title/subtitle), `keywords.exclude`,
`employers.priority` / `employers.exclude`, `priority_topics` (⭐ highlights),
`role_categories` (the Role-filter buckets). Every key is commented inline in
[`config.json`](config.json).

## Step 3 — Host the dashboard (GitHub Pages)

This publishes `triage.html` at a free public URL.
1. In your repo: **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **Deploy from a branch**.
3. Branch: **`main`**, folder: **`/ (root)`** → **Save**.
4. After ~1 minute your dashboard is live at:
   **`https://YOUR-USERNAME.github.io/YOUR-REPO/triage.html`**

New to Pages? GitHub's 2-minute guide:
[Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).
Want it on a custom domain (like `you.com/jobs`)? See
[Managing a custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site).

## Step 4 — Turn on the scrapers (GitHub Actions)

1. Open the **Actions** tab → click **"I understand my workflows, enable them."**
2. **Settings → Actions → General → Workflow permissions** → select
   **Read and write permissions** → **Save**. (This lets the scrapers commit the
   jobs they find back to your repo.)

## Step 5 — Run it the first time

In the **Actions** tab, open each watcher and click **Run workflow** (afterwards
they run automatically on a schedule):
- **LinkedIn** and **Indeed** watchers (work anywhere).
- **USAJOBS** (US federal). **NEOGOV** / **CalOpps** / **CalCareers** are
  US / California public-sector boards — run them only if relevant, or
  [disable them](#turning-sources-on--off).

Give it 1–2 minutes, then open your `…/triage.html` URL. 🎉 Hard-refresh after
each scrape to see new jobs.

## Step 6 — Phone notifications (optional)

Get a push the moment a relevant new role appears, via
**[Pushover](https://pushover.net)** (a simple, one-time ~$5 app for
[iOS](https://apps.apple.com/us/app/pushover-notifications/id506088175) /
[Android](https://play.google.com/store/apps/details?id=net.superblock.pushover);
the API is free):
1. Sign in at [pushover.net](https://pushover.net), **Create an Application/API
   Token** (any name) → copy the **API Token**. Copy your **User Key** from the
   dashboard home.
2. In your repo: **Settings → Secrets and variables → Actions → New repository
   secret** — add `PUSHOVER_TOKEN` and `PUSHOVER_USER`.
3. Test it: **Actions → Test Pushover Notification → Run workflow** — you should
   get a push within ~20 seconds.
4. (Optional) Add a repository **Variable** `NOTIFY_MIN_FIT` to tune instant
   high-fit pings.
5. (Optional) Add repository **Variable** `WEEKLY_DIGEST_PUSHOVER=true` to receive
   the weekly Pushover brief. You can also set `WEEKLY_DIGEST_DAYS` (default `7`).

Without these secrets, notifications are simply off and everything else works.

## Step 7 — AI résumé fit-scoring (optional, advanced)

`triage_agent.py` can score each role against your résumé with the
**[Claude API](https://www.anthropic.com/api)** (paid, ~pennies/run). It needs an
`ANTHROPIC_API_KEY` secret plus your profile/résumé in secrets. Entirely optional
— leave the `triage.yml` / `evals.yml` workflows **disabled** if you don't use it
(**Actions → workflow → ⋯ → Disable**).

### Turning sources on / off
Each source is a workflow in [`.github/workflows/`](.github/workflows). To stop
one, **Actions → that workflow → ⋯ → Disable workflow**. The dashboard simply
skips any source file that doesn't exist, so nothing breaks.

### Running locally
Optional — only if you want to test scrapes on your own machine. Needs
**[Python 3.11+](https://www.python.org/downloads/)**:
```bash
python scrape_jobs.py --linkedin-only      # standard library only
python scrape_jobs.py --usajobs-only       # standard library only
pip install -r requirements.txt            # only Indeed needs this (python-jobspy)
python scrape_jobs.py --indeed-only
python -m http.server 8000                 # then open http://localhost:8000/triage.html
```
The dashboard must be served over HTTP (the commands above) — opening
`triage.html` from `file://` won't load the data.

---

> **The rest of this README documents how it works**, using the shipped
> environmental / toxicology example. Skim it to customize further; you don't
> need any of it to get running.

## What It Does

> The descriptions below use this repo's shipped example config (environmental /
> toxicology; California, Oregon & Australia). **Your locations, keywords, and
> employers come from [`config.json`](config.json)** — see the
> [walkthrough above](#set-up-your-own-full-walkthrough-).

### 1. Priority-employer digest — daily, last 24h
Hits LinkedIn's public guest endpoint for roles in your configured locations
posted in the last 24 hours, then post-filters to a **priority-employer allowlist**
(`employers.priority` in `config.json`) — in the shipped example, environmental/tox consulting
firms (Ramboll, Exponent, Gradient, ToxStrategies, Tetra Tech, ICF, Integral,
Geosyntec…), research institutes & NGOs (SCCWRP, SFEI, Silent Spring, EDF, NRDC,
EWG, Health Effects Institute, RTI, Battelle…), agencies (US EPA, CalEPA/OEHHA,
State Water Board, CARB, DTSC, NIEHS…), water utilities, universities, and
product-safety teams in industry. Add to that list to expand coverage.

Output goes to `jobs.json`, `jobs.md`, and `jobs.html`. Each run dedupes against
the previously-committed `jobs.json`, so the output surfaces only postings new
since the last run.

> A direct-ATS probe path (`CURATED_BIOTECHS`) also exists but is **empty by
> default** — environmental/tox employers overwhelmingly use iCIMS/Taleo/
> SuccessFactors rather than the public Greenhouse/Workday JSON endpoints the
> original biotech version relied on. The LinkedIn + Indeed keyword watchers
> (which need no employer slug) are the primary sources.

### 2. LinkedIn watcher — hourly, last 1h
Hits LinkedIn's public guest endpoint for roles in your configured locations
posted in the last hour across your `search_terms`, dedupes by job ID, and sorts by recency.
Output goes to `linkedin_jobs.json`, `linkedin_jobs.md`, and `linkedin_jobs.html`.

Runs hourly at :17 PT (8am–8pm) via native GitHub cron, with the in-repo
watchdog (`linkedin_watch_backup.yml` at :33) re-dispatching missed slots. A
block guard preserves the previous results when LinkedIn returns zero cards
across every term (rate-limited run).

> ⚠️ Uses the unauthenticated public guest endpoint only — **never** signs in
> with a user account and does not use LinkedIn cookies, tokens, or credentials.

### 3. Indeed watcher — hourly, last 24h
Uses [`python-jobspy`](https://pypi.org/project/python-jobspy/) (Indeed's RSS and
Publisher API were deprecated in 2026 and the site sits behind Cloudflare;
JobSpy uses Indeed's mobile-app API internally). Searches your configured
locations. Output goes
to `indeed_jobs.json`, `indeed_jobs.md`, and `indeed_jobs.html`, deduped against
the previous run. Runs at :47 PT, offset from LinkedIn's :17 slot.

## Keywords Matched

A title is included if it contains any of these (case-insensitive). Multi-word
phrases match as substrings; single tokens are word-bounded (so list full words).
Full list lives in `KEYWORDS` in `scrape_jobs.py`:

**Toxicology:** `toxicologist`, `toxicology`, `ecotoxicologist`, `environmental
toxicolog`, `regulatory toxicolog`, `computational toxicolog`, `aquatic
toxicolog`, `research toxicolog`

**Risk / exposure / hazard:** `risk assess`, `risk assessor`, `human health
risk`, `ecological risk`, `exposure scien`, `exposure assess`, `hazard assess`,
`dose-response`, `pharmacokinetic`, `toxicokinetic`

**Environmental science / health / chemistry:** `environmental scien`,
`environmental health`, `environmental chemist`, `environmental engineer`,
`environmental epidemiolog`, `public health`, `epidemiologist`

**Water / contaminants:** `water quality`, `water resources`, `drinking water`,
`microplastic`, `nanoplastic`, `pfas`, `emerging contaminant`, `contaminant`,
`pollution`, `remediation`

**Chemical safety / regulatory / stewardship:** `chemical safety`, `chemical
risk`, `chemical assess`, `chemical regulatory`, `product steward`

The list is deliberately **tight** for precision: generic titles (`research
scientist`, `senior scientist`, `data scientist`, `professor`, `regulatory
affairs`) are *not* matched on their own, because they pull in pharma / biotech /
tech bench roles. Environmental academic, data, and policy roles are still caught
via their qualified forms (`Environmental Data Scientist`, `Assistant Professor
of Environmental Health`, etc.).

**Excluded everywhere:**
- **Junior / training:** `intern`, `internship`, `co-op`, `trainee`,
  `apprentice`, `technician`, `research/lab/teaching assistant`, `undergraduate`,
  `postdoc`, `work-study`, `volunteer`, `fellowship`. (Unlike the original, which
  dropped *senior* titles — Dr. Coffin is a senior IC, so senior / principal /
  lead / director roles are **kept**.)
- **EHS / workplace-safety compliance:** `EHS`, `health & safety`, `occupational
  safety/health` — a distinct field from environmental-tox science. (Does *not*
  touch `Chemical Safety`, which is in-scope.)

## Geographic Scope

**You define the locations** in [`config.json`](config.json) → `locations` (no
code edits). The shipped example searches California, Portland & Bend OR, and
Australia, but it works for anywhere — add/remove entries to suit:

- **LinkedIn** — `locations.linkedin`: each is a `location` + LinkedIn `geoId`.
  Leave `geoId` blank to let LinkedIn resolve the text (works for most
  cities/metros), or fill in the numeric id for tighter filtering. A geoId
  reference table is in [`docs/cv-to-config-prompt.md`](docs/cv-to-config-prompt.md).
- **Indeed** — `locations.indeed`: each is a `location` + `country` (`USA` →
  indeed.com, `Australia` → au.indeed.com, `GB`, `Canada`, …).
- **USAJOBS** is nationwide US (federal); **NEOGOV** is filtered to your
  configured locations; **CalCareers** and **CalOpps** are California-only boards
  by nature (disable them if you're not searching California).
- The map and dashboard auto-fit to wherever your jobs are.

## Output Files

| File | Source | Description |
|---|---|---|
| `jobs.json` / `.md` / `.html` | Priority-employer digest | Allowlisted env/tox employer roles, last 24h, deduped against the previous run |
| `linkedin_jobs.json` / `.md` / `.html` | LinkedIn watcher | Roles in your configured locations, last 1h, deduped |
| `indeed_jobs.json` / `.md` / `.html` | Indeed watcher | Indeed-sourced roles in your locations, last 24h, deduped |
| `calcareers_jobs.json` / `.md` / `.html` | CalCareers watcher | California state civil-service roles (calcareers.ca.gov) |
| `usajobs_jobs.json` / `.md` / `.html` | USAJOBS watcher | Federal roles with salary (EPA, NOAA, USGS, FDA, NIEHS…) via usajobs.gov |
| `governmentjobs_jobs.json` / `.md` / `.html` | NEOGOV watcher | CA/OR state & local-gov roles (air & water districts, county env health) via governmentjobs.com |
| `calopps_jobs.json` / `.md` / `.html` | CalOpps watcher | California local-agency roles (cities, counties, special districts) via calopps.org |
| `all_jobs.json` | accumulator | Cumulative 14-day master (feeds the dashboard + triage) |
| `scores.json` | triage agent | Optional fit verdicts keyed by job URL |

### CalCareers (California state jobs)

`scrape_jobs.py --calcareers-only` scrapes [calcareers.ca.gov](https://calcareers.ca.gov)
— the CA state civil-service portal where OEHHA, DTSC, CARB, the Water Boards,
Fish & Wildlife, and Caltrans post scientist roles. CalCareers is an ASP.NET
WebForms site with **no public API**, so the scraper seeds a session and fires
the search postback (`__EVENTTARGET=ctl00$cphMainContent$btnSearch` with the
keyword field), then parses the labeled result cards. The working postback
method was adapted from the [OpenPostings](https://github.com/Masterjx9/OpenPostings)
`calcareers` module. Fully guarded; runs daily via `calcareers_watch.yml`.
Verified returning real roles (Water Board, Fish & Wildlife, OEHHA, DTSC…).

### USAJOBS (federal jobs)

`scrape_jobs.py --usajobs-only` scrapes [usajobs.gov](https://www.usajobs.gov) —
federal env/tox roles at EPA, NOAA, USGS, FDA, NIEHS, CDC, DOI, etc., **with
salary**. It uses the site's public search endpoint (`/Search/ExecuteSearch`),
so **no API key is required**: it seeds a session, then POSTs each keyword and
keeps titles that pass the env/tox filter. Runs daily via `usajobs_watch.yml`.
Federal roles are nationwide; use the dashboard's location filter/map to focus.

> Source identified from the [OpenPostings](https://github.com/Masterjx9/OpenPostings)
> project's catalog of 80+ ATS providers. OpenPostings is a self-hosted
> aggregator (not a hosted API), so rather than depend on it we query the
> official USAJOBS public endpoint directly.

### NEOGOV & CalOpps (state & local government)

Also added from the OpenPostings catalog — the boards that carry county/city
environmental roles LinkedIn and Indeed miss:

- **`--governmentjobs-only`** ([governmentjobs.com](https://www.governmentjobs.com) /
  NEOGOV) — state & local agencies nationwide; keyword-searched and **filtered to
  CA/OR**. Surfaces e.g. air-district Air Quality Specialists, county Hazardous
  Materials Specialists, water-district roles.
- **`--calopps-only`** ([calopps.org](https://www.calopps.org)) — California
  local agencies (cities, counties, special & water districts). CA-only board, so
  it's title-filtered only (e.g. Water Resources Specialist, Environmental Health
  Specialist).

Both are HTML scrapes (no API), fully guarded, and run daily via
`localgov_watch.yml`. Local-gov env roles are sparse, so yield is low but
high-signal — they catch the occasional perfect agency role that the big boards
don't list.

### Dashboard features

The `triage.html` cockpit adds, on top of the source/role/seniority/date filters:

- **★ Priority topics** — roles touching signature topics (microplastics,
  ecotoxicology, endocrine-disrupting chemicals, R/Shiny) get a gold ★ and a
  highlighted card; a toggle filters to just those. Edit `STAR_TERMS` in
  `triage.html` to change what's flagged.
- **Cross-source de-dup** — the same role cross-posted to LinkedIn and Indeed
  collapses into one card (matched on title + location + compatible company),
  showing both source badges; triage applies to all copies at once.
- **★ Best fit** view — ranks roles by match to Dr. Coffin's specializations
  (microplastics, ecotoxicology, risk assessment, exposure, QSAR, PFAS,
  drinking water, computational tox…). Weights live in `FIT_TERMS` in
  `triage.html`; every card shows a 0–100 fit chip.
- **🚫 Not relevant** button — hides a role *and* learns from it: titles sharing
  distinctive words with your "not relevant" marks are down-ranked in Best fit.
- **Salary slider** — harmonizes inconsistent pay formats (hourly, monthly,
  yearly, `$k` ranges, title-embedded) to an annual figure, then filters by a
  minimum, with an "include unlisted" toggle.
- **🗺 Map** view — Leaflet map of roles by city (client-side geocoding, no API
  key) that auto-fits to wherever your jobs are; hover a dot for the location,
  click for the roles. Remote/unknown roles cluster at a default center.

### Interactive triage dashboard — `triage.html`

A single-file dashboard hosted on GitHub Pages that merges the latest source
JSONs into one filterable cockpit: search; source / role / seniority filters
(roles classified as Toxicology, Risk/Exposure, Water, Contaminants,
Environmental Health, Environmental Science, Policy/Regulatory, Data Science,
Academic); save / applied / dismiss buttons persisted in localStorage; top-
companies and role-mix charts; and an "export saved as Claude prompt" action.

**View it (after enabling Pages — see Deployment):**
`https://scottcoffin.github.io/Job_Scraper/triage.html`

The dashboard fetches the JSON files from the same repo at view time, so it
always reflects the latest committed scrape. To run locally:
```bash
python -m http.server 8000
# then visit http://localhost:8000/triage.html
```
Opening from `file://` won't work — the dashboard needs same-origin HTTP to
`fetch()` the source JSONs.

## Reference: commands & options

### Run a source manually

From the **Actions** tab → *Run workflow* on any watcher, or locally:
```bash
python scrape_jobs.py --biotech-only         # priority-employer digest (allowlist)
python scrape_jobs.py --linkedin-only        # general LinkedIn, last 1h
python scrape_jobs.py --indeed-only          # general Indeed, last 24h
python scrape_jobs.py --usajobs-only         # US federal jobs (usajobs.gov, no API key)
python scrape_jobs.py --governmentjobs-only  # state/local gov (NEOGOV)
python scrape_jobs.py --calopps-only         # California local agencies (calopps.org)
python scrape_jobs.py --calcareers-only      # California state jobs (calcareers.ca.gov)
```
The LinkedIn / priority / USAJOBS / gov pipelines use only the **Python standard
library**. Only Indeed needs a dependency: `pip install -r requirements.txt`
(single package, `python-jobspy`).

### 📲 Phone notifications (Pushover)

> Quick setup is in the [walkthrough Step 6](#step-6--phone-notifications-optional);
> this is the detail.

Get a push to your phone the moment a **highly-relevant** new role appears. After
each scrape, `notify.py` pushes any new posting that either touches a priority
topic (microplastics, ecotoxicology, endocrine-disrupting chemicals, R/Shiny) or
scores ≥ `NOTIFY_MIN_FIT` (default 75) on the resume-fit model. It dedupes
against `notified.json`, so the same role is never pushed twice (across sources
or runs). Priority-topic hits ping at high priority.

To enable, add these in **Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `PUSHOVER_TOKEN` | Your Pushover **application/API token** (create an app at pushover.net) |
| `PUSHOVER_USER` | Your Pushover **user key** (top of your pushover.net dashboard) |

Optional **Variable** (not secret): `NOTIFY_MIN_FIT` — lower than 75 for more
(less selective) pings, higher for fewer. Without the two secrets, notifications
are simply off (everything else still works).

Weekly brief: the `Weekly Job Digest` workflow runs Monday morning and is off by
default. To opt in, add repository **Variable** `WEEKLY_DIGEST_PUSHOVER=true`.
The brief reads `all_jobs.json` for roles first seen in the last 7 days, groups
them by salary band and organization, and includes a few standouts ranked by
`scores.json` when the optional triage agent has run. If `scores.json` is absent,
it falls back to the same deterministic resume-fit scorer used for instant
Pushover alerts, so no LLM is required. Optional variables:

| Variable | Value |
|---|---|
| `WEEKLY_DIGEST_PUSHOVER` | `true` to enable the scheduled weekly brief |
| `WEEKLY_DIGEST_DAYS` | Lookback window; default `7` |
| `DASHBOARD_URL` | Override the link attached to the push |

**Test it** (sends one push to your phone):
- **From GitHub (recommended):** Actions → **Test Pushover Notification** → *Run
  workflow*. Uses your Actions secrets, so it confirms the real setup. The run
  log prints whether the keys are set and the exact Pushover API response on
  failure (e.g. a bad token/user key).
- **Weekly digest dry run:** `python notify.py --weekly-digest --dry-run`
- **Locally:**
  ```bash
  PUSHOVER_TOKEN=xxx PUSHOVER_USER=yyy python notify.py --test
  ```

### Optional: nightly fit-scoring agent (`triage.yml`)

`triage_agent.py` scores each new role against your profile with the Claude API.
It is **optional** and needs three repo secrets (**Settings → Secrets and
variables → Actions**):

| Secret | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `CANDIDATE_PROFILE` | Short profile text (your background/targets — kept out of the public repo) |
| `CANDIDATE_RESUME` | Resume / CV text (kept out of the public repo) |

Paste your CV text into `CANDIDATE_RESUME`. Without these secrets, leave
`triage.yml` and `evals.yml` disabled (Actions → ⋯ → Disable workflow) — the
scrapers and dashboard work fully without them; `scores.json` is optional.

> Note: `eval_triage.py` still contains the original ML-candidate golden cases.
> They only matter if you run the triage agent; rewrite them for your domain (or
> keep `evals.yml` disabled) once you've finalized your profile.

## Repo Structure

```
├── config.json                     # ⭐ YOUR settings: keywords, locations, employers, branding
├── docs/cv-to-config-prompt.md     # LLM prompt to generate config.json from a CV
├── scrape_jobs.py                  # All scraping logic (reads config.json)
├── notify.py                       # Pushover notifications (optional)
├── triage_agent.py                 # Optional nightly fit-scoring agent (Claude API)
├── eval_triage.py                  # Golden-case evals for the triage agent (legacy ML cases)
├── requirements.txt                # python-jobspy (Indeed only)
├── jobs.{json,md,html}             # Priority-employer digest (last 24h)
├── linkedin_jobs.{json,md,html}    # LinkedIn watcher (last 1h)
├── indeed_jobs.{json,md,html}      # Indeed watcher (last 24h)
├── all_jobs.json                   # Cumulative 14-day master
├── scores.json                     # Triage verdicts (optional)
├── triage.html                     # Interactive dashboard
└── .github/workflows/
    ├── scrape_jobs.yml             # Daily — priority-employer digest
    ├── linkedin_watch.yml          # Hourly :17 PT — general LinkedIn (last 1h)
    ├── indeed_watch.yml            # Hourly :47 PT — Indeed (last 24h)
    ├── calcareers_watch.yml        # Daily — CalCareers (California state jobs)
    ├── usajobs_watch.yml           # Daily — USAJOBS (federal jobs, no API key)
    ├── localgov_watch.yml          # Daily — NEOGOV + CalOpps (state & local gov)
    ├── linkedin_watch_backup.yml   # Watchdog :33 PT — re-dispatches missed runs
    ├── weekly_digest.yml           # Weekly — optional Pushover summary brief
    ├── triage.yml                  # Nightly — optional fit scoring (needs secrets)
    └── evals.yml                   # Triage-agent evals (optional)
```

## Tuning the search

Everything you'd adjust lives in **[`config.json`](config.json)** (no code edits) —
the scraper and dashboard both read it:
- `keywords.include` — title-match terms · `keywords.exclude` — titles to drop.
- `search_terms.linkedin` / `search_terms.indeed` — queries sent to the boards.
- `locations.linkedin` (with `geoId`) / `locations.indeed` (with `country`).
- `employers.priority` (allowlist for the digest) / `employers.exclude` (drop).
- `priority_topics` (⭐ highlights) · `role_categories` (Role-filter buckets) ·
  `profile` (dashboard + digest branding).

Generate the whole file from your CV with
[`docs/cv-to-config-prompt.md`](docs/cv-to-config-prompt.md), or edit it by hand
(every key is commented).
