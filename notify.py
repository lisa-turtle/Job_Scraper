"""
Pushover push notifications for highly-relevant NEW jobs.

Called by scrape_jobs.save_jobs_output() with each run's new_jobs. It is a
no-op unless BOTH PUSHOVER_TOKEN and PUSHOVER_USER env vars are set (so local
runs and forks without Pushover are unaffected). It dedupes against
notified.json so the same role is never pushed twice — across sources or runs.

"Highly relevant" = a posting that either
  • touches a priority topic (microplastics, ecotoxicology, endocrine-disrupting
    chemicals, R/Shiny — mirrors STAR_TERMS in triage.html), or
  • scores >= NOTIFY_MIN_FIT (default 75) on a compact port of the dashboard's
    resume-fit model.

Set up (GitHub → Settings → Secrets and variables → Actions):
  PUSHOVER_TOKEN   your Pushover application/API token
  PUSHOVER_USER    your Pushover user key
Optional: NOTIFY_MIN_FIT (default 75) — lower to get more (less selective) pings.
"""

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NOTIFIED_PATH = os.path.join(SCRIPT_DIR, "notified.json")
ALL_JOBS_PATH = os.path.join(SCRIPT_DIR, "all_jobs.json")
SCORES_PATH = os.path.join(SCRIPT_DIR, "scores.json")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"
DASHBOARD_URL = "https://scottcoffin.github.io/Job_Scraper/triage.html"
MAX_PUSHES_PER_RUN = 8     # cap individual pings; the rest get one summary
NOTIFIED_KEEP = 600        # remember this many recent jobs to avoid repeats

# Priority-topic stars — keep in sync with STAR_TERMS in triage.html.
STAR_TERMS = [
    ("microplastics", re.compile(r'microplastic|nanoplastic|microfiber', re.I)),
    ("ecotoxicology", re.compile(r'ecotoxicolog', re.I)),
    ("endocrine-disrupting chemicals", re.compile(r'endocrine[\s-]?disrupt|\bedcs?\b', re.I)),
    ("R/Shiny", re.compile(r'\brshiny\b|\br[\s-]?shiny\b|shiny\s*(?:app|dashboard|server)|\bshiny\b', re.I)),
]

# Compact resume-fit (port of FIT_TERMS in triage.html). Title counts x3.
FIT_TERMS = [
    (re.compile(r'microplastic|nanoplastic|plastic pollution', re.I), 12),
    (re.compile(r'ecotoxicolog', re.I), 12),
    (re.compile(r'risk assess|human health risk|ecological risk', re.I), 11),
    (re.compile(r'\bexposure\b|exposure assess', re.I), 10),
    (re.compile(r'\bqsar\b|read-across', re.I), 11),
    (re.compile(r'\bpfas\b|perfluoro|per- and polyfluoro', re.I), 10),
    (re.compile(r'toxicolog', re.I), 8),
    (re.compile(r'pharmacokinetic|toxicokinetic|\bpbpk\b', re.I), 8),
    (re.compile(r'dose.response|benchmark dose', re.I), 7),
    (re.compile(r'computational tox|new approach method|\bnam\b|in vitro', re.I), 8),
    (re.compile(r'drinking water|water quality', re.I), 7),
    (re.compile(r'hazard assess', re.I), 6),
    (re.compile(r'endocrine', re.I), 5),
    (re.compile(r'environmental health|environmental chemist', re.I), 4),
    (re.compile(r'cheminformatic|chemical safety|chemical risk', re.I), 5),
]


def _min_fit() -> int:
    try:
        return int(os.environ.get("NOTIFY_MIN_FIT", "75"))
    except ValueError:
        return 75


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _load_config() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _weekly_digest_days() -> int:
    try:
        raw = os.environ.get("WEEKLY_DIGEST_DAYS") or _load_config().get(
            "notify", {}).get("weekly_digest", {}).get("days", 7)
        return max(1, int(raw))
    except ValueError:
        return 7


def _weekly_digest_enabled(force: bool = False) -> bool:
    if force:
        return True
    if _truthy(os.environ.get("WEEKLY_DIGEST_PUSHOVER")):
        return True
    return bool(_load_config().get("notify", {}).get("weekly_digest", {}).get("enabled"))


