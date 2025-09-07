import os, json, datetime, re
import requests
from bs4 import BeautifulSoup
import psycopg
import yaml
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_NAME = os.getenv("DB_NAME", "jobs")
def text_to_vec(text: str, dims: int = 128):
    import hashlib, random, math
    h = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    rnd = random.Random(h)
    vec = [rnd.uniform(-1, 1) for _ in range(dims)]
    norm = math.sqrt(sum(v*v for v in vec)) or 1.0
    return [v / norm for v in vec]
def upsert_job(cur, job):
    cur.execute(
        """
        INSERT INTO jobs(job_id, company, title, location, description, apply_url, posted_at, embedding)
        VALUES (%(job_id)s, %(company)s, %(title)s, %(location)s, %(description)s, %(apply_url)s, %(posted_at)s, %(embedding)s)
        ON CONFLICT (job_id) DO UPDATE SET
            company=EXCLUDED.company,
            title=EXCLUDED.title,
            location=EXCLUDED.location,
            description=EXCLUDED.description,
            apply_url=EXCLUDED.apply_url,
            posted_at=EXCLUDED.posted_at,
            embedding=EXCLUDED.embedding
        """,
        job,
    )
def crawl_greenhouse_json(url, company):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []
    for a in soup.select("a[href*='/jobs/']"):
        title = a.get_text(strip=True)
        apply_url = a.get("href")
        loc = "Remote" if re.search(r"Remote|US|USA", title, re.I) else "Unknown"
        desc = title
        job_id = f"gh-{company}-{apply_url.split('/')[-1]}"
        emb = text_to_vec(f"{title} {company} {desc}")
        jobs.append({
            "job_id": job_id,
            "company": company,
            "title": title,
            "location": loc,
            "description": desc,
            "apply_url": apply_url if apply_url and apply_url.startswith("http") else f"https://boards.greenhouse.io{apply_url or ''}",
            "posted_at": datetime.date.today().isoformat(),
            "embedding": emb,
        })
    return jobs
def crawl_html(url, company):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []
    for item in soup.select("a, li, div"):
        text = item.get_text(" ", strip=True)
        if len(text.split()) < 3:
            continue
        if re.search(r"engineer|developer|software|data|product", text, re.I):
            title = text[:120]
            href = item.get("href") or url
            job_id = f"html-{company}-{abs(hash(title))}"
            emb = text_to_vec(f"{title} {company}")
            jobs.append({
                "job_id": job_id,
                "company": company,
                "title": title,
                "location": "Unknown",
                "description": title,
                "apply_url": href if isinstance(href, str) and href.startswith("http") else url,
                "posted_at": datetime.date.today().isoformat(),
                "embedding": emb,
            })
    return jobs
def main():
    with open("sources.yaml", "r") as f:
        sources = yaml.safe_load(f)
    conn = psycopg.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
    with conn:
        with conn.cursor() as cur:
            total = 0
            for s in sources:
                t = s.get("type")
                company = s.get("company", "UnknownCo")
                url = s.get("url")
                try:
                    jobs = crawl_greenhouse_json(url, company) if t == "greenhouse_json" else crawl_html(url, company)
                except Exception as e:
                    print("Error crawling", company, url, e)
                    continue
                for j in jobs:
                    upsert_job(cur, j)
                total += len(jobs)
                print(f"[{company}] {len(jobs)} jobs")
            print("Total jobs ingested:", total)
if __name__ == "__main__":
    main()
