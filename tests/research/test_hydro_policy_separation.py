"""SYNTHETIC_TEST_ONLY numerical mechanisms; no optimization/solver call."""
from pathlib import Path
import sys,unittest,copy,tempfile,json
import numpy as np,pypsa
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
from test_surviving_asset_integration import network,contract,evidence
import test_gate4_activation as hydro_fixtures
import test_gate4_assets as assembly_fixtures
from integrate_surviving_assets import integrate_survivors,combined_profiles
import carbon_architecture as carbon
from assembly_components import bind_loads,merge_input_components
from build_research_network import load_unbound_recipe

class HydroTests(unittest.TestCase):
 def test_phs_duration_efficiencies_cycle_export(self):
  n=network();c=contract();p=c['performance']['Wind'];p.update(ComponentType='StorageUnit',Carrier='PHS existing',Efficiency=np.sqrt(.75),EfficiencyStore=np.sqrt(.75),MaxHours=6.,CyclicStateOfCharge=True,StorageInitialMWh=0.,NaturalInflowMW=0.,HydroSubtype='Pumped Storage',Profiles={},ResourceGroup='EXISTING_ONLY_NO_NEW_CANDIDATE',ExistingOnlyEvidence='SYNTHETIC_TEST_ONLY',StaticOperatingInputs={'p_min_pu':-1.})
  integrate_survivors(n,evidence(),c,n);r=n.storage_units.iloc[0]
  self.assertAlmostEqual(r.p_nom*r.max_hours,360.);self.assertAlmostEqual(r.efficiency_store*r.efficiency_dispatch,.75);self.assertEqual(r.inflow,0);self.assertTrue(r.cyclic_state_of_charge);self.assertEqual(r.state_of_charge_initial,0);self.assertEqual(r.p_min_pu,-1)
  # Summed cyclic balance: discharge/eta_d=eta_c*charge; zero charging
  # implies zero discharge. No initial inventory can subsidise annual output.
  self.assertAlmostEqual(100*r.efficiency_store*r.efficiency_dispatch,75.)
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'SYNTHETIC_TEST_ONLY.nc';n.export_to_netcdf(path);again=pypsa.Network(path);self.assertEqual(again.meta,n.meta);self.assertEqual(again.storage_units.iloc[0].max_hours,6.)
 def test_phs_noncyclic_free_initial_energy_rejected(self):
  for bad in [dict(CyclicStateOfCharge=False),dict(StorageInitialMWh=10.),dict(NaturalInflowMW=1.)]:
   n=network();c=contract();p=c['performance']['Wind'];p.update(ComponentType='StorageUnit',Carrier='PHS',Efficiency=.8,EfficiencyStore=.8,MaxHours=6.,CyclicStateOfCharge=True,StorageInitialMWh=0.,NaturalInflowMW=0.,HydroSubtype='Pumped Storage',Profiles={},ResourceGroup='EXISTING_ONLY_NO_NEW_CANDIDATE',ExistingOnlyEvidence='SYNTHETIC_TEST_ONLY');p.update(bad)
   with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'free initial'):integrate_survivors(n,evidence(),c,n)
 def test_shared_reservoir_not_multiplied_by_units(self):
  n,e,c,s=hydro_fixtures.HydroAggregationTests().fixture('SHARED_GROUP_ONCE',True);integrate_survivors(n,e,c,s)
  self.assertEqual(len(n.storage_units),1);self.assertAlmostEqual(float((n.storage_units_t.inflow.iloc[:,0]*n.snapshot_weightings.stores).sum()),2*8760)
 def test_ror_turbine_increase_does_not_increase_source_envelope(self):
  s=network();s.generators_t.p_max_pu.loc[:,'new-a']=.8
  q=dict(capacity=200.,performance={'Profiles':{'p_max_pu':dict(ComponentType='Generator',Component='new-a',Source='SYNTHETIC_TEST_ONLY',Multiplier=100/200,ClipUpper=1.)}})
  v=combined_profiles([q],s,s.snapshots,set())['p_max_pu'];np.testing.assert_allclose(v*200,80)
 def test_ror_smaller_turbine_clamps_availability(self):
  s=network();s.generators_t.p_max_pu.loc[:,'new-a']=.8
  q=dict(capacity=50.,performance={'Profiles':{'p_max_pu':dict(ComponentType='Generator',Component='new-a',Source='SYNTHETIC_TEST_ONLY',Multiplier=100/50,ClipUpper=1.)}})
  v=combined_profiles([q],s,s.snapshots,set())['p_max_pu'];np.testing.assert_allclose(v*50,50)
 def test_absolute_inflow_clipping_rejected(self):
  s=network();s.add('StorageUnit','river',bus='SG 0',inflow=2.)
  s.storage_units_t.inflow.loc[:,'river']=2.
  q=dict(capacity=50.,performance={'Profiles':{'inflow':dict(ComponentType='StorageUnit',Component='river',Source='SYNTHETIC_TEST_ONLY',Multiplier=1.,ClipUpper=1.)}})
  with self.assertRaisesRegex(ValueError,'Only normalised'):combined_profiles([q],s,s.snapshots,set())

