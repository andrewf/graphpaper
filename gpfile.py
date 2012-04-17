from config import ConfigDict
import sqlite3

import model
import model_v1
import kvstore


class Error(Exception):
    pass

class CorruptionError(Error):
    '''
    For when the file format is invalid
    '''
    pass

# The name for version two objects to live in
# in case we need different tablenames for different formats.
V2_TABLENAME = 'objects_v2'

class GraphPaperFile(object):
    '''
    A loaded file. Coordinates migration, presents a model.Graph to the world.
    '''

    def __init__(self, filename):
        # must have self.graph valid at end of constructor
        # sqlite open file
        self.conn = sqlite3.connect(filename)
        fresh_file = not table_exists(self.conn, 'config') # before making ConfigDict
        self.config = ConfigDict(self.conn)
        datastore = kvstore.KVStore(self.conn, V2_TABLENAME)
        # check for config format version
        version = self.config['version']
        if fresh_file:
            print 'fresh file'
            self.graph = model.Graph(datastore, None)
            self.load_default_config()
            self.commit()
        else:
            if self.config['version'] is None:
                # if no conf, migrate by creating empty graph, creating cards
                # and loading it from a v1 DataStore
                self.graph = model.Graph(datastore, None)
                self.import_v1()
            # else, load commit
            elif version == '2':
                head_ptr = self.config['head']
                if head_ptr is None:
                    raise CorruptionError('No head pointer!')
                try:
                    self.graph = model.Graph(datastore, head_ptr)
                    # after this, should be all loaded
                except model.Error as e:
                    print 'failed to open gp file:', e
                    raise ValueError

    def load_default_config(self):
        "Default configuration for new files, including version number"
        for k, v in (
            ('viewport_x', '0'),
            ('viewport_y', '0'),
            ('viewport_w', '600'),
            ('viewport_h', '400'),
            ('version', '2')):
            self.config[k] = v


    def import_v1(self):
        '''
        create DataStoreV1 and import all cards from it to self.graph
        '''
        v1_data = model_v1.DataStoreV1(self.conn)
        for card in v1_data.get_cards():
            c = self.graph.new_card()
            c.x = card.x
            c.y = card.y
            c.w = card.w
            c.h = card.h
            c.text = card.text
        self.commit()
        self.config['version'] = '2'
        self.conn.execute('drop table cards')

    def commit(self):
        self.config['head'] = self.graph.commit()



def table_exists(conn, tablename):
    return bool(list(conn.execute(
        '''select name from sqlite_master where type=\'table\' and name=?''',
        (tablename,))))

