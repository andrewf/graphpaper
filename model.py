import sqlite3
import hashlib
from os import path

def sha1(dat):
    hasher = hashlib.sha1()
    hasher.update(dat)
    return hasher.hexdigest()

class ConfigDict(object):
    def __init__(self, connection):
        self.conn = connection
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

class DataStore(object):
    '''
    Represents a loaded set of cards, edges and edgetypes

    Construct with a filename. Creates the file if it doesn't exist
    Also includes config
    '''
    def __init__(self, filename, load_sample_data=False):
        '''
        Initialize the data store. If the file doesn't exist, adds the
        infrastructure, and optionally the sample data.
        '''
        # if the file exists, don't load_sample_data
        if path.exists(filename):
            load_sample_data = False
            load_schema = False
        else:
            load_schema = True
        # filename goes to sqlite
        self.conn = sqlite3.connect(filename)
        self.config = ConfigDict(self.conn)
        # now load sample data
        if load_schema: self.load_schema()
        if load_sample_data: self.load_sample_data()
        # load cards into self.cards
        self.cards = []
        for hsh, data in self.conn.execute("select * from cards"):
            self.cards.append(Card(self, hash=hsh, data=data))
    def get_cards(self):
        return self.cards
    def new_card(self, x, y, w, h):
        card = Card(self, x, y, w, h)
        self.cards.append(card)
        return card
    # GraphPaper datastore API. The standard bits
    def create_card(self, data):
        # takes card in string serialize form, adds it to db, returns new id
        new_hash = sha1(data)
        self.conn.execute("insert into cards (key, value) values (?, ?)", (new_hash, data))
        # ignore theoretical collision possibility ^^^
        self.conn.commit()
        return new_hash
    def modify_card(self, old_hash, data):
        '''
        Input hash of old card to change and new data, get a hash
        of the new data, after it's sitting in the db. Returns None on error.
        '''
        # remember, we can rollback on sqlite any time
        # make sure old card exists
        if not self.conn.execute("select * from cards where key = ?", (old_hash,)).fetchone():
            print "old hash %s not found!!! aborting save" % old_hash
            return None
        # add new card
        new_hash = sha1(data)
        # no-op if data is the same: don't want to delete it
        if new_hash == old_hash:
            return old_hash
        # no going back
        self.conn.execute("insert into cards (key, value) values (?, ?)", (new_hash, data))
        self.conn.execute("delete from cards where key = ?", (old_hash,))
        self.conn.commit()
        return new_hash
    def delete_card(self, card_hash):
        # check card exists:
        if not self.conn.execute("select * from cards where key = ?", (card_hash,)):
            print "trying to delete non-existent card!"
            return
        self.conn.execute("delete from cards where key = ?", (card_hash,))
        self.conn.commit()
    def load_schema(self):
        # load it from schema.sql in this dir
        self.conn.executescript(open("schema.sql").read())
        # these have to be there if the file didn't exist
        self.config['viewport_x'] = 0
        self.config['viewport_y'] = 0
        self.config['viewport_w'] = 600
        self.config['viewport_h'] = 400
    def load_sample_data(self):
        for datum in [
            "{-100,-50,200,100}Foobar baz\n\nGrup grup jubyr fret yup.\nfkakeander f.",
            "{10,20,150,300}I'm a card with one line",
            "{200,200,150,100}No edges yet\n\nedges are too hard still. We'll do them later"
        ]:
            self.create_card(datum)


class InvalidCard(Exception):
    pass

class Card(object):
    '''
    A single card. All properties, when written, write to the
    data store. For now, that means it hits sqlite which (I think)
    hits the disk. Someday we'll do something more intelligent.
    Probably after a rewrite.

    members:
    * hash: the current id as supplied by the data store
    * _x, _y, _w, _h: position and dimensions of card
    * _text: text of the card
    * x, y, w, h, text: properties that save when modified
    '''
    def __init__(self, datastore, *args, **kwargs):
        '''
        Creates a representation of a card object. Must be called in one
        of two ways
        
        Card(datastore, hash=<hash>, data=<data>)
        Card(datastore, x, y, w, h)

        The first form is for loading a card from the store. The second is
        for creating new cards. I'm not going to do much checking, so be
        careful.
        '''
        self.datastore = datastore
        # there should either be args or kwargs, but not both. just assume it:
        if kwargs:
            # loading
            self.hash = kwargs['hash']
            self.unpack(kwargs['data']) # let errors out
        else:
            # new card, with no hash yet
            assert len(args) == 4
            self._x = args[0]
            self._y = args[1]
            self._w = args[2]
            self._h = args[3]
            self._text = ''
            # save it and keep id
            self.hash = self.datastore.create_card(str(self))
    def get_x(self): return self._x
    def get_y(self): return self._y
    def get_w(self): return self._w
    def get_h(self): return self._h
    def get_text(self): return self._text
    def save(self):
        # write self in standard format
        # send command to datastore
        self.hash = self.datastore.modify_card(self.hash, str(self))
    def set_pos(self, x, y):
        self._x = x
        self._y = y
        self.save()
    def set_dimensions(self, w, h):
        self._w = w
        self._h = h
        self.save()
    def set_x(self, x):
        self._x = x
        self.save()
    def set_y(self, y):
        self._y = y
        self.save()
    def set_w(self, w):
        self._w = w
        self.save()
    def set_h(self, h):
        self._h = h
        self.save()
    def set_text(self, text):
        self._text = text
        self.save()
    x = property(get_x, set_x)
    y = property(get_y, set_y)
    w = property(get_w, set_w)
    h = property(get_h, set_h)
    text = property(get_text, set_text)
    def __str__(self):
        return '{%d,%d,%d,%d}%s' % (
            self._x,
            self._y,
            self._w,
            self._h,
            self.text
        )
    def unpack(self, string):
        # unpacks self from format created in above string
        # raises InvalidCard if data is bad
        if string[0] != '{':
            raise InvalidCard("expected '{' at beginning")
        end_of_header = string.find('}')
        if end_of_header == -1:
            raise InvalidCard("header is not terminated, expected '}'")
        header = string[1:end_of_header]
        header_values = header.split(',')
        # header_values should be a list of four integers
        if not len(header_values) == 4:
            raise InvalidCard("wrong number of header items")
        try:
            header_values = map(int, header_values)
        except ValueError:
            raise InvalidCard("header items must be integers")
        # width and height must be > 0
        if not header_values[2] > 0:
            raise InvalidCard("width must be > 0")
        if not header_values[3] > 0:
            raise InvalidCard("height must be > 0")
        # copy values
        self._x = header_values[0]
        self._y = header_values[1]
        self._w = header_values[2]
        self._h = header_values[3]
        self._text = string[end_of_header+1:]
    def delete(self):
        self.datastore.delete_card(self.hash)

class Edge:
    pass

class EdgeType:
    pass
