
-- Set userid of messageconversation table based on first message

update messageconversation mc set userid=(
  select m.userid from message m
  inner join messageconversation_messages mcm on m.messageid = mcm.messageid
  where mcm.messageconversationid = mc.messageconversationid
  and mcm.sort_order=1
  limit 1)
where mc.userid is null;
