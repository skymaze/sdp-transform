import os
import unittest

from sdp_transform import *


class TestMethods(unittest.TestCase):
    def test_all(self):
        filenames = os.listdir('tests/sdps')
        for filename in filenames:
            if filename.endswith('sdp'):
                with open(f'tests/sdps/{filename}') as f:
                    print(filename)
                    sdp = f.read()
                    sdpDict1 = parse(sdp)
                    sdpStr = write(sdpDict1)
                    sdpDict2 = parse(sdpStr)
                    self.assertDictEqual(sdpDict1, sdpDict2)

if __name__ == '__main__':
    unittest.main()