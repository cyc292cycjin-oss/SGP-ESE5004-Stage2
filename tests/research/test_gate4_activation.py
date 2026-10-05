"""SYNTHETIC_TEST_ONLY hydro regressions and independent current-input checks."""
from pathlib import Path
import sys,unittest,copy,json,tempfile,subprocess
import numpy as np,pypsa
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
from test_surviving_asset_integration import parent,DECISION,network,contract
from unit_asset_survival import reconcile_units
from integrate_surviving_assets import integrate_survivors
from reconstruct_base_accounts import reconstruct
from rebuild_assembly_targets import derive
from check_assembly_inputs import load_registry,check

class HydroAggregationTests(unittest.TestCase):
 def fixture(self,mode,shared=False):
  e=reconcile_units([parent()],{'Wind':dict(DECISION,Lifetime=100.)});n=network();s=network();c=contract()
  for k,v in [('a',2.),('b',3.)]:s.add('StorageUnit',k,bus='SG 0',p_nom=100.,inflow=np.full(2920,v))
  for r,source in zip(e['records'],['a','a' if shared else 'b']):
   p=copy.deepcopy(c['performance']['Wind']);p.update(ComponentType='StorageUnit',Carrier='hydro',Efficiency=.9,EfficiencyStore=0.,MaxHours=12.,CyclicStateOfCharge=True,StaticOperatingInputs={'p_min_pu':0.},ResourceGroup='EXISTING_ONLY_NO_NEW_CANDIDATE',ExistingOnlyEvidence='SYNTHETIC_TEST_ONLY',Profiles={'inflow':dict(Source='SYNTHETIC_TEST_ONLY',ComponentType='StorageUnit',Component=source,Multiplier=1.,Aggregation=mode,ResourceIdentity=source)})
   c['performance'][r['AssetID']]=p
  return n,e,c,s
 def test_two_dedicated_hydro_inflows_sum_and_roundtrip(self):
  n,e,c,s=self.fixture('UNIT_ABSOLUTE_SUM');r=integrate_survivors(n,e,c,s);self.assertEqual(r['integrated_components'],1);name=next(iter(n.storage_units.index));self.assertEqual(n.storage_units.at[name,'p_nom'],100.)
  np.testing.assert_array_equal(n.storage_units_t.inflow[name],5.)
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'SYNTHETIC_TEST_ONLY.nc';n.export_to_netcdf(path);b=pypsa.Network(path);np.testing.assert_array_equal(b.storage_units_t.inflow[name],5.);self.assertEqual(b.meta,n.meta)
 def test_shared_hydro_inflow_is_counted_once(self):
  n,e,c,s=self.fixture('SHARED_GROUP_ONCE',True);integrate_survivors(n,e,c,s);np.testing.assert_array_equal(n.storage_units_t.inflow.iloc[:,0],2.)
 def test_shared_flow_cannot_repeat_across_performance_groups(self):
  n,e,c,s=self.fixture('SHARED_GROUP_ONCE',True);c['performance'][e['records'][0]['AssetID']]['MaxHours']=10.
  with self.assertRaisesRegex(ValueError,'repeated across'):integrate_survivors(n,e,c,s)
 def test_ambiguous_multiplant_inflow_refused(self):
  n,e,c,s=self.fixture('SINGLE_COMPONENT_ABSOLUTE',True)
  with self.assertRaisesRegex(ValueError,'ownership'):integrate_survivors(n,e,c,s)
 def test_normalised_curves_capacity_weighted_not_summed(self):
  n=network();s=network();s.generators_t.p_max_pu.loc[:,'new-a']=.2;s.generators_t.p_max_pu.loc[:,'new-b']=.8;c=contract();e=reconcile_units([parent()],{'Wind':dict(DECISION,Lifetime=100.)})
  for r in e['records']:
   p=copy.deepcopy(c['performance']['Wind']);p['Profiles']['p_max_pu']['Component']='new-a' if r['RawUnitID']=='old' else 'new-b';c['performance'][r['AssetID']]=p
  integrate_survivors(n,e,c,s);name=next(iter(n.meta['existing_unit_components'].values()))['component'];np.testing.assert_allclose(n.generators_t.p_max_pu[name],.56)
 def test_engineering_proxy_needs_authorisation(self):
  n,e,c,s=self.fixture('SHARED_GROUP_ONCE',True)
  for p in c['performance'].values():p['ApprovalStatus']='SOURCE_QUALIFIED_ENGINEERING_PROXY';p.pop('AuthorizationReference',None)
  self.assertEqual(integrate_survivors(n,e,c,s)['integrated_units'],0)

class AppliedInputTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.f=ROOT/'research_inputs/assembly_v1';cls.data=load_registry(cls.f);cls.base=reconstruct(cls.f/'sources')
 def test_prior133_values_unchanged_new19_have_sources(self):
  old=json.loads(subprocess.check_output(['git','show','7c4b9dda:research_inputs/assembly_v1/registry.json'],cwd=ROOT));accepted=lambda d:{r['InputID']:r for r in d['records'] if r['Year']==2050 and r['Kind']=='DEMAND' and r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED'}
  before=accepted(old);after=accepted(self.data);self.assertEqual(len(before),133);self.assertEqual(len(after),152)
  for k,r in before.items():self.assertEqual(r['Value'],after[k]['Value'])
  self.assertEqual(len(derive(self.f)['records']),152)
 def test_thailand_four_items_exact_no_memo_posting(self):
  from decimal import Decimal as D
  selected=[r for r in self.base['selected_rows'] if r['Country']=='TH' and r['Account']=='RoadResidualFuel' and r['Commodity'] in ['Motor Gasoline','Gas Oil/ Diesel Oil','Biogasoline','Biodiesel']]
  self.assertEqual(len(selected),4);self.assertEqual(sum(D(r['MWh']) for r in selected),D('274632227.776'))
  self.assertEqual(len([x for x in self.base['resolved_blends'].values() if x['SourceRows'][0].startswith(json.loads((self.f/'sources/TH_ROAD_LOCAL_VINTAGE_APPLIED.json').read_text())['replacements'][0]['NewRawRow']['SourceSHA256'])]),2)
 def test_rail_parent_not_posted_and_ph_stays_blocked(self):
  records=self.data['records'];rail=[r for r in records if r['Year']==2050 and r['Account']=='RailNonElectric']
  self.assertEqual({r['Country'] for r in rail if r['AssemblyStatus']=='ASSEMBLY_V1_ACCEPTED'},{'ID','KH','MM','TH'})
  self.assertTrue(all(r['AssemblyStatus']=='PENDING' for r in rail if r['Country']=='PH'))
  parents=[r for r in records if r.get('Representation')=='APPROVED_CARRIER_SPLIT'];self.assertEqual(len(parents),5);self.assertTrue(all(r['Kind']=='ACCOUNTING' and not r['Required'] and r['Value'] is None for r in parents))
 def test_nec_source_rows_unique_and_retained(self):
  rows=[r for r in self.data['records'] if r['Year']==2050 and r['Kind']=='DEMAND' and r['Account'] in ['TransportNEC','OtherNEC']];ids=[x for r in rows for x in r['BaseSourceRows']]
  self.assertEqual(len(ids),15);self.assertEqual(len(set(ids)),15);self.assertTrue(all(r['Value']==r['BaseValueMWh'] for r in rows))
 def test_coverage_and_ev_boundary_remain_guarded(self):
  q=check(self.data['records'],2050,known_unallocated=self.data['known_unallocated_base_accounts']);self.assertFalse(q['NUMERIC_INPUT_READY']);self.assertEqual(q['known_positive_target_method_pending'],0)
  self.assertTrue(all(r['Kind']=='BOUNDARY' and r['Value'] is None for r in self.data['records'] if r['Year']==2050 and r['Account']=='RoadEVFinalElectricity'))
 def test_zero_proof_uses_one_original_vintage(self):
  self.assertIn('immutable',self.base['zero_proof_vintage_scope']);old=json.loads(subprocess.check_output(['git','show','7c4b9dda:research_inputs/assembly_v1/registry.json'],cwd=ROOT));before={r['InputID']:r for r in old['records'] if r['Year']==2050 and r.get('Classification')=='SOURCE_SUPPORTED_NOT_APPLICABLE'}
  for r in self.data['records']:
   if r['InputID'] in before:self.assertEqual(set(r['ZeroEvidence'].split(';')),set(before[r['InputID']]['ZeroEvidence'].split(';')))
 def test_explicit_nec_rail_physical_reporting_no_power_policy(self):
  from carbon_architecture import classify_record
  for sector in ['RailNonElectric','TransportNEC','OtherNEC']:
   r=classify_record('fixture','oil',sector,'TH',.25,source='SYNTHETIC_TEST_ONLY',policy_weight=0.,accepted=True);self.assertEqual(r['Sector'],sector);self.assertFalse(r['PolicyCO2Power']);self.assertTrue(r['ReportingCO2FullSystem'])
   with self.assertRaisesRegex(ValueError,'Non-power'):classify_record('fixture','oil',sector,'TH',.25,source='SYNTHETIC_TEST_ONLY',policy_weight=1.,accepted=True)
if __name__=='__main__':unittest.main(verbosity=2)
