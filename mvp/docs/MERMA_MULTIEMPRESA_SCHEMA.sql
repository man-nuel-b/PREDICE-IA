-- Predice-IA: esquema de referencia para una base NUEVA y EXCLUSIVA.
-- NO aplicar a TIMELESS ni a otros proyectos. Requiere pruebas de RLS antes de producción.
create extension if not exists pgcrypto;
create table if not exists public.merma_organizations (
 id uuid primary key default gen_random_uuid(),
 name text not null check (char_length(name) between 2 and 120),
 created_at timestamptz not null default now()
);
create table if not exists public.merma_memberships (
 organization_id uuid not null references public.merma_organizations(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 role text not null check (role in ('owner','analyst','viewer')),
 primary key(organization_id,user_id)
);
create table if not exists public.merma_lots (
 id uuid primary key default gen_random_uuid(),
 organization_id uuid not null references public.merma_organizations(id) on delete cascade,
 code text not null,sku text not null,location text not null,
 product_name text not null, category text not null,
 quantity numeric(16,3) not null check(quantity>=0),
 unit_cost numeric(16,2) not null check(unit_cost>=0),
 unit_price numeric(16,2) not null check(unit_price>=0),
 expires_on date not null,
 created_at timestamptz not null default now(),
 unique(organization_id,code,location)
);
create table if not exists public.merma_sales (
 id uuid primary key default gen_random_uuid(),
 organization_id uuid not null references public.merma_organizations(id) on delete cascade,
 sku text not null,location text not null,sold_on date not null,
 quantity numeric(16,3) not null check(quantity>=0),
 unit_price numeric(16,2) not null check(unit_price>=0),
 created_at timestamptz not null default now()
);
create table if not exists public.merma_waste (
 id uuid primary key default gen_random_uuid(),
 organization_id uuid not null references public.merma_organizations(id) on delete cascade,
 sku text not null,location text not null,occurred_on date not null,
 quantity numeric(16,3) not null check(quantity>=0),
 unit_cost numeric(16,2) not null check(unit_cost>=0),
 cause text, created_at timestamptz not null default now()
);
create index if not exists merma_lots_tenant_idx on public.merma_lots(organization_id,sku,location);
create index if not exists merma_sales_tenant_date_idx on public.merma_sales(organization_id,sold_on);
create index if not exists merma_waste_tenant_date_idx on public.merma_waste(organization_id,occurred_on);
alter table public.merma_organizations enable row level security;
alter table public.merma_memberships enable row level security;
alter table public.merma_lots enable row level security;
alter table public.merma_sales enable row level security;
alter table public.merma_waste enable row level security;
revoke all on public.merma_organizations, public.merma_memberships,public.merma_lots,public.merma_sales,public.merma_waste from anon,authenticated;
grant select on public.merma_organizations,public.merma_memberships,public.merma_lots,public.merma_sales,public.merma_waste to authenticated;
grant insert,update,delete on public.merma_lots,public.merma_sales,public.merma_waste to authenticated;
-- Membership lookup avoids recursive RLS by only allowing users to read their OWN memberships.
create policy merma_memberships_self_select on public.merma_memberships for select to authenticated
 using (user_id=(select auth.uid()));
create policy merma_organizations_member_select on public.merma_organizations for select to authenticated
 using (exists (select 1 from public.merma_memberships m where m.organization_id=id and m.user_id=(select auth.uid())));
-- Memberships and organizations must be provisioned by trusted, audited server-side workflows;
-- clients have NO insert/update/delete privileges on these tables.
create policy merma_lots_member_select on public.merma_lots for select to authenticated
 using (exists(select 1 from public.merma_memberships m where m.organization_id=merma_lots.organization_id and m.user_id=(select auth.uid())));
create policy merma_lots_editor_insert on public.merma_lots for insert to authenticated
 with check (exists(select 1 from public.merma_memberships m where m.organization_id=merma_lots.organization_id and m.user_id=(select auth.uid()) and m.role in ('owner','analyst')));
create policy merma_lots_editor_update on public.merma_lots for update to authenticated
 using (exists(select 1 from public.merma_memberships m where m.organization_id=merma_lots.organization_id and m.user_id=(select auth.uid()) and m.role in ('owner','analyst')))
 with check (exists(select 1 from public.merma_memberships m where m.organization_id=merma_lots.organization_id and m.user_id=(select auth.uid()) and m.role in ('owner','analyst')));
create policy merma_sales_member_select on public.merma_sales for select to authenticated
 using (exists(select 1 from public.merma_memberships m where m.organization_id=merma_sales.organization_id and m.user_id=(select auth.uid())));
create policy merma_sales_editor_insert on public.merma_sales for insert to authenticated
 with check (exists(select 1 from public.merma_memberships m where m.organization_id=merma_sales.organization_id and m.user_id=(select auth.uid()) and m.role in ('owner','analyst')));
create policy merma_sales_editor_update on public.merma_sales for update to authenticated
 using (exists(select 1 from public.merma_memberships m where m.organization_id=merma_sales.organization_id and m.user_id=(select auth.uid()) and m.role in ('owner','analyst')))
 with check (exists(select 1 from public.merma_memberships m where m.organization_id=merma_sales.organization_id and m.user_id=(select auth.uid()) and m.role in ('owner','analyst')));
create policy merma_waste_member_select on public.merma_waste for select to authenticated
 using (exists(select 1 from public.merma_memberships m where m.organization_id=merma_waste.organization_id and m.user_id=(select auth.uid())));
create policy merma_waste_editor_insert on public.merma_waste for insert to authenticated
 with check (exists(select 1 from public.merma_memberships m where m.organization_id=merma_waste.organization_id and m.user_id=(select auth.uid()) and m.role in ('owner','analyst')));
create policy merma_waste_editor_update on public.merma_waste for update to authenticated
 using (exists(select 1 from public.merma_memberships m where m.organization_id=merma_waste.organization_id and m.user_id=(select auth.uid()) and m.role in ('owner','analyst')))
 with check (exists(select 1 from public.merma_memberships m where m.organization_id=merma_waste.organization_id and m.user_id=(select auth.uid()) and m.role in ('owner','analyst')));
-- No client DELETE policies: historical evidence cannot be casually erased.
-- REQUIRED BEFORE GO-LIVE: automated RLS negative tests for two tenants,
-- lifecycle provisioning, audit trail, backup restoration and privacy review.