class PhysicalPolicyTests(unittest.TestCase):
 def record(self,**change):
  args=dict(component='SMR',carrier='SMR',sector='HydrogenProduction',country='SG',coefficient=.2,source='SYNTHETIC_TEST_ONLY',policy_weight=None,physical_qualified=True,policy_qualified=False);args.update(change);return carbon.classify_record(**args)
 def test_physical_qualified_policy_null(self):
  r=self.record();self.assertTrue(r['PhysicalReportingQualified']);self.assertFalse(r['PolicyAttributionQualified']);self.assertIsNone(r['PolicyWeight']);self.assertIsNone(r['PolicyCO2Power'])
 def test_unknown_weight_cannot_become_zero(self):
  with self.assertRaisesRegex(ValueError,'null'):self.record(policy_weight=0.)
 def test_legacy_nonpower_missing_weight_is_not_zero(self):
  r=carbon.classify_record('SMR','SMR','HydrogenProduction','SG',.2,source='SYNTHETIC_TEST_ONLY',accepted=True)
  self.assertIsNone(r['PolicyWeight']);self.assertFalse(r['PolicyAttributionQualified'])
 def test_unqualified_physical_fails(self):
  with self.assertRaisesRegex(ValueError,'Physical'):self.record(physical_qualified=False)
 def test_smr_and_cc_physical_balance_without_policy(self):
  for cc in [0.,.9]:
   events,proof=carbon.smr_physical_events('test','SG',100.,.2,cc,source='SYNTHETIC_TEST_ONLY');view=carbon.views(events)
   self.assertAlmostEqual(proof['ImmediateAtmosphere']+proof['CapturedTransfer'],20.);self.assertAlmostEqual(view['ReportingCO2_FullSystem'],20*(1-cc));self.assertIsNone(view['PolicyCO2_Power']);self.assertEqual(len(view['PolicyAttributionPending']),2)
 def test_same_smr_event_cannot_repeat(self):
  e,_=carbon.smr_physical_events('test','SG',1,.2,.9,source='SYNTHETIC_TEST_ONLY')
  with self.assertRaisesRegex(ValueError,'Duplicate'):carbon.views(e+[e[0]])
 def test_policy_enabled_refuses_physically_qualified_pending(self):
  terms=[dict(policy_weight=None,accepted=False,PhysicalReportingQualified=True,PolicyAttributionQualified=False)]
  with self.assertRaisesRegex(ValueError,'POLICY_ATTRIBUTION_PENDING'):carbon.install_power_policy(None,terms,2050,enabled=True,scope_complete=True,expected_hours=8760)
  self.assertFalse(carbon.install_power_policy(None,terms,2050,enabled=False,scope_complete=False,expected_hours=8760)['constraint_created'])
 def test_capture_outside_physical_bounds_refused(self):
  with self.assertRaises(ValueError):carbon.smr_physical_events('x','SG',1,.2,1.1,source='fixture')

class AssemblyBoundaryTests(unittest.TestCase):
 def test_named_weights_survive_serialization_column_order(self):
  n=network();sub=pypsa.Network();sub.set_snapshots(n.snapshots);sub.snapshot_weightings=n.snapshot_weightings[['stores','objective','generators']].copy();merge_input_components(n,sub)
 def test_physical_weight_change_still_rejected(self):
  n=network();sub=pypsa.Network();sub.set_snapshots(n.snapshots);sub.snapshot_weightings=n.snapshot_weightings.copy();sub.snapshot_weightings.loc[:,'stores']=6.
  with self.assertRaisesRegex(ValueError,'time boundary'):merge_input_components(n,sub)
 def test_double_binding_refused(self):
  n,r,m,a,d=assembly_fixtures.RoundtripTests().setup_network()
  with self.assertRaisesRegex(ValueError,'only once'):bind_loads(n,r,m,a,d)
 def test_bound_fragment_refused_before_merge(self):
  n,*_=assembly_fixtures.RoundtripTests().setup_network();empty=pypsa.Network();empty.set_snapshots(n.snapshots);empty.snapshot_weightings=n.snapshot_weightings.copy()
  with self.assertRaisesRegex(ValueError,'Bound development'):merge_input_components(empty,n)
 def test_real_unbound_recipe_excludes_loads(self):
  p=ROOT/'results_project/assembly_v1/assets/carrier_fragment.json'
  if not p.exists():self.skipTest('Production assets not available')
  raw=load_unbound_recipe(p);self.assertFalse(any(x['type']=='Load' for x in raw['components'].values()));self.assertGreater(len(raw['demand_destinations']),0)
  with self.assertRaisesRegex(ValueError,'never a bound'):load_unbound_recipe(p.with_name('carrier_fragment_2050_unsolved.nc'))
 def test_recipe_with_load_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.json';p.write_text(json.dumps({'components':{'x':{'type':'Load'}}}))
   with self.assertRaisesRegex(ValueError,'Bound demand'):load_unbound_recipe(p)

if __name__=='__main__':unittest.main(verbosity=2)
