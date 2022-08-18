-- Updates sort order for category options within a category to fix "holes" in the index

-- Drop primary key, create sequence

alter table categories_categoryoptions drop constraint if exists categories_categoryoptions_pkey;
drop sequence if exists sortorder;
create sequence sortorder minvalue 1 start 1;

-- Update sort_order for category options (update category id to the relevant category)

update categories_categoryoptions
set sort_order = nextval('sortorder')
where categoryid=492298;

-- Put back primary key, drop sequence

alter table categories_categoryoptions add constraint categories_categoryoptions_pkey primary key(categoryid, sort_order);
drop sequence sortorder;
