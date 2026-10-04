from pathlib import Path
import sys,copy,unittest,tempfile,shutil,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
from check_assembly_inputs import load_registry,validate_records,check,ACCEPTED
class AssemblyInputTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.records=load_registry(ROOT/'research_inputs/assembly_v1')['records']
 def accepted(self):return copy.deepcopy(next(r for r in self.records if r['Kind']=='DEMAND' and r['AssemblyStatus']==ACCEPTED))
 def test_eleven_baseyear_anchors(self):self.assertEqual(sum(r['Kind']=='DEMAND' and r['AssemblyStatus']==ACCEPTED and r['Year']==2019 for r in self.records),11)
 def test_target_2050_blocks_before_network(self):
  r=check(self.records,2050);self.assertEqual(r['status'],'BLOCKED_INPUT_FREEZE');self.assertEqual(r['accepted_target_demands'],0);self.assertFalse(r['network_construction_started']);self.assertEqual(r['solver_runs'],0)
 def test_unknown_target_does_not_pass_empty(self):
  with self.assertRaises(ValueError):check(self.records,2047)
 def test_baseyear_not_a_forecast(self):
  r=self.accepted();r['Year']=2050
  with self.assertRaises(ValueError):validate_records([r])
 def test_no_duplicate_parent(self):
  r=self.accepted()
  with self.assertRaises(ValueError):validate_records([r,r])
 def test_missing_is_not_zero(self):
  for v in [None,'0','NaN','Infinity',-1]:
   r=self.accepted();r['Value']=v
   with self.subTest(value=v),self.assertRaises(ValueError):validate_records([r])
 def test_assembly_not_human_acceptance(self):
  r=self.accepted();r['AssemblyStatus']='HUMAN_ACCEPTED'
  with self.assertRaises(ValueError):validate_records([r])
 def test_missing_unit_rejected(self):
  r=self.accepted();r['Unit']=''
  with self.assertRaises(ValueError):validate_records([r])
 def test_missing_source_rejected(self):
  r=self.accepted();r['SourceSHA256']=''
  with self.assertRaises(ValueError):validate_records([r])
 def test_resource_unavailable_not_zero_potential(self):
  rows=[r for r in self.records if r['Kind']=='BOUNDARY' and r['Availability']]
  self.assertEqual(len(rows),2);self.assertTrue(all(r['Value'] is None for r in rows))
 def test_hash_tamper_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'inputs';shutil.copytree(ROOT/'research_inputs/assembly_v1',p)
   (p/'registry.json').write_text('{}')
   with self.assertRaises(ValueError):load_registry(p)
 def test_accepted_2019_requires_allocation(self):
  records=copy.deepcopy(self.records)
  for r in records:
   if r['Kind']=='DEMAND' and r['Year']==2019 and r['AssemblyStatus']==ACCEPTED:r['TargetReady']=True
  self.assertEqual(len(check(records,2019)['allocation_missing']),11)
if __name__=='__main__':unittest.main(verbosity=2)