def _stars(text: str) -> list:
    return [name for name, rx in STAR_TERMS if rx.search(text)]


def _fit(title: str, body: str) -> int:
    score = 0
    for rx, w in FIT_TERMS:
        if rx.search(title):
            score += w * 3
        elif rx.search(body):
            score += w
    return max(0, min(100, round(score * 1.6)))


def relevance(job: dict) -> tuple[bool, list, int]:
    title = job.get("title", "") or ""
    body = f"{job.get('company', '')} {job.get('description', '')}"
    stars = _stars(f"{title} {body}")
    fit = _fit(title, body)
    return (bool(stars) or fit >= _min_fit()), stars, fit


def _identity(job: dict) -> str:
    co = re.sub(r'[^a-z0-9]', '', (job.get("company", "") or "").lower())
    ti = re.sub(r'[^a-z0-9]', '', (job.get("title", "") or "").lower())
    return f"{co}|{ti}"


def _load_notified() -> dict:
    try:
        with open(NOTIFIED_PATH) as f:
            data = json.load(f)
            data.setdefault("ids", [])
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"ids": []}


def _save_notified(data: dict):
    data["ids"] = data["ids"][-NOTIFIED_KEEP:]
    with open(NOTIFIED_PATH, "w") as f:
        json.dump(data, f)


