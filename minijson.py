'''
Provides a standard data format with unique representations of data. That
is, each set of data has exactly one representation. To that effect, we
render the data is minified json and encode it as utf-8.
'''

import unittest
import json

def encode(data):
    return json.dumps(data, encoding='utf-8', separators = (',', ':'), sort_keys=True)

def decode(minijson):
    return json.loads(minijson)

class TestMiniJson(unittest.TestCase):
    def testAll(self):
        for reference, data in [
            (r'''{}''', {}),
            (r'''{"objtype":"card","text":"title\n\n\"body\" text","x":34}''', {'objtype':'card', 'x': 34, "text":'''title\n\n"body" text'''}),
            (r'''{"cards":["abcd","de43"],"objtype":"manifest","parent":"abcdef123456"}''', {'objtype': 'manifest', 'parent': 'abcdef123456', 'cards': ['abcd', 'de43']}),
        ]:
            self.assertEqual(encode(data), reference.encode('utf-8'))

if __name__ == '__main__':
    unittest.main()
