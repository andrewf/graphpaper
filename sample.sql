-- Sample topology:
--
--       hi there           Joke      this is really dumb
--       /       \             \       /
--      /         \             \     /
--     v           v             v   v
--   Edges        Cards        So he says...
 
 
 
insert into cards (title, text) values ("hi there", "Welcome to graph paper");
insert into cards (title, text) values ("Edges", "Edges are connections between cards.");
insert into cards (title, text) values ("Cards", "Cards can hold any text you want them to.");

insert into cards (title, text) values ("Joke", "A man walks into a bar");
insert into cards (title, text) values ("So he says...", "Ouch.");
insert into cards (title, text) values ("this is really dumb", "");

insert into edges (origin, destination) values (1, 2);
insert into edges (origin, destination) values (1, 3);
insert into edges (origin, destination) values (4, 5);
insert into edges (origin, destination) values (6, 5);

insert into config values ("autosave", 1);
insert into config values ("color", "blue");