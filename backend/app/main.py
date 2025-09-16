from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
from .db import execute, fetchone
from .embeddings import text_to_vec
from .matching import get_matches
app = FastAPI(title="Agentic Job Matching — Walking Skeleton")
def parse_resume_to_profile_text(resume_bytes: bytes) -> dict:
    text = resume_bytes.decode("utf-8", errors="ignore")
    canonical = ["python","java","javascript","go","kubernetes","aws","gcp","azure","postgresql","mysql","docker"]
    tokens = set([t.strip(".,;:()[]{}<>\n\t ").lower() for t in text.split()])
    skills = [s for s in canonical if s in tokens] or canonical[:5]
    titles = ["Software Engineer"] if "engineer" in tokens else ["Developer"]
    years = 5 if "senior" in tokens else 2
    locations = ["remote"]
    return {
        "titles": titles,
        "skills": skills,
        "years_experience": years,
        "locations": locations,
        "raw_text": text,
    }
@app.post("/profiles")
async def create_profile(file: UploadFile = File(...)):
    resume_bytes = await file.read()
    parsed = parse_resume_to_profile_text(resume_bytes)
    profile_id = str(uuid.uuid4())
    emb = text_to_vec(" ".join(parsed["titles"] + parsed["skills"]))
    execute(
        """
        INSERT INTO profiles(profile_id, titles, skills, years_experience, locations, raw_resume, embedding)
        VALUES (:pid, :titles, :skills, :years, :locs, :raw, :emb)
        """,
        {
            "pid": profile_id,
            "titles": parsed["titles"],
            "skills": parsed["skills"],
            "years": parsed["years_experience"],
            "locs": parsed["locations"],
            "raw": parsed["raw_text"],
            "emb": emb,
        },
    )
    return {"profile_id": profile_id}
@app.get("/matches")
def matches(profile_id: str = Query(...), limit: int = Query(20)):
    prof = fetchone("SELECT profile_id FROM profiles WHERE profile_id=:pid", {"pid": profile_id})
    if not prof:
        raise HTTPException(status_code=404, detail="profile not found")
    results = get_matches(profile_id=profile_id, limit=limit)
    return JSONResponse(content={"results": results})
@app.post("/feedback")
def feedback(profile_id: str, job_id: str, label: str):
    execute(
        "INSERT INTO feedback(profile_id, job_id, label) VALUES (:pid, :jid, :lbl)",
        {"pid": profile_id, "jid": job_id, "lbl": label},
    )
    return {"ok": True}