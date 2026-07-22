CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS opportunities (
  event_id text PRIMARY KEY,
  external_id text NOT NULL,
  source_system text NOT NULL,
  title text NOT NULL,
  issuer text NOT NULL,
  jurisdiction text NOT NULL,
  opportunity_type text NOT NULL,
  status text NOT NULL DEFAULT 'active',
  publication_date timestamptz,
  update_date timestamptz,
  deadline timestamptz,
  value_amount numeric,
  value_currency text,
  value_text text,
  payload jsonb NOT NULL,
  canonical_hash text NOT NULL,
  first_seen_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source_system, external_id)
);

CREATE TABLE IF NOT EXISTS opportunity_provenance (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id text NOT NULL REFERENCES opportunities(event_id) ON DELETE CASCADE,
  source_system text NOT NULL,
  authority text NOT NULL,
  source_url text NOT NULL,
  retrieved_at timestamptz NOT NULL,
  content_hash text,
  attachment_urls jsonb NOT NULL DEFAULT '[]'::jsonb,
  UNIQUE (event_id, source_system, source_url, retrieved_at)
);

CREATE TABLE IF NOT EXISTS opportunity_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id text NOT NULL REFERENCES opportunities(event_id) ON DELETE CASCADE,
  revision_number integer NOT NULL,
  change_type text NOT NULL,
  previous_hash text,
  current_hash text NOT NULL,
  changed_fields jsonb NOT NULL DEFAULT '[]'::jsonb,
  payload jsonb NOT NULL,
  observed_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (event_id, revision_number)
);

CREATE TABLE IF NOT EXISTS treasury_analyses (
  opportunity_id text PRIMARY KEY REFERENCES opportunities(event_id) ON DELETE CASCADE,
  analysis jsonb NOT NULL,
  analysis_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS build_specifications (
  specification_id text PRIMARY KEY,
  opportunity_id text NOT NULL REFERENCES opportunities(event_id) ON DELETE CASCADE,
  specification jsonb NOT NULL,
  approval_state text NOT NULL DEFAULT 'draft',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS brain_plans (
  plan_id text PRIMARY KEY,
  specification_id text NOT NULL REFERENCES build_specifications(specification_id) ON DELETE CASCADE,
  plan jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS spine_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type text NOT NULL,
  aggregate_id text NOT NULL,
  payload jsonb NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_opportunities_deadline ON opportunities(deadline);
CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opportunities_last_seen ON opportunities(last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_spine_events_unpublished ON spine_events(occurred_at) WHERE published_at IS NULL;
