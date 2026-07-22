create table if not exists engineering_export_manifests (
  manifest_id text primary key,
  program_id text not null references engineering_programs(program_id) on delete cascade,
  opportunity_id text not null,
  manifest_json jsonb not null,
  manifest_hash text not null,
  release_state text not null check (release_state in ('internal_review','role_review_complete')),
  external_action_blocked boolean not null default true,
  created_at timestamptz not null default now()
);

create index if not exists engineering_export_manifests_program_idx
  on engineering_export_manifests(program_id, created_at desc);
