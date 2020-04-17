
-- Create CSV file from git repo

-- $ git log --date=iso --pretty=format:"%h|%an|%ad|%s" > commits.csv

-- Create table

create table gitlog(id text, developer text, committime timestamp, message text);
alter table gitlog add constraint id_unique unique (id);

-- Copy data

copy gitlog(id, developer, committime, message) from '/var/lib/postgresql/commits.csv' delimiter '|' csv;

-- All commits

select id, developer, committime, message 
from gitlog 
where committime > '2018-01-01';

-- Commits per developer

select developer, count(developer) as commits
from gitlog 
where committime > '2018-01-01'
group by developer
order by commits desc;

-- Commits by days

select committime::timestamp::date as commitdate, count(committime::timestamp::date) as commits
from gitlog 
where committime > '2018-01-01'
group by commitdate
order by commits desc;

-- Data cleaning

update gitlog set developer = 'Abyot Asalefew Gizaw' where developer in ('abyot');
update gitlog set developer = 'Jan Henrik Øverland' where developer in ('Jan Henrik Overland');
update gitlog set developer = 'Viet Nguyen' where developer in ('vietnguyen');
update gitlog set developer = 'Gintare Vilkelyte' where developer in ('vilkg');
update gitlog set developer = 'Zubair Asghar' where developer in ('Zubair', 'zubaira');
update gitlog set developer = 'Lars Kristian Roland Wærstad' where developer in ('lkwaerst');
update gitlog set developer = 'Mohamed Ameen' where developer in ('Ameen');
