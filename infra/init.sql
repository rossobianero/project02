CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS jobs (
  id BIGSERIAL PRIMARY KEY,
  job_id TEXT UNIQUE,
  company TEXT,
  title TEXT,
  location TEXT,
  description TEXT,
  apply_url TEXT,
  posted_at DATE,
  embedding vector(128)
);
CREATE TABLE IF NOT EXISTS profiles (
  id BIGSERIAL PRIMARY KEY,
  profile_id TEXT UNIQUE,
  name TEXT,
  email TEXT,
  embedding vector(128)
);
