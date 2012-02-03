import sqlite3
import re
from os import path

import minijson

class DataStoreV1(object):
    '''
    OBSOLETE: Represents a loaded set of cards in the old format.

    Construct with a filename. Creates the file if it doesn't exist
    Also includes config
    '''
    def __init__(self, conn):
        '''
        Initialize the data store. If the file doesn't exist, adds the
        infrastructure, and optionally the sample data.
        '''
        self.conn = conn
        # load cards into self.cards
        self.cards = []
        for hsh, data in self.conn.execute("select * from cards"):
            self.cards.append(Card(self, hash=hsh, data=data))
    def get_cards(self):
        return self.cards

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
        return minijson.encode({
            'objtype': 'card',
            'x': int(self._x),
            'y': int(self._y),
            'w': int(self._w),
            'h': int(self._h),
            'text': self._text,
        })

    def unpack(self, string):
        old_regex = re.compile(
            r'''{(?P<x>-?\d+),(?P<y>-?\d+),(?P<w>-?\d+),(?P<h>-?\d+)}(?P<text>.*)''',
            flags = re.MULTILINE | re.DOTALL # must match multiple lines of text
        )
        match = old_regex.match(string)
        if match:
            # this is an old-format card
            self._x = int(match.group('x'))
            self._y = int(match.group('y'))
            self._w = int(match.group('w'))
            self._h = int(match.group('h'))
            self._text = match.group('text')
        else:
            try:
                data = minijson.decode(string)
                self._x = data['x']
                self._y = data['y']
                self._w = data['w']
                self._h = data['h']
                self._text = data['text']
            except ValueError:
                raise InvalidCard("Could not parse card at all!")
            except KeyError:
                raise InvalidCard("Card data did not contain all required fields!")
        # make sure w and h are valid
        if self._w <= 0:
            raise InvalidCard('Card width must be > 0!')
        if self._h <= 0:
            raise InvalidCard('Card height must be > 0!')

    def delete(self):
        self.datastore.delete_card(self.hash)

