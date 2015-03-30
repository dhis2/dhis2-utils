

INSERT INTO patientattribute ( lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( now(),'Gender', 'Gender','combo', false, false, false);


INSERT INTO patientattributeoption ( name, patientattributeid ) 
select 'F', patientattributeid from patientattribute where name='Gender';

INSERT INTO patientattributeoption ( name, patientattributeid ) 
select 'M', patientattributeid from patientattribute where name='Gender';

INSERT INTO patientattributeoption (name, patientattributeid ) 
select 'T', patientattributeid from patientattribute where name='Gender';


INSERT INTO patientattributevalue (patientid, patientattributeid, value, patientattributeoptionid ) 
SELECT patientid, pao.patientattributeid, pao.name,  pao.patientattributeoptionid
FROM patient p, patientattribute pa, patientattributeoption pao
WHERE p.gender=pao.`name` AND pa.`name`='Gender' AND pao.`name` in('F','M','T') and p.gender is not null;



INSERT INTO patientattribute ( lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( now(),'Death date', 'Death date','date', false, false, false);


INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.deathDate
from patient p, patientattribute pa
where pa.`name`='Death date' and p.deathdate is not null;



INSERT INTO patientattribute ( lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( now(),'Registration date', 'Registration date','date', false, false, false);


INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.registrationDate
from patient p, patientattribute pa
where pa.`name`='Registration date' and p.registrationDate is not null;


INSERT INTO patientattribute ( lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( now(),'Is Dead', 'Is Dead','trueOnly', false, false, false);


INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.isDead
from patient p, patientattribute pa
where pa.`name`='Is Dead' and p.isDead=true;

INSERT INTO patientattribute ( lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( now(),'Is under age', 'Is under age','trackerAssociate', false, false, false);


INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.underAge
from patient p, patientattribute pa
where pa.`name`='Is Dead' and p.underAge=true;


INSERT INTO patientattribute ( lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( now(),'DOB type', 'DOB type','combo', false, false, false);



INSERT INTO patientattributeoption ( name, patientattributeid ) 
select 'A', patientattributeid from patientattribute where name='DOB type';

INSERT INTO patientattributeoption ( name, patientattributeid ) 
select 'D', patientattributeid from patientattribute where name='DOB type';


INSERT INTO patientattributeoption ( name, patientattributeid ) 
select 'V', patientattributeid from patientattribute where name='DOB type';



INSERT INTO patientattributevalue (patientid, patientattributeid, value, patientattributeoptionid ) 
SELECT patientid, pao.patientattributeid, pao.name, pao.patientattributeoptionid
FROM patient p, patientattribute pa, patientattributeoption pao
WHERE p.dobType=pao.`name` AND pao.`name` in('A','D','V') AND pa.`name`='DOB type' and p.dobType is not null;


INSERT INTO patientattribute ( lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( now(),'Birth date', 'Birth date','date', false, false, false);


INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.birthdate
from patient p, patientattribute pa
where pa.`name`='Birth date' and p.birthdate is not null and p.dobType in ('D','V');



INSERT INTO patientattribute ( lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( now(),'Age', 'Age','age', false, false, false);


INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.birthdate
from patient p, patientattribute pa
where pa.`name`='Age' and p.birthdate is not null and dobType ='A';


INSERT INTO patientattribute ( lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( now(),'Phone number', 'Phone number','phoneNumber', false, false, false);


INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.phoneNumber
from patient p, patientattribute pa
where pa.`name`='Phone number' and p.phoneNumber is not null;


INSERT INTO patientattribute ( lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( now(),'Full name', 'Full name','string', false, false, false);


INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.name
from patient p, patientattribute pa
where pa.`name`='Full name' and p.name is not null;



INSERT INTO patientattribute ( lastUpdated, name, description, valueType, mandatory, inherit, displayOnVisitSchedule ) 
VALUES ( now(),'Staff', 'Staff','users', false, false, false);


INSERT INTO patientattributevalue (patientid, patientattributeid, value ) 
select patientid, pa.patientattributeid, p.healthworkerid
from patient p, patientattribute pa
where pa.`name`='Staff' and p.healthworkerid is not null;


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

