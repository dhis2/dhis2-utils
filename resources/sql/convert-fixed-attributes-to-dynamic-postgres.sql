
------------------
-- Gender
------------------

INSERT INTO patientattribute ( patientattributeid, lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( nextval('hibernate_sequence'), now(),'Gender', 'Gender','combo', false, false, false);

-- Create options for this attribute Gender

INSERT INTO patientattributeoption (patientattributeoptionid, name, patientattributeid ) 
select nextval('hibernate_sequence'), 'F', patientattributeid from patientattribute where name='Gender';

INSERT INTO patientattributeoption (patientattributeoptionid, name, patientattributeid ) 
select nextval('hibernate_sequence'), 'M', patientattributeid from patientattribute where name='Gender';

INSERT INTO patientattributeoption (patientattributeoptionid, name, patientattributeid ) 
select nextval('hibernate_sequence'), 'T', patientattributeid from patientattribute where name='Gender';

-- Insert patientattributevalue for the attribute Gender

INSERT INTO patientattributevalue (patientid, patientattributeid, value, patientattributeoptionid ) 
SELECT patientid, pao.patientattributeid, pao.name,  pao.patientattributeoptionid
FROM patient p, patientattribute pa, patientattributeoption pao
WHERE p.gender=pao."name" AND pa."name"='Gender' AND pao."name" in('F','M','T') and p.gender is not null;


------------------
--  Death date
------------------

INSERT INTO patientattribute ( patientattributeid, lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( nextval('hibernate_sequence'), now(),'Death date', 'Death date','date', false, false, false);

-- Insert data into Deathdate

INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.deathDate
from patient p, patientattribute pa
where pa."name"='Death date' and p.deathdate is not null;

------------------
-- registrationDate
------------------


INSERT INTO patientattribute ( patientattributeid, lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( nextval('hibernate_sequence'), now(),'Registration date', 'Registration date','date', false, false, false);

-- Insert data into registrationDate

INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.registrationDate
from patient p, patientattribute pa
where pa."name"='Registration date' and p.registrationDate is not null;


------------------
-- isDead
------------------


INSERT INTO patientattribute ( patientattributeid, lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( nextval('hibernate_sequence'), now(),'Is Dead', 'Is Dead','trueOnly', false, false, false);

-- Inserting data into isDead


INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.isDead
from patient p, patientattribute pa
where pa."name"='Is Dead' and p.isDead=true;

------------------
-- underAge
------------------

INSERT INTO patientattribute ( patientattributeid, lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( nextval('hibernate_sequence'), now(),'Is under age', 'Is under age','trackerAssociate', false, false, false);

-- Inserting data into underAge

INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.underAge
from patient p, patientattribute pa
where pa."name"='Is Dead' and p.underAge=true;


------------------
-- dobType
------------------

INSERT INTO patientattribute ( patientattributeid, lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( nextval('hibernate_sequence'), now(),'DOB type', 'DOB type','combo', false, false, false);

-- Insert dobType options


INSERT INTO patientattributeoption (patientattributeoptionid, name, patientattributeid ) 
select nextval('hibernate_sequence'), 'A', patientattributeid from patientattribute where name='DOB type';

INSERT INTO patientattributeoption (patientattributeoptionid, name, patientattributeid ) 
select nextval('hibernate_sequence'), 'D', patientattributeid from patientattribute where name='DOB type';


INSERT INTO patientattributeoption (patientattributeoptionid, name, patientattributeid ) 
select nextval('hibernate_sequence'), 'V', patientattributeid from patientattribute where name='DOB type';


-- Insert patientattributevalue for the attribute dobType

INSERT INTO patientattributevalue (patientid, patientattributeid, value, patientattributeoptionid ) 
SELECT patientid, pao.patientattributeid, pao.name, pao.patientattributeoptionid
FROM patient p, patientattribute pa, patientattributeoption pao
WHERE p.dobType=pao."name" AND pao."name" in('A','D','V') AND pa."name"='DOB type' and p.dobType is not null;


------------------
-- birthdate
------------------

INSERT INTO patientattribute ( patientattributeid, lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( nextval('hibernate_sequence'), now(),'Birth date', 'Birth date','date', false, false, false);

-- Inserting data into birthdate

INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.birthdate
from patient p, patientattribute pa
where pa."name"='Birth date' and p.birthdate is not null and p.dobType in ('D','V');


------------------
-- Age
------------------

INSERT INTO patientattribute ( patientattributeid, lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( nextval('hibernate_sequence'), now(),'Age', 'Age','age', false, false, false);

-- Inserting data into birthdate

INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.birthdate
from patient p, patientattribute pa
where pa."name"='Age' and p.birthdate is not null and dobType ='A';


------------------
-- phoneNumber
------------------

INSERT INTO patientattribute ( patientattributeid, lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( nextval('hibernate_sequence'), now(),'Phone number', 'Phone number','phoneNumber', false, false, false);

-- Inserting data into birthdate

INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.phoneNumber
from patient p, patientattribute pa
where pa."name"='Phone number' and p.phoneNumber is not null;


------------------
-- full name
------------------


INSERT INTO patientattribute ( patientattributeid, lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( nextval('hibernate_sequence'), now(),'Full name', 'Full name','string', false, false, false);

-- Inserting data into full name

INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.name
from patient p, patientattribute pa
where pa."name"='Full name' and p.name is not null;


------------------
-- User Associate
------------------


INSERT INTO patientattribute ( patientattributeid, lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( nextval('hibernate_sequence'), now(),'Staff', 'Staff','users', false, false, false);

-- Inserting data into staff / associate

INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.healthworkerid
from patient p, patientattribute pa
where pa."name"='Staff' and p.healthworkerid is not null;

-- Dropping columns of patient TABLE 

ALTER TABLE patient DROP COLUMN gender;
ALTER TABLE patient DROP COLUMN deathDate;
ALTER TABLE patient DROP COLUMN registrationDate;
ALTER TABLE patient DROP COLUMN isDead;
ALTER TABLE patient DROP COLUMN underAge;
ALTER TABLE patient DROP COLUMN dobType;
ALTER TABLE patient DROP COLUMN birthdate;
ALTER TABLE patient DROP COLUMN phoneNumber;
ALTER TABLE patient DROP COLUMN name;
ALTER TABLE patient DROP COLUMN healthworkerid;

