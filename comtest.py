# script for testing data model integrity and stuff

import sqlite3
import os

from kvstore import KVStore
from model import *

dat = KVStore(sqlite3.connect(':memory:'), 'objects')

g = Graph(dat, None)

c = g.new_card()
c.obj['text'] = 'card 1'

g.commit()

c2 = g.new_card()
c2.obj['text'] = 'number 2'

g.commit()

c.delete()
c2.obj['text'] = 'number 2\n\nyeah!'

last_commit = g.commit()

for k,v in dat.getall():
    print k, ':'
    print '   ', v

# now load it fresh
g2 = Graph(dat, last_commit)
assert g2.cards[0].obj.oid == g.cards[0].obj.oid


