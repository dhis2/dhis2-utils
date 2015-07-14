
-- Set userid of messageconversation table based on first message

alter table messageconversation drop constraint fk_messageconversation_userid;

alter table messageconversation add column userid integer;

update messageconversation mc set userid=(
  select m.userid from message m
  inner join messageconversation_messages mcm on m.messageid = mcm.messageid
  where mcm.messageconversationid = mc.messageconversationid
  and mcm.sort_order=1
  limit 1)
where mc.userid is null;

-- Set organisation units with no opening date to 1970 and set not null

update organisationunit set openingdate='1970-01-01' where openingdate is null;
alter table organisationunit alter column openingdate set not null;
