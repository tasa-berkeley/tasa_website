drop table if exists events;
create table events (
  id integer primary key autoincrement,
  title text not null,
  time text not null,
  location text not null,
  link text not null,
  image_url text not null,
  unix_time int not null
  attendance	INTEGER DEFAULT 0,
	new_attendance	INTEGER DEFAULT 0,
	returning_attendance	INTEGER DEFAULT 0
);

drop table if exists officers;
create table officers (
	id integer primary key autoincrement,
	name text not null,
	year integer not null,
	major text not null,
	quote text not null,
	description text not null,
	image_url text not null,
	position integer not null,
	href text not null
);

drop table if exists families;
create table families(
    id integer primary key autoincrement,
    family_name text not null,
    family_head1 text not null,
    family_head2 text not null,
    family_head_intern text not null,
    description text not null,
    image_url text not null
);

drop table if exists files;
create table files(
    id integer primary key autoincrement,
    name text not null,
    file_url text not null
);

drop table if exists members;
create table members(
    id integer primary key autoincrement,
    name text not null,
    year text not null
    email text not null
    findable integer not null
    checkins integer not null
);

drop table if exists event_checkins;
create table event_checkins(
  eventID integer not null
  eventName text not null
  memberID integer not null
  memberName text not null
);

drop table if exists late_jars;
create table late_jars(
  id integer primary key autoincrement,
  difficulty TEXT NOT null,
  jar TEXT NOT null
);

