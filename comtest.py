# script for testing data model integrity and stuff

import sqlite3
import os

from kvstore import KVStore
from model import *

dat = KVStore(sqlite3.connect(':memory:'), 'objects')

g = Graph(dat, None)

c = g.new_card()
c.obj['text'] = 'card 1'
c2 = g.new_card()
c2.obj['text'] = 'number 2'
c3 = g.new_card()
c3.obj['text'] = 'numero tres'

g.commit()

# make an edge
e1 = g.new_edge(c, c2)
e2 = g.new_edge(c3, c2)

g.commit()

# modify more stuff
e2._delete_me = True
c._delete_me = True

last_commit = g.commit()

for k,v in dat.getall():
    print '#', k, ':'
    print '   ', v

# now load it fresh
g2 = Graph(dat, last_commit)

assert set(g.obj['cards']) == set(g2.obj['cards'])
assert set(g.obj['edges']) == set(g2.obj['edges'])

