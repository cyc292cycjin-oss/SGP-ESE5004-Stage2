"""Actual pinned topology plus targeted corruption checks. Never builds/solves."""
from pathlib import Path
import sys,unittest,copy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
from research_topology import inspect,tables
class TopologyTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.t=tables(ROOT/'data/osm-plus-prebuilt/0.1.1')
 def test_actual_all_references_valid(self):self.assertEqual(inspect(self.t)['issues'],[])
 def test_765_is_retained_766_not_fabricated(self):
  ids={r['bus_id'] for r in self.t['Bus']};self.assertIn('765',ids);self.assertNotIn('766',ids)
 def test_obsolete_transformer_absent(self):self.assertFalse(any(r['line_id']=='transf_524_0' for r in self.t['Transformer']))
 def test_missing_line_endpoint_detected(self):
  t=copy.deepcopy(self.t);t['Line'][0]['bus1']='MISSING';self.assertTrue(inspect(t)['issues'])
 def test_missing_converter_endpoint_detected(self):
  t=copy.deepcopy(self.t);t['Link'][0]['bus1']='MISSING';self.assertTrue(inspect(t)['issues'])
 def test_missing_transformer_endpoint_detected(self):
  t=copy.deepcopy(self.t);t['Transformer'][0]['bus1']='MISSING';self.assertTrue(inspect(t)['issues'])
 def test_duplicate_bus_rejected(self):
  t=copy.deepcopy(self.t);t['Bus'].append(t['Bus'][0]);self.assertTrue(inspect(t)['issues'])
 def test_unknown_country_rejected(self):
  t=copy.deepcopy(self.t);t['Bus'][0]['country']='';self.assertTrue(inspect(t)['issues'])
 def test_nonfinite_coordinate_rejected(self):
  t=copy.deepcopy(self.t);t['Bus'][0]['lon']='NaN';self.assertTrue(inspect(t)['issues'])
if __name__=='__main__':unittest.main(verbosity=2)
