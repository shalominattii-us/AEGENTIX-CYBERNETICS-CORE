create table if not exists correspondence_drafts (
  id text primary key,
  purpose text not null,
  mailbox_json jsonb not null,
  to_json jsonb not null,
  cc_json jsonb not null default '[]'::jsonb,
  subject text not null,
  body text not null,
  attachments_json jsonb not null default '[]'::jsonb,
  opportunity_id text,
  status text not null check (status in ('draft','approved','sent','rejected')),
  created_at timestamptz not null,
  updated_at timestamptz not null default now(),
  provider_message_id text,
  sent_at timestamptz
);

create table if not exists correspondence_approvals (
  draft_id text primary key references correspondence_drafts(id) on delete cascade,
  approved_by text not null,
  approved_at timestamptz not null,
  scope text not null check (scope='single_message'),
  authorization_token_hash text not null
);

create index if not exists correspondence_drafts_status_idx on correspondence_drafts(status,created_at desc);