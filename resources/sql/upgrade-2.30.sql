-- Update "See <AppName>" authority to "M_See_<Appname>"
update userroleauthorities set authority = 'M_' || replace(authority, ' ', '_') where authority like 'See%';