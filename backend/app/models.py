from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
class ProfileCreateResponse(BaseModel):
    profile_id: str
class CandidateProfile(BaseModel):
    profile_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    titles: List[str]
    skills: List[str]
    years_experience: int
    locations: List[str]
    raw_resume_url: Optional[str] = None
    embedding: Optional[list] = None
class JobPosting(BaseModel):
    job_id: str
    company: str
    title: str
    location: str
    description: str
    apply_url: str
    posted_at: Optional[str] = None
    embedding: Optional[list] = None
class MatchResult(BaseModel):
    job_id: str
    company: str
    title: str
    location: str
    score: float
    reasons: List[str] = []