def _load_scores() -> dict:
    try:
        with open(SCORES_PATH, encoding="utf-8") as f:
            return json.load(f).get("scores", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _parse_first_seen(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _salary_numbers(salary: str) -> list[float]:
    core = re.sub(r"\([^)]*\)", "", salary or "")
    values: list[float] = []
    for raw, suffix in re.findall(r"(?:[$A-Z]*\$)?\s*([0-9][0-9,]*(?:\.\d+)?)\s*([kK]?)", core):
        try:
            val = float(raw.replace(",", ""))
        except ValueError:
            continue
        if suffix.lower() == "k":
            val *= 1000
        values.append(val)
    return values


def salary_annual_range(salary: str) -> tuple[float, float] | None:
    values = _salary_numbers(salary)
    if not values:
        return None
    text = salary.lower()
    lo, hi = min(values), max(values)
    if re.search(r"\b(hour|hourly|hr)\b|/hr", text):
        factor = 2080
    elif re.search(r"\b(month|monthly|mo)\b|/mo", text):
        factor = 12
    elif re.search(r"\b(week|weekly|wk)\b|/wk", text):
        factor = 52
    elif re.search(r"\b(day|daily)\b|/day", text):
        factor = 260
    else:
        factor = 1
        if hi < 1000:
            # Some sources label hourly wages as "/yr"; avoid bucketing $34 as
            # an annual salary.
            factor = 2080
    return lo * factor, hi * factor


def salary_band(job: dict) -> str:
    annual = salary_annual_range(job.get("salary", ""))
    if not annual:
        return "No listed salary"
    hi = annual[1]
    if hi >= 200000:
        return "$200k+"
    if hi >= 150000:
        return "$150k-$199k"
    if hi >= 100000:
        return "$100k-$149k"
    if hi >= 75000:
        return "$75k-$99k"
    return "<$75k"


def _score_job(job: dict, scores: dict) -> tuple[int, str]:
    verdict = scores.get(job.get("url", ""), {})
    score = verdict.get("score")
    if isinstance(score, int) and verdict.get("verdict") != "error":
        return max(0, min(100, score)), "agent"
    _, _, fit = relevance(job)
    return fit, "fit"


def _recent_jobs(days: int) -> list[dict]:
    try:
        with open(ALL_JOBS_PATH, encoding="utf-8") as f:
            jobs = list(json.load(f).get("jobs", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = []
    for job in jobs:
        seen = _parse_first_seen(job.get("first_seen", ""))
        if seen and seen >= cutoff:
            recent.append(job)
    return recent


def _count_by(items: list[dict], key_func) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for item in items:
        key = key_func(item) or "Unknown"
        counts[key] = counts.get(key, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))


def _join_counts(counts: list[tuple[str, int]], limit: int = 5) -> str:
    shown = [f"{name} {count}" for name, count in counts[:limit]]
    extra = sum(count for _, count in counts[limit:])
    if extra:
        shown.append(f"other {extra}")
    return "; ".join(shown) if shown else "none"


def _standout_lines(jobs: list[dict], scores: dict, limit: int = 3) -> list[str]:
    ranked = []
    for job in jobs:
        score, source = _score_job(job, scores)
        annual = salary_annual_range(job.get("salary", ""))
        salary_hi = annual[1] if annual else -1
        ranked.append((score, salary_hi, job.get("first_seen", ""), source, job))
    ranked.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)

    lines = []
    for score, _, _, source, job in ranked[:limit]:
        where = job.get("location") or "location n/a"
        salary = f" - {job['salary']}" if job.get("salary") else ""
        lines.append(
            f"- {score}/100 {source}: {job.get('title', 'Untitled')} @ "
            f"{job.get('company', 'Unknown')} ({where}){salary}"
        )
    return lines


def build_weekly_digest(days: int | None = None) -> tuple[str, str, str]:
    days = days or _weekly_digest_days()
    jobs = _recent_jobs(days)
    scores = _load_scores()
    org_count = len({(j.get("company") or "").strip().lower() for j in jobs if j.get("company")})

    title = f"Weekly job digest: {len(jobs)} new role(s)"
    if not jobs:
        return title, f"No new roles first seen in the last {days} day(s).", DASHBOARD_URL

    salary_counts = _count_by(jobs, salary_band)
    org_counts = _count_by(jobs, lambda j: j.get("company", "").strip())
    lines = [
        f"Last {days}d: {len(jobs)} roles across {org_count} organization(s).",
        f"By salary: {_join_counts(salary_counts, limit=6)}.",
        f"Top orgs: {_join_counts(org_counts, limit=5)}.",
        "Standouts:",
    ]
    lines.extend(_standout_lines(jobs, scores, limit=3))
    msg = "\n".join(lines)
    if len(msg) > 1000:
        msg = "\n".join(lines[:4] + _standout_lines(jobs, scores, limit=2))
    if len(msg) > 1000:
        msg = msg[:997] + "..."
    return title, msg, os.environ.get("DASHBOARD_URL") or DASHBOARD_URL


def send_pushover(token: str, user: str, *, title: str, message: str,
                  url: str = "", url_title: str = "", priority: int = 0) -> bool:
    body = {"token": token, "user": user, "title": title[:250],
            "message": message[:1024], "priority": priority}
    if url:
        body["url"] = url
        body["url_title"] = url_title or "View posting"
    data = urllib.parse.urlencode(body).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(PUSHOVER_URL, data=data), timeout=15) as r:
            return 200 <= r.status < 300
    except urllib.error.HTTPError as e:
        # Pushover returns a JSON body with the specific error (bad token/user…).
        try:
            detail = e.read().decode("utf-8", "ignore")
        except Exception:
            detail = ""
        print(f"  ⚠️  Pushover HTTP {e.code}: {detail[:300]}")
        return False
    except Exception as e:
        print(f"  ⚠️  Pushover send failed: {e}")
        return False


def notify_new_jobs(new_jobs: list, source_label: str = ""):
    """Push the highly-relevant, not-yet-notified entries of new_jobs."""
    token = os.environ.get("PUSHOVER_TOKEN")
    user = os.environ.get("PUSHOVER_USER")
    if not token or not user:
        return  # notifications disabled — no creds

    notified = _load_notified()
    seen = set(notified["ids"])
    picks = []
    for job in new_jobs:
        ident = _identity(job)
        if ident in seen:
            continue
        relevant, stars, fit = relevance(job)
        if not relevant:
            continue
        seen.add(ident)
        notified["ids"].append(ident)
        picks.append((job, stars, fit))

    if not picks:
        _save_notified(notified)
        return

    # Starred first, then highest fit.
    picks.sort(key=lambda p: (-len(p[1]), -p[2]))
    sent = 0
    for job, stars, fit in picks[:MAX_PUSHES_PER_RUN]:
        tag = ("★ " + ", ".join(stars)) if stars else f"fit {fit}/100"
        msg = f"{job.get('company', '?')} — {job.get('location', '')}\n{tag}"
        if job.get("salary"):
            msg += f" · {job['salary']}"
        send_pushover(
            token, user,
            title=f"🧪 {job.get('title', 'New role')}",
            message=msg,
            url=job.get("url", ""), url_title="Open posting",
            priority=1 if stars else 0,   # priority topics ping with high priority
        )
        sent += 1

    extra = len(picks) - sent
    if extra > 0:
        send_pushover(token, user, title="🧪 More relevant roles",
                      message=f"+{extra} more relevant new role(s) — open the dashboard.")
    print(f"  📲 Pushover: notified {sent} relevant role(s)"
          + (f" (+{extra} summarized)" if extra else ""))
    _save_notified(notified)


def send_weekly_digest(*, days: int | None = None, force: bool = False,
                       dry_run: bool = False) -> bool:
    """Send the opt-in weekly digest. No LLM call is required; standouts use
    scores.json when present and the deterministic fit scorer otherwise."""
    if not _weekly_digest_enabled(force=force) and not dry_run:
        print("Weekly digest disabled; set WEEKLY_DIGEST_PUSHOVER=true to opt in.")
        return True

    title, message, url = build_weekly_digest(days=days)
    if dry_run:
        print(title)
        print(message)
        print(f"URL: {url}")
        return True

    token = os.environ.get("PUSHOVER_TOKEN")
    user = os.environ.get("PUSHOVER_USER")
    if not token or not user:
        print("Weekly digest skipped: PUSHOVER_TOKEN/PUSHOVER_USER are missing.")
        return False

    ok = send_pushover(
        token,
        user,
        title=title,
        message=message,
        url=url,
        url_title="Open dashboard",
        priority=0,
    )
    print("Weekly digest sent." if ok else "Weekly digest send failed.")
    return ok


def send_test() -> bool:
    """Send a single test push to verify the Pushover setup end-to-end.
    Returns True on success. Prints a clear diagnosis on failure."""
    token = os.environ.get("PUSHOVER_TOKEN")
    user = os.environ.get("PUSHOVER_USER")
    print(f"PUSHOVER_TOKEN: {'(set)' if token else '(MISSING)'}")
    print(f"PUSHOVER_USER:  {'(set)' if user else '(MISSING)'}")
    if not token or not user:
        print("\n❌ Both PUSHOVER_TOKEN and PUSHOVER_USER must be set.\n"
              "   • Locally:  PUSHOVER_TOKEN=… PUSHOVER_USER=… python notify.py --test\n"
              "   • On GitHub: add them as Actions secrets, then run the "
              "'Test Pushover Notification' workflow.")
        return False
    ok = send_pushover(
        token, user,
        title="🧪 Job_Scraper — test notification",
        message=("Pushover is wired up correctly. You'll get pings like this for "
                 "highly-relevant new roles: microplastics, ecotoxicology, "
                 "endocrine-disrupting chemicals, R/Shiny, or a high resume-fit score."),
        url="https://scottcoffin.github.io/Job_Scraper/triage.html",
        url_title="Open dashboard",
        priority=0,
    )
    print("\n✅ Test notification sent — check your phone." if ok
          else "\n❌ Send failed (see the error above — usually a wrong token or user key).")
    return ok


if __name__ == "__main__":
    # `python notify.py` or `python notify.py --test` -> send a test push.
    # `python notify.py --weekly-digest` -> send the opt-in weekly brief.
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # let emoji print on Windows too
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Pushover notifications for Job_Scraper.")
    parser.add_argument("--test", action="store_true", help="send a test push")
    parser.add_argument("--weekly-digest", action="store_true", help="send the weekly digest")
    parser.add_argument("--days", type=int, default=None,
                        help="lookback window for --weekly-digest (default: env or 7)")
    parser.add_argument("--force", action="store_true",
                        help="bypass the weekly opt-in flag for manual dispatch")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the weekly digest without sending Pushover")
    args = parser.parse_args()

    if args.weekly_digest:
        raise SystemExit(0 if send_weekly_digest(
            days=args.days, force=args.force, dry_run=args.dry_run) else 1)
    raise SystemExit(0 if send_test() else 1)
