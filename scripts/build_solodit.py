"""Audit-finding labels from the Solodit API (Cyfrin). NOT run yet: needs an API key
(SOLODIT_API_KEY, from a Solodit account > API Keys). ToS (https://solodit.cyfrin.io/terms-of-service,
last updated 2025-12-17) s.4 allows derivative datasets and ML training/benchmarking with
attribution; s.5.1 forbids redistributing raw/unmodified data. So this script stores ONLY
derived metadata (no title/body text): finding id/slug link, firm, protocol, impact, tags, date.
Rate limit is ~20 req/min; we sleep accordingly."""
import os, sys, json, time, urllib.request
from common import write
KEY = os.environ.get("SOLODIT_API_KEY")
if not KEY: sys.exit("SOLODIT_API_KEY not set; skipping (see data/SOURCES.md)")
URL = "https://solodit.cyfrin.io/api/v1/solodit/findings"
MAX_PAGES = int(os.environ.get("SOLODIT_MAX_PAGES", "50"))
rows, page = [], 1
while page <= MAX_PAGES:
    body = json.dumps({"page": page, "pageSize": 100, "filters": {"impact": ["HIGH", "MEDIUM"]}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json", "X-Cyfrin-API-Key": KEY})
    d = json.loads(urllib.request.urlopen(req, timeout=60).read())
    items = d.get("findings") or d.get("data") or []
    if not items: break
    for f in items:
        slug = f.get("slug") or f.get("id")
        tags = ";".join(t.get("tags_tag", {}).get("title", "") if isinstance(t, dict) else str(t)
                        for t in (f.get("issues_issuetagscore") or f.get("tags") or []))
        rows.append(dict(id=f"solodit-{f.get('id')}", source=f"Solodit/{f.get('firm_name','')}", chain="",
            contract_name=f.get("protocol_name", ""), label=f"audit_{str(f.get('impact','')).lower()}",
            vuln_category=tags, date=str(f.get("report_date", ""))[:10],
            reference_url=f"https://solodit.cyfrin.io/issues/{slug}", license="Solodit ToS: derived metadata, attribution 'Data from Solodit'",
            source_commit=f"api page {page}"))
    page += 1; time.sleep(3.1)
write("solodit_audit_findings.csv", rows)
