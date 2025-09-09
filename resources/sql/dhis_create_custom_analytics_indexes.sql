--
-- SQL script for adding custom indexes to DHIS 2 analytics tables
--
-- Statements can be run with a DHIS 2 analytics table hook or with a cron job
--
-- Index statements should be adjusted to match frequent and slow anaytics queries
--
-- Cron job to run every morning after analytics tables are populated and before business hours
--
-- 30 6 * * *      /bin/bash -c 'psql -d dhis2 -f /var/lib/postgresql/scripts/dhis_create_custom_analytics_indexes.sql'
--

-- Partition 2025

create index if not exists "in_dx_uidlevel1_2025" on public.analytics_2025 using btree (dx, uidlevel1);
create index if not exists "in_dx_uidlevel2_2025" on public.analytics_2025 using btree (dx, uidlevel2);
create index if not exists "in_dx_uidlevel3_2025" on public.analytics_2025 using btree (dx, uidlevel3);
create index if not exists "in_dx_uidlevel4_2025" on public.analytics_2025 using btree (dx, uidlevel4);
create index if not exists "in_dx_monthly_2025" on public.analytics_2025 using btree (dx, monthly);
create index if not exists "in_dx_quarterly_2025" on public.analytics_2025 using btree (dx, quarterly);
create index if not exists "in_dx_yearly_2025" on public.analytics_2025 using btree (dx, yearly);

-- Partition 2024

create index if not exists "in_dx_uidlevel1_2024" on public.analytics_2024 using btree (dx, uidlevel1);
create index if not exists "in_dx_uidlevel2_2024" on public.analytics_2024 using btree (dx, uidlevel2);
create index if not exists "in_dx_uidlevel3_2024" on public.analytics_2024 using btree (dx, uidlevel3);
create index if not exists "in_dx_uidlevel4_2024" on public.analytics_2024 using btree (dx, uidlevel4);
create index if not exists "in_dx_monthly_2024" on public.analytics_2024 using btree (dx, monthly);
create index if not exists "in_dx_quarterly_2024" on public.analytics_2024 using btree (dx, quarterly);
create index if not exists "in_dx_yearly_2024" on public.analytics_2024 using btree (dx, yearly);
