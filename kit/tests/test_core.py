import unittest,tempfile,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dfir_kit as k
class Core(unittest.TestCase):
 def test_time(self):
  self.assertEqual(k.normalize({'time':'2026-01-01T01:00:00+01:00'})['time_utc'],'2026-01-01T00:00:00+00:00')
 def test_naive(self): self.assertIsNone(k.normalize({'time':'2026-01-01T00:00:00'})['time_utc'])
 def test_bad_time(self): self.assertIsNone(k.normalize({'time':'bad'})['time_utc'])
 def test_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'a').write_text('original');k.manifest(p)
   self.assertTrue(k.verify(p));(p/'a').write_text('changed');self.assertFalse(k.verify(p))
 def test_import(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);c=p/'case';c.mkdir();s=p/'s';s.write_text('evidence');k.import_file(c,s)
   self.assertEqual(k.digest(s),k.digest(next((c/'imports').iterdir())))
 def test_rules(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);f=p/'events.csv';f.write_text('time,source,event_id\n2026-01-01T00:00:00Z,test,1102\n2026-01-01T00:01:00Z,test,4624\n')
   k.analyze(p,f);r=json.loads((p/'analysis/findings.json').read_text());self.assertEqual(len(r),1);self.assertEqual(r[0]['assessment'],'review_required')
