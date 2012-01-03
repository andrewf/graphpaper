all: test.sqlite

clean:
	rm -f test.sqlite

test.sqlite: test.sql schema.sql
	rm -f test.sqlite
	sqlite3 test.sqlite < schema.sql
	sqlite3 test.sqlite < test.sql
	python load_test_data.py

