
class ConfigDict(object):
    '''
    Given a sqlite connection, use it as a config database.

    Creates a new table if one is not present.
    '''

    def __init__(self, connection):
        self.conn = connection
        self.conn.execute('''
            create table if not exists config (
                key text primary key constraint unique_key unique on conflict replace not null,
                value text not null)''')
        self.conn.commit()

    def __getitem__(self, key):
        result = self.conn.execute("select value from config where key = ?", (key,)).fetchone()
        # result is a 1-tuple or None
        if result:
            return result[0]
        else:
            return None

    def __setitem__(self, key, value):
        self.conn.execute("insert into config values (?, ?)", (key, value))
        self.conn.commit()

    def get(self, key, default=None):
        return self[key] or default
