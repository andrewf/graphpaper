create table if not exists cards (
    id integer primary key,
    title varchar,
    text varchar,
    created date,
    last_modified date
);

create table if not exists edges (
    id integer primary key,
    type integer,
    origin integer,
    destination integer
);

create table if not exists edge_types (
    id integer primary key,
    name varchar,
    color varchar,
    thickness varchar
);

create table if not exists config (
    key varchar,
    value varchar
);


