-- A very tiny test database

insert into cards (title, text) values ("card 1", "I am the first card");
insert into cards (title, text) values ("card 2", "I am number two");

insert into edges (origin, destination) values (1, 2);

insert into config values ("autosave", 1);
insert into config values ("color", "blue");
