CREATE TABLE IF NOT EXISTS opportunity_records (
  event_id TEXT PRIMARY KEY,
  external_id TEXT NOT NULL,
  source_system TEXT NOT NULL,
  canonical_hash TEXT NOT NULL,
  revision INTEGER NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active', 'cancelled', 'awarded', 'closed')),
  opportunity_json TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  UNIQUE (source_system, external_id)
);

CREATE TABLE IF NOT EXISTS opportunity_revisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL REFERENCES opportunity_records(event_id),
  revision INTEGER NOT NULL,
  canonical_hash TEXT NOT NULL,
  change_type TEXT NOT NULL CHECK (change_type IN ('created', 'amended', 'cancelled', 'awarded')),
  changed_fields TEXT NOT NULL,
  opportunity_json TEXT NOT NULL,
  observed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intake_outbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,
  aggregate_id TEXT NOT NULL REFERENCES opportunity_records(event_id),
  payload_json TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  published_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_opportunity_revisions_event ON opportunity_revisions (event_id);
CREATE INDEX IF NOT EXISTS idx_intake_outbox_unpublished ON intake_outbox (id) WHERE published_at IS NULL;
