import os, asyncio, httpx, yaml, urllib.parse
import psycopg
from pydantic import BaseModel
from typing import Optional, List, Tuple, Dict
from providers import web_search
from detectors import detect_ats

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_NAME = os.getenv("DB_NAME", "jobs")

DISCOVERY_LIMIT = int(os.getenv("DISCOVERY_LIMIT", "200"))
UA = os.getenv("CRAWLER_USER_AGENT", "Mozilla/5.0 (compatible; JobMatchBot/0.2; +https://example.local)")

# Search queries targeting common ATS platforms
SEARCH_QUERIES = [
    'site:boards-api.greenhouse.io "v1/boards" "jobs"',
    'site:boards.greenhouse.io "embed/job_board?for="',
    'site:jobs.lever.co "jobs"',
    'site:myworkdayjobs.com "jobs"',
    'site:jobs.ashbyhq.com',
    'site:careers.smartrecruiters.com',
    'site:successfactors.com "career" OR "careers"'
]

class Source(BaseModel):
    company: Optional[str] = None
    type: str
    url: Optional[str] = None
    board_token: Optional[str] = None
    status: str = "new"
    robots_allowed: Optional[bool] = None
    score: float = 0.0

def robots_allows(url: str, ua: str) -> bool:
    import urllib.robotparser as robotparser
    parsed = urllib.parse.urlsplit(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(ua, url)
    except Exception:
        return True  # default allow if robots.txt not reachable

async def validate_url(url: str) -> Tuple[bool, Optional[int]]:
    headers = {"User-Agent": UA}
    try:
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            r = await client.get(url)
            if r.status_code == 403:
                return (False, 403)
            if r.status_code in (429, 500, 502, 503):
                return (False, r.status_code)
            r.raise_for_status()
            return (True, r.status_code)
    except Exception:
        return (False, None)

def upsert_source(cur, src: Source):
    cur.execute(
        """
        INSERT INTO sources(company, type, url, board_token, status, robots_allowed, score)
        VALUES (%(company)s, %(type)s, %(url)s, %(board_token)s, %(status)s, %(robots_allowed)s, %(score)s)
        ON CONFLICT (type, COALESCE(board_token,''), COALESCE(url,'')) DO UPDATE SET
            company = COALESCE(EXCLUDED.company, sources.company),
            status = EXCLUDED.status,
            robots_allowed = EXCLUDED.robots_allowed,
            score = EXCLUDED.score,
            updated_at = now()
        """,
        src.dict(),
    )

async def discover_once() -> int:
    found: List[Source] = []

    # 1. Run discovery queries
    for q in SEARCH_QUERIES:
        results = await web_search(q, limit=20)
        for item in results:
            url = item.get("url") or ""
            det = detect_ats(url)
            if not det:
                continue
            typ, token_or_url = det
            if typ == "greenhouse_api":
                src = Source(type="greenhouse_api",
                             board_token=token_or_url,
                             url=f"https://boards-api.greenhouse.io/v1/boards/{token_or_url}/jobs")
            elif typ == "greenhouse_embed":
                src = Source(type="greenhouse_embed", url=token_or_url)
            elif typ in ("lever", "workday", "ashby", "smartrecruiters", "successfactors"):
                src = Source(type=typ, url=url)
            else:
                continue
            found.append(src)

    # 2. Deduplicate
    canon: Dict[Tuple[str, str, str], Source] = {}
    for s in found:
        key = (s.type, s.board_token or "", s.url or "")
        canon[key] = s
    unique = list(canon.values())[:DISCOVERY_LIMIT]

    # 3. Validate & upsert
    inserted = 0
    conn = psycopg.connect(host=DB_HOST, port=DB_PORT,
                           user=DB_USER, password=DB_PASS, dbname=DB_NAME)
    with conn:
        with conn.cursor() as cur:
            for s in unique:
                ra = True
                if s.url:
                    ra = robots_allows(s.url, UA)
                s.robots_allowed = ra
                ok, code = (True, 200)
                if s.url and ra:
                    ok, code = await validate_url(s.url)
                s.status = "valid" if (ok and ra) else ("blocked" if code == 403 or not ra else "error")
                s.score = 1.0 if s.status == "valid" else 0.0
                upsert_source(cur, s)
                inserted += 1
    return inserted

def export_yaml(path: str):
    rows = []
    conn = psycopg.connect(host=DB_HOST, port=DB_PORT,
                           user=DB_USER, password=DB_PASS, dbname=DB_NAME)
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT type, company, url, board_token FROM sources
                WHERE status='valid' AND (robots_allowed IS NULL OR robots_allowed=true)
                ORDER BY score DESC, updated_at DESC
                LIMIT 500
            """)
            for (typ, company, url, token) in cur.fetchall():
                if typ == "greenhouse_api" and token:
                    rows.append({
                        "type": "greenhouse_api",
                        "company": company or "Unknown",
                        "board_token": token
                    })
                else:
                    rows.append({
                        "type": typ,
                        "company": company or "Unknown",
                        "url": url
                    })
    with open(path, "w") as f:
        yaml.safe_dump(rows, f, sort_keys=False)
    print(f"Exported {len(rows)} sources to {path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-yaml", help="Export validated sources to a YAML file for the crawler")
    args = parser.parse_args()
    inserted = asyncio.run(discover_once())
    print(f"Discovered/updated {inserted} sources.")
    if args.export_yaml:
        export_yaml(args.export_yaml)
