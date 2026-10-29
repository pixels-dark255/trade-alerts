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

-- =====================================================================================================
-- v21 (24 Oct 2026): automatic 14-day Pro trial for EVERY new sign-up + welcome email. Safe to re-run.
-- =====================================================================================================
alter table subscribers add column if not exists trial boolean not null default false;
alter table subscribers add column if not exists welcome_sent_at timestamptz;
-- people who signed up before today already had their first emails: don't send them a "welcome"
update subscribers set welcome_sent_at = coalesce(welcome_sent_at, now()) where created_at < now();

-- every sign-up from the public website starts as a 14-day Pro trial (the daily run moves it back to free)
create or replace function start_trial() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if coalesce(nullif(current_setting('request.jwt.claims', true), '')::json->>'role', '') = 'anon' then
    new.plan := 'pro'; new.trial := true; new.paid_until := current_date + 14; new.welcome_sent_at := null;
  end if;
  return new;
end $$;
revoke all on function start_trial() from public;
drop trigger if exists a_start_trial on subscribers;
create trigger a_start_trial before insert on subscribers for each row execute function start_trial();

-- the public sign-up rule now allows exactly that trial row (still nothing else)
drop policy if exists "public signup" on subscribers;
create policy "public signup" on subscribers for insert to anon with check (
  plan = 'pro' and trial and paid_until = current_date + 14 and welcome_sent_at is null
  and status = 'active' and unsubscribed_at is null and name is null
  and email ~* '^[^@\s]{1,64}@[^@\s]+\.[a-z]{2,}$' and length(email) <= 254
  and coalesce(length(company), 0) <= 120
  and coalesce(array_length(hs_prefixes, 1), 0) <= 60
  and coalesce(array_to_string(hs_prefixes, ','), '') ~ '^([0-9]{2,8}(,[0-9]{2,8})*)?$'
  and coalesce(array_length(sectors, 1), 0) <= 5);

-- OPTIONAL: also give a 14-day trial to people already on the free plan who never had one. Remove the "--" to run.
-- update subscribers set plan = 'pro', trial = true, paid_until = current_date + 14 where plan = 'free' and status = 'active' and not trial;

-- =====================================================================================================
-- v22 (29 Oct 2026): automatic upgrade after Razorpay payment + Firm client setup. Safe to re-run.
-- =====================================================================================================

-- 1. Every Razorpay payment we have processed (so a payment is never applied twice)
create table if not exists payments (
  razorpay_payment_id text primary key,
  email       text not null,
  plan        text not null,
  days        int  not null,
  amount_inr  numeric not null,
  paid_until  date not null,
  created_at  timestamptz default now()
);
alter table payments enable row level security;
revoke all on payments from anon, authenticated;

-- 2. Apply a payment: called only by the webhook function with the service key.
--    Extends from the later of today or the current paid end date (if they were already paying), never shortens.
create or replace function apply_payment(p_payment_id text, p_email text, p_plan text, p_days int, p_amount numeric)
returns jsonb language plpgsql security definer set search_path = public as $$
declare s subscribers%rowtype; base date; new_until date; existed boolean;
begin
  if exists (select 1 from payments where razorpay_payment_id = p_payment_id) then
    return jsonb_build_object('status', 'duplicate');
  end if;
  p_email := lower(trim(p_email));
  select * into s from subscribers where lower(email) = p_email;
  existed := found;
  if existed and s.plan = p_plan and not s.trial and s.paid_until is not null and s.paid_until > current_date then
    base := s.paid_until;
  else
    base := current_date;
  end if;
  new_until := base + p_days;
  if not existed then
    insert into subscribers (email) values (p_email) returning * into s;
  end if;
  -- set the paid values explicitly (also overrides the sign-up trial trigger)
  update subscribers set plan = p_plan, trial = false, paid_until = new_until, status = 'active',
         unsubscribed_at = null where id = s.id;
  insert into payments values (p_payment_id, p_email, p_plan, p_days, p_amount, new_until, now());
  return jsonb_build_object('status', case when existed then 'upgraded' else 'created' end,
                            'paid_until', new_until, 'token', (select unsubscribe_token from subscribers where lower(email) = p_email));
end $$;
revoke all on function apply_payment(text, text, text, int, numeric) from public, anon, authenticated;

-- 3. Firm clients: up to 25 named clients per Firm subscriber, each with its own HS codes
create table if not exists firm_clients (
  id            uuid primary key default gen_random_uuid(),
  subscriber_id uuid not null references subscribers(id) on delete cascade,
  position      int  not null,
  name          text not null check (length(name) between 1 and 80),
  products      text check (coalesce(length(products), 0) <= 300),
  hs_prefixes   text[] not null default '{}',
  created_at    timestamptz default now()
);
create index if not exists firm_clients_sub_idx on firm_clients (subscriber_id);
alter table firm_clients enable row level security;
revoke all on firm_clients from anon, authenticated;

-- Read / save clients with the secret token from the firm's own emails (no passwords, no public reads).
create or replace function get_firm_clients(token uuid)
returns jsonb language plpgsql security definer set search_path = public as $$
declare s subscribers%rowtype;
begin
  select * into s from subscribers where unsubscribe_token = token and status = 'active';
  if not found then return null; end if;
  return jsonb_build_object('email', s.email, 'plan', s.plan, 'paid_until', s.paid_until,
    'clients', coalesce((select jsonb_agg(jsonb_build_object('name', c.name, 'products', c.products, 'hs', c.hs_prefixes)
                         order by c.position) from firm_clients c where c.subscriber_id = s.id), '[]'::jsonb));
end $$;

create or replace function save_firm_clients(token uuid, clients jsonb)
returns jsonb language plpgsql security definer set search_path = public as $$
declare s subscribers%rowtype; c jsonb; i int := 0; codes text[]; allc text[] := '{}';
begin
  select * into s from subscribers where unsubscribe_token = token and status = 'active';
  if not found then return jsonb_build_object('ok', false, 'error', 'invalid link'); end if;
  if s.plan <> 'firm' then return jsonb_build_object('ok', false, 'error', 'Client setup is part of the Firm plan'); end if;
  if jsonb_typeof(clients) <> 'array' or jsonb_array_length(clients) > 25 then
    return jsonb_build_object('ok', false, 'error', 'Up to 25 clients'); end if;
  delete from firm_clients where subscriber_id = s.id;
  for c in select * from jsonb_array_elements(clients) loop
    i := i + 1;
    select coalesce(array_agg(distinct x), '{}') into codes
      from jsonb_array_elements_text(coalesce(c->'hs', '[]'::jsonb)) x where x ~ '^[0-9]{2,8}$';
    if length(trim(coalesce(c->>'name', ''))) = 0 then continue; end if;
    insert into firm_clients (subscriber_id, position, name, products, hs_prefixes)
    values (s.id, i, left(trim(c->>'name'), 80), left(c->>'products', 300), codes[1:60]);
    allc := allc || codes[1:60];
  end loop;
  -- the firm's alerts match the union of all its clients' codes
  update subscribers set hs_prefixes = (select coalesce(array_agg(distinct x), '{}') from unnest(allc) x)
  where id = s.id;
  return jsonb_build_object('ok', true, 'clients', (select count(*) from firm_clients where subscriber_id = s.id));
end $$;
revoke all on function get_firm_clients(uuid), save_firm_clients(uuid, jsonb) from public;
grant execute on function get_firm_clients(uuid), save_firm_clients(uuid, jsonb) to anon;
