#!/bin/sh

dbnames="sample test"

for db in ${dbnames}; do
    rm -f ${db}.database;
    sqlite3 ${db}.database < schema.sql
    sqlite3 ${db}.database < ${db}.sql
done;



