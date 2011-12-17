create table if not exists cards (
    id integer primary key,
    title text,
    text text,
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
    name text,
    color text,
    thickness text
);

create table if not exists config (
    key text constraint unique_key unique on conflict replace,
    value text
);


