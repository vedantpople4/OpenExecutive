-- OpenExec Postgres schema. Idempotent -- safe to re-run.
--
-- Hybrid shape: columns for what is filtered, ordered or joined on; one jsonb
-- blob for the result payload. That keeps the repository returning plain dicts
-- with the same keys the rest of the app already reads, so routers, services,
-- to_summary/to_detail and the frontend need no changes.

create table if not exists decisions (
    id                text primary key,
    -- Plain text, deliberately not a reference to Supabase's auth.users: this
    -- file also builds the plain postgres:16 that CI and tests/conftest.py use,
    -- where no auth schema exists. Holds a Supabase user uuid as a string.
    -- The sentinel default backfills rows written before auth existed; nothing
    -- filters on user_id yet, so they stay reachable until that lands.
    user_id           text        not null default '__unmigrated__',
    status            text        not null,
    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now(),
    prompt            text        not null,
    -- The submit route already 404s on a missing parent; this also closes the
    -- window where the parent is deleted between that check and the insert.
    -- set null rather than cascade: a branch losing its parent should become a
    -- root decision, not disappear along with it.
    parent_run_id     text        references decisions(id) on delete set null,
    team_mode_enabled boolean     not null default false,
    requested_agents  jsonb       not null default '[]'::jsonb,
    -- agent_reports, deliberation_rounds, board_decision, action_items,
    -- top_risks, agent_alignment, executive_summary, ... Everything the API
    -- returns but never queries by.
    data              jsonb       not null default '{}'::jsonb
);

-- CREATE TABLE IF NOT EXISTS is a no-op on a database that predates the column,
-- so the ALTER is what actually migrates an existing deployment.
alter table decisions add column if not exists user_id text not null default '__unmigrated__';

-- Replaces gsi_recency. No partition key needed: ORDER BY created_at DESC does
-- the job that entity_type existed only to enable, so that column is gone.
-- id is the tiebreaker so the keyset cursor is total -- two decisions created
-- in the same millisecond would otherwise page unstably.
--
-- user_id leads so per-user pagination stays one index scan rather than a scan
-- of everybody's decisions filtered down. The unconditional DROP is how an
-- existing database picks the new definition up: CREATE INDEX IF NOT EXISTS
-- matches on name alone and would leave the old two-column index in place.
drop index if exists decisions_recency;
create index if not exists decisions_recency
    on decisions (user_id, created_at desc, id desc);

-- Replaces gsi_parent, which backs has_children().
create index if not exists decisions_parent
    on decisions (parent_run_id)
    where parent_run_id is not null;

create table if not exists events (
    -- DynamoDB had no cascade, so routers/decisions.py deletes events first and
    -- the decision second. The cascade makes that ordering a backstop rather
    -- than the only thing standing between a delete and an orphaned timeline.
    aggregate_id text  not null references decisions(id) on delete cascade,
    -- ISO-timestamp-prefixed sort key, carried over unchanged: it already
    -- sorts emission order lexicographically.
    sk           text  not null,
    event_id     text,
    timestamp    timestamptz,
    type         text,
    payload      jsonb not null default '{}'::jsonb,
    primary key (aggregate_id, sk)
);
