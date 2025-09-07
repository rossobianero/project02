CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS profiles (
  profile_id UUID PRIMARY KEY,
  titles TEXT[],
  skills TEXT[],
  years_experience INT,
  locations TEXT[],
  raw_resume TEXT,
  embedding vector(128)
);
CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  company TEXT,
  title TEXT,
  location TEXT,
  description TEXT,
  apply_url TEXT,
  posted_at DATE,
  embedding vector(128)
);
CREATE TABLE IF NOT EXISTS feedback (
  profile_id UUID REFERENCES profiles(profile_id) ON DELETE CASCADE,
  job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
  label TEXT,
  created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs USING GIN (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,'')));
CREATE INDEX IF NOT EXISTS idx_jobs_emb ON jobs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_profiles_emb ON profiles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
