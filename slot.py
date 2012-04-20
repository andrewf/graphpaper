'''
Extremely basic signal/slot class

Just store a dict of ints to callbacks.
'''

class Slot(object):
    '''
    Stores a list of callables, and calls them with the
    args passed to self.signal.
    '''
    def __init__(self):
        self.d = {} # {int: callable}
        self.n = 0 # counter for keys

    def add(self, fn):
        key = self.n
        self.n += 1
        self.d[key] = fn
        return key

    def remove(self, handle):
        try:
            del self.d[handle]
        except KeyError:
            pass
    
    def signal(self, *args, **kwargs):
        # make a copy of the dict and iterate through
        # that, so callbacks can remove themselves
        copy = dict(self.d)
        for fn in copy.itervalues():
            fn(*args, **kwargs)

