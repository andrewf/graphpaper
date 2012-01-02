create table if not exists cards (
    key text unique not null primary key,
    value text
);

create table if not exists edges (
    key text unique not null primary key,
    value text
);

create table if not exists edgetypes (
    key text unique not null primary key,
    value text
);
-- maybe the keys should be blobs?

