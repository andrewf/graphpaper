'''
Contains the latest version of the basic data model classes.
'''

import storable

COMMIT_OBJTYPE = 'commit'
CARD_OBJTYPE = 'card'

MIN_CARD_SIZE = 20

class Error(Exception):
    pass

class Graph(object):
    '''
    Interface for managing and saving a version of the graph.

    Members:
    * datastore: a kvstore.KVStore used to store everything.
    '''

    def __init__(self, datastore, oid):
        '''
        Load the graph specified by the commit from the datastore.

        If oid is None, create empty graph. If oid is invalid or not
        a commit, error out.
        '''
        self.obj = storable.Storable()
        self.datastore = datastore
        if oid:
            try:
                self.obj.load(datastore, oid)
            except storable.KeyError:
                # key missing
                raise Error('Can\'t find commit %s' % oid)
            except storable.Error:
                raise Error('commit %s is invalid?' % oid)
            else:
                # loaded successfully
                # check validity
                if not self.obj['objtype'] == COMMIT_OBJTYPE:
                    raise Error('Graph found invalid commit %s' % oid)
                # check schema?
                # all good
                self.oid = oid
        else:
            self.load_empty_graph()
        # can now assume self.oid and self.obj are good
        self.cards = [Card(self, oid) for oid in self.obj['cards']]

    def get_cards(self):
        '''
        Return all cards, somehow, as model.Card's
        '''
        return self.cards

    def new_card(self, x=0, y=0, w=MIN_CARD_SIZE, h=MIN_CARD_SIZE):
        c = Card(self, None)
        c.x = x
        c.y = y
        c.w = w
        c.h = h
        self.cards.append(c)
        return c

    def commit(self):
        '''
        Save a new commit object

        Save all the cards, delete those that want to be deleted, get
        the remaining hashes, and stuff it all in the datastore.
        '''
        old_id = self.obj.oid
        to_delete = []
        for card in self.cards:
            if card.delete_me:
                to_delete.append(card)
            elif card.dirty:
                card.save()
        for card in to_delete:
            self.cards.remove(card) # TODO: more efficient algo
        #for edge in all_edges:
        #    if edge.delete_me:
        #        add to list
        #    edge.regenerate() # loads new card ids,
        #clear to_delete list
        self.obj['cards'] = map(lambda c: c.obj.oid, self.cards)
        #self.obj['edges'] = updated list of edge ids
        self.obj['parent'] = old_id
        return self.obj.save(self.datastore)

    def load_empty_graph(self):
        '''
        Initialize self.obj with data for an empty graph.

        Make parent null, and empty list of cards
        '''
        self.obj['objtype'] = COMMIT_OBJTYPE
        self.obj['parent'] = None
        self.obj['cards'] = []


class Card(object):
    '''
    Wraps a Storable to represent a card
    '''

    def __init__(self, graph, oid=None):
        '''
        Load self from datastore, or create new card

        If oid is invalid, error. If oid is None, create new card.
        '''
        self.graph = graph
        self.obj = storable.Storable()
        if oid is not None:
            try:
                self.obj.load(self.graph.datastore, oid)
            except storable.Error:
                raise Error('Failed to find card %s' % oid)
            # validate card
            try:
                if not self.obj['objtype'] == CARD_OBJTYPE:
                    raise Error('Invalid card at %s' % oid)
            except KeyError:
                raise Error('Alleged card has no objtype at %s' % oid)
            for prop in ('text', 'x', 'y', 'w', 'h'):
                if not prop in self.obj:
                    raise Error('Card missing property "%s" at %s' % (prop, oid))
        else:
            self.load_empty_card()
        # initialize deletion flag
        self._delete_me = False

    def load_empty_card(self):
        self.obj['objtype'] = CARD_OBJTYPE
        self.obj['text'] = ''
        self.x = 0
        self.y = 0
        self.w = MIN_CARD_SIZE
        self.h = MIN_CARD_SIZE        

    def save(self):
        return self.obj.save(self.graph.datastore)

    def delete(self):
        self._delete_me = True

    def set_x(self, x):
        self.obj['x'] = x
    def get_x(self):
        return self.obj['x']
    x = property(get_x, set_x)

    def set_y(self, y):
        self.obj['y'] = y
    def get_y(self):
        return self.obj['y']
    y = property(get_y, set_y)

    def set_w(self, w):
        self.obj['w'] = max(w, MIN_CARD_SIZE)
    def get_w(self):
        return self.obj['w']
    w = property(get_w, set_w)

    def set_h(self, h):
        self.obj['h'] = max(h, MIN_CARD_SIZE)
    def get_h(self):
        return self.obj['h']
    h = property(get_h, set_h)

    def set_text(self, text):
        self.obj['text'] = text
    def get_text(self):
        return self.obj['text']
    text = property(get_text, set_text)

    @property
    def delete_me(self):
        return self._delete_me
    
    @property
    def dirty(self):
        return self.obj.oid is None


