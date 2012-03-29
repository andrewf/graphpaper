import minijson

class Error(Exception):
    pass

class KeyError(Error):
    pass

class Storable(dict):
    '''
    Easy interface for storing dicts in a KVStore.
    Object acts like a dict, but adds a save method that takes
    a kvstore and returns the stored id.
    '''

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.oid = None

    def load(self, datastore, oid):
        dat = datastore.get(oid)
        if dat:
            try:
                dat = minijson.decode(dat)       
                if isinstance(dat, dict):
                    self.clear()
                    self.update(dat)
                    self.oid = oid
                else:
                    raise Error('StorableDict must be loaded from dict, key: %s' % oid)
            except ValueError:
                raise Error('StorableDict data at %s is invalid' % oid)
        else:
            raise Error('StorableDict got invalid key: %s' % oid)
    
    def save(self, datastore):
        self.oid = datastore.store(minijson.encode(self))
        return self.oid

    def __setitem__(self, *args):
        self.oid = None
        dict.__setitem__(self, *args)
