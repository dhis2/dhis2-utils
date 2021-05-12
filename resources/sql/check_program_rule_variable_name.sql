-- check if program rule variable name contains forbidden keywords (and, or, not) in words separated by space

select * from
(select uid, name, regexp_split_to_table(name, '\s+') as keyword from programrulevariable) as p
where keyword = 'and' or keyword = 'or' or keyword = 'not'