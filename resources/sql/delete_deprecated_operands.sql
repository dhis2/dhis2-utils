delete from dataelementoperand
where dataelementoperandid not in 
(select dataelementoperandid from sectiongreyedfields UNION select dataelementoperandid from datasetoperands);
