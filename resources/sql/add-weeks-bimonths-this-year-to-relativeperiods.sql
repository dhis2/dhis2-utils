ALTER TABLE relativeperiods ADD COLUMN weeksthisyear BOOLEAN;
ALTER TABLE relativeperiods ADD COLUMN bimonthsthisyear BOOLEAN;

UPDATE relativeperiods SET weeksthisyear=FALSE, bimonthsthisyear=FALSE;
