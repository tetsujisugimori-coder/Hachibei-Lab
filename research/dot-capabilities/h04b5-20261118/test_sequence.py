import unittest
from sequence import ORDER,validate
class Tests(unittest.TestCase):
 def test_normal(self):self.assertEqual(validate(ORDER),{'status':'PASS','permit':False})
 def test_empty(self):self.assertEqual(validate([])['status'],'NOT_TESTED')
 def test_prefix(self):self.assertEqual(validate(ORDER[:6])['status'],'PARTIAL')
 def test_missing(self):
  for i in range(len(ORDER)-1):self.assertEqual(validate(ORDER[:i]+ORDER[i+1:])['status'],'BLOCKED')
 def test_b1_early(self):self.assertEqual(validate(['B1_CREATE']+ORDER)['status'],'BLOCKED')
 def test_retry(self):self.assertEqual(validate(ORDER[:2]+['B0_SEND']+ORDER[2:])['status'],'BLOCKED')
if __name__=='__main__':unittest.main()
