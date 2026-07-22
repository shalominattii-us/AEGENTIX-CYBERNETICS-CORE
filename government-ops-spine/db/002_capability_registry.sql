create table if not exists capability_assets (
  id text primary key,
  source_type text not null check (source_type in ('github','docker','document','service','cad','patent','test','manual')),
  source_uri text not null,
  name text not null,
  description text not null default '',
  maturity text not null default 'unknown',
  execution_zones jsonb not null default '[]'::jsonb,
  tags jsonb not null default '[]'::jsonb,
  evidence jsonb not null default '[]'::jsonb,
  metadata_json jsonb not null default '{}'::jsonb,
  content_hash text not null,
  discovered_at timestamptz not null,
  updated_at timestamptz not null default now(),
  unique(source_type, source_uri)
);

create table if not exists capability_matches (
  opportunity_id text not null,
  requirement_id text not null,
  capability_id text references capability_assets(id),
  score numeric not null,
  disposition text not null check (disposition in ('reuse','adapt','build','partner')),
  rationale text not null,
  created_at timestamptz not null default now(),
  primary key (opportunity_id, requirement_id)
);

create index if not exists capability_assets_tags_gin on capability_assets using gin(tags);
create index if not exists capability_assets_metadata_gin on capability_assets using gin(metadata_json);
