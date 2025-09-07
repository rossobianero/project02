from .db import fetchall
from .embeddings import cosine
from typing import List, Dict
def bm25_like(text: str, terms: List[str]) -> float:
    t = text.lower()
    hits = sum(1 for term in terms if term.lower() in t)
    return hits / max(1, len(terms))
def get_matches(profile_id: str, limit: int = 20) -> List[Dict]:
    rows = fetchall(
        """
        SELECT j.job_id, j.company, j.title, j.location, j.description,
               j.embedding as job_emb,
               p.embedding as prof_emb,
               p.skills as skills
        FROM jobs j CROSS JOIN profiles p
        WHERE p.profile_id = :pid
        """,
        {"pid": profile_id},
    )
    scored = []
    for r in rows:
        prof_emb = r["prof_emb"]
        job_emb = r["job_emb"]
        if not (prof_emb and job_emb):
            continue
        sim = cosine(prof_emb, job_emb)
        kw = bm25_like(r["description"] or "", r["skills"] or [])
        score = 0.7 * sim + 0.3 * kw
        reasons = []
        if kw > 0:
            reasons.append(f"Keyword overlap with {int(kw*len(r['skills']))} skills")
        reasons.append(f"Semantic similarity {sim:.2f}")
        scored.append({
            "job_id": r["job_id"],
            "company": r["company"],
            "title": r["title"],
            "location": r["location"],
            "score": float(score),
            "reasons": reasons
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]
