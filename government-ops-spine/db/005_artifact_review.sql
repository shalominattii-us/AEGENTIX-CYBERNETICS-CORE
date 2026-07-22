create table if not exists artifact_reviews (
  receipt_id text primary key,
  artifact_id text not null references engineering_artifacts(artifact_id) on delete cascade,
  artifact_hash text not null,
  reviewer_json jsonb not null,
  decision text not null check (decision in ('approve','request_changes','reject')),
  comments text not null,
  reviewed_at timestamptz not null,
  receipt_hash text not null unique,
  created_at timestamptz not null default now()
);
create index if not exists artifact_reviews_artifact_idx on artifact_reviews(artifact_id,reviewed_at);

create table if not exists artifact_exports (
  package_id text primary key,
  artifact_id text not null references engineering_artifacts(artifact_id) on delete cascade,
  format text not null check (format in ('markdown','json')),
  filename text not null,
  media_type text not null,
  content_text text not null,
  content_hash text not null,
  release_state text not null check (release_state in ('internal_review','release_candidate')),
  external_action_blocked boolean not null default true,
  created_at timestamptz not null default now()
);
create index if not exists artifact_exports_artifact_idx on artifact_exports(artifact_id,created_at);
