create table if not exists engineering_programs (
  program_id text primary key,
  opportunity_id text not null,
  specification_id text not null,
  plan_id text not null,
  capability_matches_json jsonb not null default '[]'::jsonb,
  generated_at timestamptz not null,
  external_actions_blocked boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists engineering_artifacts (
  artifact_id text primary key,
  program_id text not null references engineering_programs(program_id) on delete cascade,
  opportunity_id text not null,
  specification_id text not null,
  artifact_type text not null,
  title text not null,
  content_json jsonb not null,
  content_hash text not null,
  approval_state text not null default 'draft' check (approval_state in ('draft','technical_review','authorized')),
  external_action_blocked boolean not null default true,
  created_at timestamptz not null
);

create index if not exists engineering_programs_opportunity_idx on engineering_programs(opportunity_id);
create index if not exists engineering_artifacts_program_idx on engineering_artifacts(program_id);
create index if not exists engineering_artifacts_type_idx on engineering_artifacts(artifact_type);
