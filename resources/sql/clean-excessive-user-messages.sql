
-- Delete system messages

delete from messageconversation_usermessages where messageconversationid in (
select mc.messageconversationid from messageconversation mc
where subject in ('Analytics table process failed', 'Data mart process failed','Resource table process failed')
);

delete from messageconversation_messages where messageconversationid in (
select mc.messageconversationid from messageconversation mc
where subject in ('Analytics table process failed', 'Data mart process failed','Resource table process failed')
);

delete from messageconversation mc
where subject in ('Analytics table process failed', 'Data mart process failed','Resource table process failed');


-- Delete user messages where user is not original sender of sender of any message

delete from messageconversation_usermessages where usermessageid in (
select mcu.usermessageid from messageconversation_usermessages mcu
inner join usermessage um on mcu.usermessageid=um.usermessageid
where um.userid not in (
  select m.userid from message m
  inner join messageconversation_messages mcm on m.messageid=mcm.messageid
  where mcm.messageconversationid=mcu.messageconversationid)
and um.userid not in (
  select ugm.userid from usergroupmembers ugm
  inner join usergroup ug on ugm.usergroupid=ug.usergroupid
  where ug.name = 'Feedback Message Recipients')
);

delete from usermessage um
where um.usermessageid not in (
  select usermessageid from messageconversation_usermessages);

delete from message m
where m.messageid not in (
  select messageid from messageconversation_messages);

