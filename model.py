class DataStore(object):
    '''
    Represents a loaded set of cards, edges and edgetypes

    Construct with a filename. Creates the file if it doesn't exist
    Also includes config
    '''
    def __init__(self, filename):
        # filename goes to sqlite
        # we'll make up fake data for now
        self.config = { # TODO: replace with custom dict-like obj
            'viewport_x': -120,
            'viewport_y': -100,
            'viewport_w': 600,
            'viewport_h': 400
        }
        self.cards = [
            Card(self, -100, -50, 200, 100, "Foobar baz\n\nGrup grup jubyr fret yup.\nfkakeander f."),
            Card(self, 10, 20, 150, 300, "I'm a card with one line"),
            Card(self, 200, 200, 150, 100, "No edges yet\n\nedges are too hard still. We'll do them later. Namespaces are a honking great idea. let's do more of those. wait, what?"),
        ]
    def get_cards(self):
        return self.cards
    def new_card(self, x, y, w, h, text=''):
        card = Card(self, x, y, w, h, text)
        self.cards.append(card)
        return card


class Card(object):
    '''
    A single card. All properties, when written, write to the
    data store. For now, that means it hits sqlite which (I think)
    hits the disk. Someday we'll do something more intelligent.
    Probably after a rewrite.
    '''
    def __init__(self, datastore, x, y, w, h, text):
        self.datastore = datastore
        self._x = x
        self._y = y
        self._w = w
        self._h = h
        self._text = text
    def get_x(self): return self._x
    def get_y(self): return self._y
    def get_w(self): return self._w
    def get_h(self): return self._h
    def get_text(self): return self._text
    def save(self):
        # write self in standard format
        # send command to datastore
        pass
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

class Edge:
    pass

class EdgeType:
    pass
