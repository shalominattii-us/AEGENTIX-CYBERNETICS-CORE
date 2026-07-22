create table if not exists organization_directory (
  organization_id text primary key,
  name text not null,
  submission_email text not null,
  cc_json jsonb not null default '[]'::jsonb,
  address text,
  jurisdiction text,
  sectors_json jsonb not null default '[]'::jsonb,
  verified_at timestamptz not null,
  source text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists human_review_queue (
  review_id text primary key,
  item_type text not null,
  aggregate_id text not null,
  opportunity_id text,
  title text not null,
  summary text not null,
  required_role text not null,
  status text not null default 'pending',
  due_at timestamptz,
  payload_json jsonb not null,
  created_at timestamptz not null,
  decided_at timestamptz,
  decided_by text,
  decision_comments text,
  authorization_token_hash text
);
create index if not exists human_review_queue_status_idx on human_review_queue(status,created_at);

create table if not exists complete_submission_packages (
  package_id text primary key,
  opportunity_id text not null,
  program_id text not null,
  organization_id text not null references organization_directory(organization_id),
  manifest_id text not null,
  subject text not null,
  body text not null,
  attachments_json jsonb not null,
  package_hash text not null,
  status text not null default 'pending_review',
  external_action_blocked boolean not null default true,
  created_at timestamptz not null,
  updated_at timestamptz not null default now()
);
create index if not exists complete_submission_packages_opportunity_idx on complete_submission_packages(opportunity_id,created_at);
