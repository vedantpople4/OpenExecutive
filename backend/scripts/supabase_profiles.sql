-- Supabase-specific DDL. Run this once by hand in the Supabase SQL editor
-- against the real project. It is NOT part of the app's migration path:
-- create_tables() applies schema.sql only, and never this file.
--
-- It references auth.users, which exists only inside a Supabase project. The
-- plain postgres:16 that CI and backend/tests/conftest.py run against has no
-- auth schema, so putting any of this in schema.sql would break the suite.
-- That is also why decisions.user_id over in schema.sql is plain text with no
-- foreign key: the app's own schema stays portable to any Postgres.
--
-- Idempotent -- safe to re-run.

create table if not exists public.profiles (
    id         uuid primary key references auth.users(id) on delete cascade,
    email      text,
    created_at timestamptz not null default now()
);

-- PostgREST exposes every table in `public` to anyone holding the anon key, so
-- without RLS this table would hand out the full email list of the user base.
alter table public.profiles enable row level security;

drop policy if exists profiles_select_own on public.profiles;
create policy profiles_select_own on public.profiles
    for select using (auth.uid() = id);

drop policy if exists profiles_update_own on public.profiles;
create policy profiles_update_own on public.profiles
    for update using (auth.uid() = id) with check (auth.uid() = id);

-- security definer because the insert runs as the signing-up user, who has no
-- rights on public.profiles; empty search_path so a schema on the caller's
-- path cannot shadow the table this resolves to.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    insert into public.profiles (id, email)
    values (new.id, new.email)
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();
