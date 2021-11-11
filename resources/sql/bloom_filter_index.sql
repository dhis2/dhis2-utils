-- Bloom filter index in PostgreSQL

-- Create extension

create extension bloom;

-- Create operator classes

-- An operator class defines how a particular data type can be used with an index

create operator class character_ops
default for type character 
using bloom AS
  operator 1 =(character,character),
  function 1 hashbpchar;

create operator class double_precision_ops
default for type double precision 
using bloom AS
  operator 1 =(double precision,double precision),
  function 1 hashfloat8;

 -- Create bloom filter index

create index ax_co_monthly_2020_bloom on analytics_2020 using bloom (dx, co, monthly);

