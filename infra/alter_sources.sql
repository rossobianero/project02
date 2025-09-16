CREATE TABLE IF NOT EXISTS sources (
  id BIGSERIAL PRIMARY KEY,
  company TEXT,
  type TEXT NOT NULL,
  url TEXT,
  board_token TEXT,
  status TEXT DEFAULT 'new',
  robots_allowed BOOLEAN,
  score DOUBLE PRECISION DEFAULT 0.0,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);
