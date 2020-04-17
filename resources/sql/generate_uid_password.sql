CREATE OR REPLACE LANGUAGE pltcl;

-- Generates a valid dhis2 uid identifier
CREATE OR REPLACE FUNCTION dhis_uid() RETURNS varchar(11) AS $$
  set map "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
  #-- first character must be a letter
  set uid [string index $map [expr int(rand()*52)]]
  #-- 10 more characters
  for {set x 0} { $x<10 } {incr x} {
    set uid $uid[string index $map [expr int(rand()*62)]]
  }	
  return $uid
$$ LANGUAGE pltcl;

-- Internal function reimplements Java String.hashCode() method and merges
-- username with password
CREATE OR REPLACE FUNCTION dhis_password_mash(varchar, varchar) RETURNS varchar AS $$
  set userhash 0
  set userlength [string length $1]
  for {set x 0} {$x<$userlength} {incr x} {
    scan [string index $1 $x] %c ch 
    set userhash [expr 31*$userhash + $ch]
  }
  set merged $2\{$userhash\}
  return $merged
$$ LANGUAGE pltcl;

-- Returns a dhis2 hash code for a username, password combination
CREATE  OR REPLACE FUNCTION dhis_password_hash(varchar, varchar) 
  RETURNS varchar AS  'select md5(dhis_password_mash($1, $2));'
LANGUAGE SQL;

-- testing
select dhis_uid(), dhis_password_hash('admin','district');
