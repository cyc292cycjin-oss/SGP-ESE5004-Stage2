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
  old=json.loads((ROOT/'tests/research/fixtures/gate4_before_continue.json').read_text())['records']
  r=check(old,2050);self.assertEqual(r['status'],'BLOCKED_INPUT_FREEZE');self.assertEqual(r['accepted_target_demands'],0);self.assertFalse(r['network_construction_started']);self.assertEqual(r['solver_runs'],0)
  self.assertEqual(r['required_target_demands'],264)
  self.assertGreaterEqual(r['numeric_accepted_target_demands'],17)
  self.assertEqual(r['external_supply_pending'],[])
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
 def test_road_ev_cannot_be_zero_or_a_load(self):
  ev=next(r for r in self.records if r['Account']=='RoadEVFinalElectricity' and r['Year']==2050)
  for patch in [{'Value':'0'},{'Kind':'DEMAND'},{'Required':True},{'ParentAccount':''},{'Representation':'EXPLICIT'}]:
   row=copy.deepcopy(ev);row.update(patch)
   with self.subTest(patch=patch),self.assertRaises(ValueError):validate_records([row])
 def test_missing_obligation_cannot_be_dropped_to_force_pass(self):
  rows=copy.deepcopy(self.records)
  next(r for r in rows if r['Year']==2050 and r['Account']=='InternationalShippingBunker' and r['Country']=='BN')['Required']=False
  with self.assertRaises(ValueError):check(rows,2050)
 def test_road_parent_cannot_be_an_additional_load(self):
  r=copy.deepcopy(next(r for r in self.records if r['Account']=='RoadParent'))
  r['Kind']='DEMAND'
  with self.assertRaises(ValueError):validate_records([r])
 def test_bunker_constant_preserves_singapore_and_missing(self):
  sg=next(r for r in self.records if r['Year']==2050 and r['Account']=='InternationalShippingBunker' and r['Country']=='SG')
  self.assertEqual(float(sg['Value']),535341800.);self.assertEqual(sg['MethodID'],'ASSEMBLY_V1_BUNKER_CONSTANT_2019');self.assertTrue(sg['Phase5SensitivityRequired'])
  bn=next(r for r in self.records if r['Year']==2050 and r['Account']=='InternationalShippingBunker' and r['Country']=='BN')
  self.assertIsNone(bn['Value']);self.assertFalse(bn['Posting']);self.assertFalse(bn['RequiredPhysical'])
  self.assertEqual(bn['AssemblyStatus'],'HUMAN_COVERAGE_BOUNDARY_APPLIED')
 def test_historical_missing_bunker_requires_explicit_boundary_decision(self):
  old=json.loads((ROOT/'tests/research/fixtures/gate4_before_continue.json').read_text())['records']
  bn=next(r for r in old if r['Year']==2050 and r['Account']=='InternationalShippingBunker' and r['Country']=='BN')
  self.assertIsNone(bn['Value']);self.assertEqual(bn['AssemblyStatus'],'PENDING')
 def test_carbon_gate_is_post_build_not_numerical_input(self):
  self.assertEqual(check(self.records,2050)['carbon_validation_stage'],'POST_BUILD_STATIC_VALIDATION_BLOCKER')
if __name__=='__main__':unittest.main(verbosity=2)
