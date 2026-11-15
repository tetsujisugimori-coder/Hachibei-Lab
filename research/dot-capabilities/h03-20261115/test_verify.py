"""Synthetic controls only; never actual cross-thread evidence."""
import unittest
from verify import compare
class Controls(unittest.TestCase):
    def test_normal(self):
        b='架空合成\n'.encode(); self.assertEqual(compare(b,b,b+'確認済み\n'.encode())['automatic_sharing'],'UNKNOWN')
    def test_wrong_restatement(self):
        with self.assertRaisesRegex(ValueError,'restatement'): compare('架空合成\n'.encode(),b'foreign',b'')
    def test_wrong_revision(self):
        b='架空合成\n'.encode()
        with self.assertRaisesRegex(ValueError,'revision'): compare(b,b,b)
    def test_empty(self):
        with self.assertRaisesRegex(ValueError,'format'): compare(b'',b'',b'')
if __name__=='__main__': unittest.main()
