
--
-- Tracker and event queries
--


-- Relationship types and relationship constraints

select 
  rt.relationshiptypeid,
  rt.uid as type_uid, 
  rt.name as type_name, 
  rt.code as type_code, 
  rt.bidirectional as type_bidirectional, 
  rt.fromtoname as type_from_to_name, 
  rt.tofromname as type_from_to_name,
  from_tet.uid as from_tet_uid,
  from_tet.name as from_tet_name, 
  from_pr.uid as from_pr_uid,
  from_pr.name as from_pr_name,
  from_ps.uid as from_ps_uid, 
  from_ps.name as from_ps_name,
  to_tet.uid as to_tet_uid, 
  to_tet.name as to_tet_name,
  to_pr.uid as to_pr_uid, 
  to_pr.name as to_pr_name,
  to_ps.uid as to_ps_uid, 
  to_ps.name as to_ps_name
from 
  relationshiptype rt
inner join relationshipconstraint from_rc on
  rt.from_relationshipconstraintid = from_rc.relationshipconstraintid
left join trackedentitytype from_tet on
  from_rc.trackedentitytypeid = from_tet.trackedentitytypeid
left join program from_pr on 
  from_rc.programid = from_pr.programid
left join programstage from_ps on
  from_rc.programstageid = from_ps.programstageid
inner join relationshipconstraint to_rc on
  rt.to_relationshipconstraintid = to_rc.relationshipconstraintid
left join trackedentitytype to_tet on
  to_rc.trackedentitytypeid = to_tet.trackedentitytypeid
left join program to_pr on
  to_rc.programid = to_pr.programid
left join programstage to_ps on
  to_rc.programstageid = to_ps.programstageid;


-- Relationships and relationship types

select 
  rt.uid as type_uid,
  rt.name as type_name,
  r.relationshipid,
  r.relationshiptypeid,
  r.uid,
  r.from_relationshipitemid,
  r.to_relationshipitemid,
  r.key,
  r.inverted_key,
  r.deleted  
from 
  relationship r
inner join relationshiptype rt on
  r.relationshiptypeid=rt.relationshiptypeid ;
