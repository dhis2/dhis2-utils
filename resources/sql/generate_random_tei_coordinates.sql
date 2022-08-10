
-- SQL script for generating random coordinats for TEIs based on the associated org unit

-- Create support functions

drop function if exists long_from_coord;
create function long_from_coord(coord text) returns double precision as $$
begin
	return substring(coord,'^\[(-?\d{1,3}\.\d{1,9}),.*\]$')::double precision;
end;
$$ language plpgsql;


drop function if exists lat_from_coord;
create function lat_from_coord(coord text) returns double precision as $$
begin
	return substring(coord,'^\[.*,(-?\d{1,3}\.\d{1,9})\]$')::double precision;
end;
$$ language plpgsql;


drop function if exists random_coord_diff;
create function random_coord_diff(val double precision) returns double precision as $$
begin
	return ((random() * 0.3) - 0.15) + val;
end;
$$ language plpgsql;


drop function if exists coord_format;
create function coord_format(val double precision) returns text as $$
begin
	return trim(leading from to_char(val,'99.9999'));
end;
$$ language plpgsql;


drop function if exists random_coord;
create function random_coord(coord text) returns text as $$
begin
	return concat('[', coord_format(random_coord_diff(long_from_coord(coord))), ',', coord_format(random_coord_diff(lat_from_coord(coord))), ']');
end;
$$ language plpgsql;


-- Update TEI coordinates

update trackedentityinstance tei set coordinates = (
	
select random_coord(ou2.coordinates)
from trackedentityinstance tei2
inner join organisationunit ou2 on tei2.organisationunitid = ou2.organisationunitid
where ou2.coordinates is not null
and (tei2.featuretype is null or tei2.featuretype = 'NONE')
and tei2.trackedentityinstanceid = tei.trackedentityinstanceid

);


-- Update TEI feature type

update trackedentityinstance set featuretype = 'POINT' 
where coordinates is not null 
and featuretype = 'NONE';


-- Clean up

drop function if exists long_from_coord;
drop function if exists lat_from_coord;
drop function if exists random_coord_diff;
drop function if exists coord_format;
drop function if exists random_coord;
