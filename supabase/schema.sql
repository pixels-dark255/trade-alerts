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
