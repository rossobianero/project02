-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

---------------------------------------------------
-- Candidate Profiles
---------------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
  profile_id UUID PRIMARY KEY,
  titles TEXT[],
  skills TEXT[],
  years_experience INT,
  locations TEXT[],
  raw_resume TEXT,
  embedding vector(128)
);

---------------------------------------------------
-- Jobs
---------------------------------------------------
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

---------------------------------------------------
-- Feedback (user likes/dislikes on matches)
---------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
  profile_id UUID REFERENCES profiles(profile_id) ON DELETE CASCADE,
  job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
  label TEXT,
  created_at TIMESTAMP DEFAULT now()
);

---------------------------------------------------
-- Sources registry (discovery service results)
---------------------------------------------------
CREATE TABLE IF NOT EXISTS sources (
  id BIGSERIAL PRIMARY KEY,
  company TEXT,
  type TEXT NOT NULL,
  url TEXT,
  board_token TEXT,
  status TEXT DEFAULT 'new',
  robots_allowed BOOLEAN,
  score DOUBLE PRECISION DEFAULT 0.0,
  notes TEXT,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  -- Unique dedupe key across type+board_token+url
  key TEXT GENERATED ALWAYS AS (
    type || '|' || COALESCE(board_token,'') || '|' || COALESCE(url,'')
  ) STORED,
  UNIQUE(key)
);

---------------------------------------------------
-- Indexes
---------------------------------------------------
-- For jobs text search & ANN vector search
CREATE INDEX IF NOT EXISTS idx_jobs_title
  ON jobs USING GIN (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,'')));

CREATE INDEX IF NOT EXISTS idx_jobs_emb
  ON jobs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_profiles_emb
  ON profiles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);

-- For sources
CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status);
CREATE INDEX IF NOT EXISTS idx_sources_type   ON sources(type);

---------------------------------------------------
-- Triggers
---------------------------------------------------
-- Auto-update `updated_at`
CREATE OR REPLACE FUNCTION touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sources_touch ON sources;
CREATE TRIGGER trg_sources_touch
BEFORE UPDATE ON sources
FOR EACH ROW
EXECUTE FUNCTION touch_updated_at();
