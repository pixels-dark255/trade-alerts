-- Run once in Supabase → SQL Editor.

create table if not exists notices (
  id            text primary key,              -- stable hash of source+number+date+title
  source        text not null,
  authority     text not null,
  kind          text not null,
  number        text,
  title         text not null,
  notice_date   date,
  url           text,
  raw_text      text,
  summary       jsonb,                          -- AI output (see src/summarize.py)
  impact        text,                           -- high | medium | low
  hs_codes      text[] default '{}',
  sectors       text[] default '{}',
  posted_telegram boolean default false,
  created_at    timestamptz default now()
);
create index if not exists notices_created_idx on notices (created_at desc);

create table if not exists subscribers (
  id                uuid primary key default gen_random_uuid(),
  email             text unique not null,
  name              text,
  company           text,
  hs_prefixes       text[] default '{}',        -- e.g. {'39','3923','7113'}
  sectors           text[] default '{}',
  plan              text not null default 'free',   -- free | pro | firm
  status            text not null default 'active', -- active | unsubscribed
  consent_at        timestamptz not null default now(),
  unsubscribe_token uuid not null default gen_random_uuid(),
  created_at        timestamptz default now()
);

create table if not exists deliveries (
  id            bigserial primary key,
  subscriber_id uuid references subscribers(id) on delete cascade,
  notice_ids    text[] not null,
  channel       text not null default 'email',
  sent_at       timestamptz default now()
);

-- Security: the public website (anon key) may ONLY insert free signups.
alter table notices     enable row level security;
alter table subscribers enable row level security;
alter table deliveries  enable row level security;

drop policy if exists "public signup" on subscribers;
create policy "public signup" on subscribers
  for insert to anon
  with check (plan = 'free' and status = 'active');

-- One-click unsubscribe callable from the website without exposing data.
create or replace function unsubscribe(token uuid)
returns boolean language sql security definer set search_path = public as $$
  update subscribers set status = 'unsubscribed'
  where unsubscribe_token = token
  returning true;
$$;
grant execute on function unsubscribe(uuid) to anon;

-- v17: paid plans are not auto-renewing. Set this date when you switch a subscriber to pro/firm.
-- The daily run emails a renewal link 3 days before and on the day, and moves them back to free 3 days after.
alter table subscribers add column if not exists paid_until date;

-- =====================================================================================================
-- v20 (20 Oct 2026): security + privacy hardening. Safe to run more than once. Run ALL of this block.
-- =====================================================================================================

-- 1. Pilot interest table (in case the v19b block was not run) + data-request table
create table if not exists pilot_interest (
  id uuid primary key default gen_random_uuid(),
  offer text not null check (offer in ('eodc','eudr','cbam')),
  name text, email text not null, company text, city text, phone text, details text, page text,
  created_at timestamptz default now()
);
create table if not exists data_requests (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  kind text not null check (kind in ('delete','access','correct','withdraw')),
  details text,
  created_at timestamptz default now(),
  done_at timestamptz
);
alter table subscribers add column if not exists unsubscribed_at timestamptz;
alter table subscribers add column if not exists paid_until date;

-- 2. Row Level Security: the public (anon) key may ONLY insert, never read, update or delete.
alter table notices        enable row level security;
alter table subscribers    enable row level security;
alter table deliveries     enable row level security;
alter table pilot_interest enable row level security;
alter table data_requests  enable row level security;
revoke all on notices, deliveries from anon, authenticated;
revoke select, update, delete on subscribers, pilot_interest, data_requests from anon, authenticated;
grant insert on subscribers, pilot_interest, data_requests to anon;

-- 3. What a public sign-up may contain (free plan only, sane sizes, valid email, HS codes digits only)
drop policy if exists "public signup" on subscribers;
create policy "public signup" on subscribers for insert to anon with check (
  plan = 'free' and status = 'active' and paid_until is null and unsubscribed_at is null and name is null
  and email ~* '^[^@\s]{1,64}@[^@\s]+\.[a-z]{2,}$' and length(email) <= 254
  and coalesce(length(company), 0) <= 120
  and coalesce(array_length(hs_prefixes, 1), 0) <= 60
  and coalesce(array_to_string(hs_prefixes, ','), '') ~ '^([0-9]{2,8}(,[0-9]{2,8})*)?$'
  and coalesce(array_length(sectors, 1), 0) <= 5);

drop policy if exists "public pilot interest" on pilot_interest;
create policy "public pilot interest" on pilot_interest for insert to anon with check (
  email ~* '^[^@\s]{1,64}@[^@\s]+\.[a-z]{2,}$' and length(email) <= 254
  and coalesce(length(name), 0) <= 100 and coalesce(length(company), 0) <= 120
  and coalesce(length(city), 0) <= 80 and coalesce(length(phone), 0) <= 20
  and coalesce(length(details), 0) <= 1000 and coalesce(length(page), 0) <= 100);

drop policy if exists "public data request" on data_requests;
create policy "public data request" on data_requests for insert to anon with check (
  email ~* '^[^@\s]{1,64}@[^@\s]+\.[a-z]{2,}$' and length(email) <= 254
  and coalesce(length(details), 0) <= 1000 and done_at is null);

-- 4. Rate limiting (anti-spam): max 20 new rows per table per 10 minutes, max 3 per email per day.
create or replace function rate_limit() returns trigger language plpgsql security definer set search_path = public as $$
declare recent int; same int; who text;
begin
  -- only limit the public website (role anon); our server (service_role) and the SQL editor are not limited
  who := coalesce(nullif(current_setting('request.jwt.claims', true), '')::json->>'role', '');
  if who <> 'anon' then return new; end if;
  execute format('select count(*) from %I where created_at > now() - interval ''10 minutes''', tg_table_name) into recent;
  execute format('select count(*) from %I where lower(email) = lower($1) and created_at > now() - interval ''1 day''', tg_table_name)
    using new.email into same;
  if recent >= 20 or same >= 3 then
    raise exception 'Too many requests, please try again later' using errcode = 'P0001';
  end if;
  return new;
end $$;
drop trigger if exists rl_subscribers on subscribers;
create trigger rl_subscribers before insert on subscribers for each row execute function rate_limit();
drop trigger if exists rl_pilot on pilot_interest;
create trigger rl_pilot before insert on pilot_interest for each row execute function rate_limit();
drop trigger if exists rl_requests on data_requests;
create trigger rl_requests before insert on data_requests for each row execute function rate_limit();

-- 5. Unsubscribe and "Delete my data": only work with the secret token from the subscriber's own email.
create or replace function unsubscribe(token uuid)
returns boolean language sql security definer set search_path = public as $$
  update subscribers set status = 'unsubscribed', unsubscribed_at = coalesce(unsubscribed_at, now())
  where unsubscribe_token = token and status <> 'unsubscribed'
  returning true;
$$;
create or replace function delete_my_data(token uuid)
returns boolean language sql security definer set search_path = public as $$
  delete from subscribers where unsubscribe_token = token returning true;   -- deliveries cascade
$$;
revoke all on function unsubscribe(uuid), delete_my_data(uuid), rate_limit() from public;
grant execute on function unsubscribe(uuid), delete_my_data(uuid) to anon;
