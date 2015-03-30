update organisationunit ou set coordinates=NULL
where
ou.coordinates not like '%[%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates not like '%.%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates like '%,0%' and ou.coordinates not like '%,0.%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates like '%,-0%' and ou.coordinates not like '%,-0.%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates like '%[0%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates not like '%,%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates not like '%]' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates like '%.%.%.%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates not like '%.%.%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates like '%[ 0%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates like '%, 0%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates like '%+%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates like '%E%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates like '%00.%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);

update organisationunit ou set coordinates=NULL
where
ou.coordinates like '%i%' and

ou.organisationunitid in (
select ou.organisationunitid from organisationunit ou, _orgunitstructure oustr
where
oustr."level"=5 and
ou.organisationunitid=oustr.organisationunitid
);
