# Set up your own job-tracker dashboard (~5 minutes)

This repo scrapes job boards on a schedule and shows the results in a single
filterable dashboard (`triage.html`) hosted free on GitHub Pages. Everything you
search for lives in **one file, `config.json`** — point it at your field and
locations and you're done. No server, no API keys required.

## 1. Get your own copy (30 sec)
- Click **Use this template → Create a new repository** (or **Fork**).
- Make it **public** (GitHub Pages is free for public repos).

## 2. Set your search — pick one (2 min)

**A. Generate it from your CV (recommended).** Open
[`docs/cv-to-config-prompt.md`](docs/cv-to-config-prompt.md), copy the prompt,
paste it into ChatGPT / Claude / Gemini with your CV and target locations, and
it returns a finished `config.json`. In your repo, open `config.json` → **Edit**
(✏️) → paste → **Commit**.

**B. Edit `config.json` by hand.** It's self-documenting. The essentials:
- `keywords.include` + `search_terms` — *what roles* (job-title words/phrases).
- `locations` — *where* (LinkedIn + Indeed entries; `geoId` can be `""`).
- `profile.title` / `subtitle` — dashboard branding.
- Optional: `keywords.exclude`, `employers.priority`/`exclude`,
  `priority_topics` (⭐ highlights), `role_categories` (Role filter buckets).

## 3. Turn on GitHub Pages (1 min)
**Settings → Pages →** Source: **Deploy from a branch**, Branch **`main`**,
folder **`/ (root)`** → **Save**. Your dashboard will be at
`https://<your-username>.github.io/<repo-name>/triage.html`.

## 4. Turn on Actions (1 min)
- **Actions** tab → **"I understand my workflows, enable them."**
- **Settings → Actions → General → Workflow permissions →** select
  **Read and write permissions** → **Save** (lets the scrapers commit results).

## 5. Seed the first results (1 min)
**Actions** tab → run these with **Run workflow** (they then run on a daily/hourly schedule):
- **LinkedIn Env/Tox Watcher**, **Indeed Env/Tox Watcher**
- **USAJOBS Watcher** (federal, US), **Local & State Gov Watcher**, **CalCareers Watcher** (US/CA only — skip if irrelevant)

Wait ~1–2 min, then open your `triage.html` URL. 🎉

## 6. (Optional) Phone notifications
Get a push when a relevant new role appears:
1. At [pushover.net](https://pushover.net), create an **Application** → copy the
   **API Token**; copy your **User Key** from the dashboard.
2. **Settings → Secrets and variables → Actions → New repository secret:**
   add `PUSHOVER_TOKEN` and `PUSHOVER_USER`.
3. Test it: **Actions → Test Pushover Notification → Run workflow.**
4. (Optional) add a repository **Variable** `NOTIFY_TERMS` (comma-separated
   title words) to only get pinged for the roles you care most about.

---

### Turning sources on/off
Each source has a workflow in `.github/workflows/`. Don't want a source? Disable
its workflow (**Actions → that workflow → ⋯ → Disable**). The dashboard simply
skips any source file that doesn't exist. The US/California-specific gov sources
(USAJOBS / NEOGOV / CalOpps / CalCareers) are most useful for US searches.

### Re-running after a config change
Edit `config.json`, commit, then re-run the watchers (or wait for the next
schedule). Hard-refresh the dashboard to pick up new branding/filters.

### Optional: AI fit-scoring
`triage_agent.py` + `triage.yml` score each role against your résumé using the
Claude API (needs `ANTHROPIC_API_KEY` + your profile in secrets). Entirely
optional — the dashboard works without it. Leave `triage.yml` / `evals.yml`
disabled if you don't use it.
