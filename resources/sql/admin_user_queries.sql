
--
-- USERS
--

-- User roles

select ur.userroleid, ur.uid, ur.name
from userrole ur;

-- Users in user role

select 
  u.userinfoid as user_id, 
  u.username as username, 
  u.firstname as first_name, 
  u.surname as surname,
  u.disabled as disabled
from userinfo u 
inner join userrolemembers urm on u.userinfoid=urm.userid 
inner join userrole ur on urm.userroleid=ur.userroleid 
where ur.name='Superuser';

-- User roles of user

select ur.userroleid, ur.uid, ur.name
from userrole ur
where ur.userroleid in (
  select urm.userroleid
  from userrolemembers urm
  inner join userinfo u on urm.userid=u.userinfoid
  where u.username = 'admin');

-- Users with ALL authority

select u.userinfoid, u.username, u.firstname, u.surname 
from userinfo u
where u.userinfoid in (
  select urm.userid from userrolemembers urm 
  inner join userrole ur on urm.userroleid=ur.userroleid
  inner join userroleauthorities ura on ur.userroleid=ura.userroleid 
  where ura.authority = 'ALL'
);

-- User roles with ALL authority

select ur.userroleid, ur.name
from userrole ur
inner join userroleauthorities ura on ur.userroleid=ura.userroleid 
where ura.authority = 'ALL';

-- (Write) Bcrypt set password to "district" for admin user up to 2.37

update users set password='$2a$10$wjLPViry3bkYEcjwGRqnYO1bT2Kl.ZY0kO.fwFDfMX53hitfx5.3C', disabled = false where username='admin';

-- (Write) Bcrypt set password to "district" for admin user after 2.37

update userinfo set password='$2a$10$wjLPViry3bkYEcjwGRqnYO1bT2Kl.ZY0kO.fwFDfMX53hitfx5.3C', disabled = false where username='admin';

-- (Write) Add user to first user role with ALL authority 

insert into userrolemembers (userid, userroleid)
select userid, userroleid 
from (
  -- Find username
  select u.userid 
  from userinfo u 
  where u.username = 'admin'
  limit 1) as userid, (
  -- Find first user role with 'ALL' auth
  select ur.userroleid
  from userrole ur 
  inner join userroleauthorities ura on ur.userroleid=ura.userroleid 
  where ura.authority = 'ALL'
  limit 1) as userroleid;
