create table if not exists artifact_binary_exports (
  package_id text primary key,
  artifact_id text not null references engineering_artifacts(artifact_id) on delete cascade,
  format text not null check (format in ('pdf','docx')),
  filename text not null,
  media_type text not null,
  content_bytes bytea not null,
  content_hash text not null,
  release_state text not null,
  external_action_blocked boolean not null default true,
  created_at timestamptz not null default now()
);
create index if not exists idx_artifact_binary_exports_artifact on artifact_binary_exports(artifact_id,created_at desc);

create table if not exists execution_receipts (
  receipt_id text primary key,
  event_type text not null,
  aggregate_id text not null,
  status text not null check (status in ('recorded','published','failed')),
  occurred_at timestamptz not null,
  payload_hash text not null,
  payload_json jsonb not null
);
create index if not exists idx_execution_receipts_recent on execution_receipts(occurred_at desc);
create index if not exists idx_execution_receipts_aggregate on execution_receipts(aggregate_id,event_type);

create table if not exists gmail_draft_receipts (
  receipt_id text primary key,
  correspondence_id text not null unique references correspondence_drafts(id) on delete cascade,
  provider_draft_id text not null,
  mailbox text not null,
  created_at timestamptz not null,
  status text not null check (status='draft_created'),
  send_blocked boolean not null default true
);
