-- 2.29 upgrade script

alter table trackedentity rename to trackedentitytype;
alter table trackedentitytype rename trackedentityid to trackedentitytypeid;

alter table program rename trackedentityid to trackedentitytypeid;
alter table program rename constraint fk_program_trackedentityid to fk_program_trackedentitytypeid;

alter table trackedentityinstance rename trackedentityid to trackedentitytypeid;
alter table trackedentityinstance rename constraint fk_trackedentityinstance_trackedentityid to fk_trackedentityinstance_trackedentitytypeid;

alter table attribute rename trackedentityattribute to trackedentitytypeattribute;

alter table trackedentityattributevalues rename to trackedentitytypeattributevalues;
alter table trackedentitytypeattributevalues rename trackedentityid to trackedentitytypeid;

alter table trackedentitytranslations rename trackedentityid to trackedentitytypeid;            
alter table trackedentitytranslations rename constraint fk_objecttranslation_trackedentityid to fk_objecttranslation_trackedentitytypeid
