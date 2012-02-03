
import hashlib
import re

def sha1(dat):
    hasher = hashlib.sha1()
    hasher.update(dat)
    return hasher.hexdigest()

tablename_re = re.compile(r'^[a-zA-Z][\w]*$')
def is_valid_tablename(name):
    return tablename_re.match(name) is not None

class KVStore(object):
    '''
    Puts a basic hash-based key-value interface on sqlite

    Two basic operations: get(key) -> value and store(value) -> key.
    Underneath, it SHA1s the data to get the key.
    '''

    def __init__(self, conn, tablename):
        '''
        Use the named table in the sqlite connection to store values.
        Create the table if necessary.
        '''
        self.conn = conn
        if is_valid_tablename(tablename):
            self.tablename = tablename
        else:
            raise ValueError('invalid tablename: "%s"' % tablename)
        # create the table if it doesn't exist with proper constraints
        # I think we'll do the uniqueness checking manually
        self.conn.execute('''
            create table if not exists %s (
                key text unique primary key not null,
                value text)''' % self.tablename)
        self.conn.commit()

    def get(self, key):
        '''
        Get the blob referred to or None
        '''
        cur = self.conn.execute('''
            select value from %s where key = ?
        ''' % self.tablename, (key,))
        result = cur.fetchone()
        if result:
            return result[0]
        return None

    def store(self, value):
        '''
        Store a blob, return the key. Raise ValueError if there's a collision.
        Hope springs eternal...
        '''
        key = sha1(value)
        cur_value = self.get(key)
        if cur_value is not None:
            if cur_value == value:
                return key
            else:
                raise ValueError('holy crap, SHA1 collision! """%s""", """%s"""' % (repr(value), repr(cur_value)))
        # key is new
        self.conn.execute('''
            insert into %s values (?, ?)
        ''' % self.tablename, (key, value))
        self.conn.commit()
        return key

    def getall(self):
        return list(self.conn.execute('select * from %s' % self.tablename))

