
-- Update source type for program rules

update programrulevariable set sourcetype = 'DATAELEMENT_CURRENT_EVENT', lastupdated = current_timestamp 
where uid in (
  select prv.uid from programrulevariable prv join program p on p.programid = prv.programid 
  where p.type = 'WITHOUT_REGISTRATION' and (
  prv.sourcetype = 'DATAELEMENT_NEWEST_EVENT_PROGRAM' or prv.sourcetype = 'DATAELEMENT_NEWEST_EVENT_PROGRAM_STAGE')
);
