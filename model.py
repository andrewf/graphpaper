'''
Contains the latest version of the basic data model classes.
'''

import storable

COMMIT_OBJTYPE = 'commit'
CARD_OBJTYPE = 'card'
EDGE_OBJTYPE = 'edge'
objtype = 'objtype'

MIN_CARD_SIZE = 70

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
                if not self.obj[objtype] == COMMIT_OBJTYPE:
                    raise Error('Graph found invalid commit %s' % oid)
                # check schema?
                # all good
        else:
            self.load_empty_graph()
        # while loading cards, build dict of oids to cards
        # we only need this during loading phase to give to edge constructors
        card_dict = {}
        self.cards = []
        for oid in self.obj['cards']:
            c = Card(self, oid)
            card_dict[oid] = c
            self.cards.append(c)
        card_mapper = lambda oid: card_dict.get(oid, None)
        self.edges = [Edge(self, oid, card_mapper) for oid in self.obj['edges']]

    def get_cards(self):
        '''
        Return all cards, somehow, as model.Card's
        '''
        return self.cards

    def get_edges(self):
        "as get_cards()"
        return self.edges

    def new_card(self, x=0, y=0, w=MIN_CARD_SIZE, h=MIN_CARD_SIZE):
        c = Card(self, None)
        c.x = x
        c.y = y
        c.w = w
        c.h = h
        self.cards.append(c)
        return c

    def new_edge(self, orig, dest):
        e = Edge(self, orig=orig, dest=dest)
        self.edges.append(e)
        return e

    def commit(self):
        '''
        Save a new commit object

        Save all the cards, delete those that want to be deleted, get
        the remaining hashes, and stuff it all in the datastore.
        '''
        old_id = self.obj.oid
        # make sure obj.oid is None for any edges invalid now
        # since we're about to save all the cards and otherwise
        # edge.dirty would no longer be true and edges wouldn't get updated
        for edge in self.edges:
            if edge.dirty:
                edge.invalidate() # sets edge.obj.oid = None
        to_delete = []
        # update card ids
        for card in self.cards:
            if card.delete_me:
                to_delete.append(card)
            elif card.dirty:
                card.save()
        for card in to_delete:
            self.cards.remove(card) # TODO: more efficient algo
        # reuse deletion list for cards
        to_delete = []
        # update edge ids
        # must be BEFORE cards, so edges will know which cards' hashes
        # changed.
        for edge in self.edges:
            if edge.delete_me:
                to_delete.append(edge)
            elif edge.dirty:
                edge.save()
        for edge in to_delete:
            self.edges.remove(edge)
        # load up new commit object
        get_oid = lambda c: c.obj.oid
        self.obj['cards'] = map(get_oid, self.cards)
        self.obj['edges'] = map(get_oid, self.edges)
        self.obj['parent'] = old_id
        return self.obj.save(self.datastore)

    def load_empty_graph(self):
        '''
        Initialize self.obj with data for an empty graph.

        Make parent null, and empty lists of cards and edges
        '''
        self.obj[objtype] = COMMIT_OBJTYPE
        self.obj['parent'] = None
        self.obj['cards'] = []
        self.obj['edges'] = []


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
                if not self.obj[objtype] == CARD_OBJTYPE:
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
        self.obj[objtype] = CARD_OBJTYPE
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


class Edge(object):
    def __init__(self, graph, oid=None, card_by_oid=None, **kwargs):
        '''
        Load self from datastore, or create new Edge

        Must be called in one of two ways:
         * Edge(graph, oid, id_map(oid)->model.Card), when loading from a commit
         * Edge(graph, orig=model.Card, dest=model.Card), when creating from scratch

        In the first case, the second parameter is a function mapping card oids
        to the corresponding model.Card. Edge needs to keep track of the actual
        Card object, and has no other way to get it from the oids in its data.
        The function should return None if it can't find the card.

        In the second case, oid is None and both keyword args must be present.
        Someday it will accept other parameters for edge type and whatever else,
        but for now any other kwargs will be ignored.
        '''
        self.graph = graph
        self.obj = storable.Storable()
        if oid is not None:
            # load from kvstore
            try:
                self.obj.load(self.graph.datastore, oid)
            except storable.Error:
                raise Error('Failed to find edge %s' % oid)
            # validate
            # edge must have objtype == 'edge' and orig & dest in set of cards
            try:
                if not self.obj[objtype] == EDGE_OBJTYPE:
                    raise Error('Alleged edge %s has wrong objtype' % oid)
                self._orig = card_by_oid(self.obj['orig'])
                if not self._orig:
                    raise Error('Edge %s has invalid origin card id %s' % (oid, self.obj['orig']))
                self._dest = card_by_oid(self.obj['dest'])
                if not self._dest:
                    raise Error('Edge %s has invalid dest card id %s' % (oid, self.obj['dest']))
            except KeyError as e:
                raise Error('Edge %s is missing required field %s' % (oid, e))
        else:
            # create fresh edge
            # not much to do here. most work will be done when saving, which
            # gets the referenced cards' ids into self.obj
            self.obj[objtype] = EDGE_OBJTYPE
            try:
                self._orig = kwargs['orig']
                self._dest = kwargs['dest']
            except KeyError as e:
                raise Error('Missing required Edge fresh-construction argument %s' % e)
        self._delete_me = False
 
    def save(self):
        '''
        Make sure card oids are up to date and save data

        This function basically assumes it is being called right after you went
        through all the cards in a graph and saved them. It has to get their
        new ids and save them in itself to keep the graph consistent.
        '''
        # do nothing if already saved
        if not self.dirty:
            return self.obj.oid
        # load origin
        if self._orig.obj.oid:
            self.obj['orig'] = self._orig.obj.oid
        else:
            raise Error('Failed to save edge: origin card has not been saved')
        # load dest
        if self._dest.obj.oid:
            self.obj['dest'] = self._dest.obj.oid
        else:
            raise Error('Failed to save edge: dest card has not been saved')
        # ok, now really save
        return self.obj.save(self.graph.datastore)

    def set_orig(self, new):
        "Set origin card, do bookkeeping"
        assert new.graph is self.graph
        self._orig = new
        self.obj['orig'] = '' # invalidate
    def get_orig(self):
        return self._orig
    orig = property(get_orig, set_orig)
    
    def set_dest(self, new):
        "Set dest card, plus bookkeeping"
        assert new.graph is self.graph
        self._dest = new
        self.obj['dest'] = ''
    def get_dest(self):
        return self._dest
    dest = property(get_dest, set_dest)

    @property
    def dirty(self):
        return self.obj.oid is None or self._orig.dirty or self._dest.dirty

    def invalidate(self):
        "make self.dirty true, in cases where we know better"
        self.obj.oid = None

    @property
    def delete_me(self):
        # note that for this to work, both cards have to be not actually
        # deleted yet. GC should handle this fine...
        return self._delete_me or self._orig.delete_me or self._dest.delete_me

