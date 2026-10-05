from pathlib import Path
from copy import deepcopy
import json,sys,unittest
REPO=Path(__file__).resolve().parents[2];sys.path.insert(0,str(REPO/'scripts_project'))
from asset_survival import select_asset
from asset_lifetime_override import load_overrides,apply_override
from blend_uncertainty import bounds,observations
class LimitedLifetime(unittest.TestCase):
 def setUp(self):
  self.u=json.loads((REPO/'tests/research/fixtures/avion_unapproved_lifetime.json').read_text());self.d=load_overrides(REPO)
 def test_scoped25_not_ccgt40(self):
  self.assertEqual(json.loads((REPO/'research_inputs/asset_survival/lifetime_decisions.json').read_text())['technologies']['CCGT']['Lifetime'],40)
  out=apply_override(self.u,self.d);self.assertEqual(out['Lifetime'],25);z=select_asset(out)
  self.assertEqual((z['RetirementYear'],z['RetainedCapacity2050'],z['SurvivalStatus']),(2041.,0.,'NOT_ACTIVE_2050'));self.assertEqual(z['RetirementDerivation'],'DERIVED_FROM_ACCEPTED_LIFETIME');self.assertEqual(z['OriginalCapacity'],100);self.assertEqual(z['DependableCapacityMW'],97)
 def test_unapproved_fixture_not_zero(self):
  d=deepcopy(self.d);d['records'][0]['ApprovalStatus']='PENDING';z=select_asset(apply_override(self.u,d));self.assertIsNone(z['RetainedCapacity2050']);self.assertEqual(z['SurvivalStatus'],'UNRESOLVED_RETIREMENT_OR_LIFETIME')
 def test_actual_retirement_takes_priority(self):
  u=dict(self.u,RetirementYear=2055,RetirementEvidenceVerified=True);z=select_asset(apply_override(u,self.d));self.assertEqual(z['RetirementDerivation'],'VERIFIED_RETIREMENT_RECORD');self.assertEqual(z['RetainedCapacity2050'],100)
 def test_new_build_unaffected(self):
  u=dict(self.u,AssetClass='NEW_BUILD_CANDIDATE',Lifetime=30,efficiency=.5,capital_cost=999);self.assertEqual(apply_override(u,self.d),u);self.assertEqual(select_asset(u)['SurvivalStatus'],'NOT_INHERITED_NEW_BUILD_CANDIDATE')
 def test_other_existing_ocgt_not_authorised(self):
  u=dict(self.u,AssetID='OTHER_OCGT');self.assertEqual(apply_override(u,self.d),u)
 def test_material_conflicts_not_suppressed(self):
  for k,v in [('Country','MM'),('Technology','CCGT'),('OriginalCapacity',97),('CommissioningYear',2017),('UnresolvedRefurbishmentEvidence',True)]:
   with self.subTest(k=k),self.assertRaises(ValueError):apply_override(dict(self.u,**{k:v}),self.d)
 def test_no_performance_acceptance(self):
  out=apply_override(self.u,self.d)
  for key in ['efficiency','FOM','VOM','capital_cost','marginal_cost']:self.assertNotIn(key,out)
class BlendBounds(unittest.TestCase):
 def setUp(self):
  self.p=dict(Country='PH',Year=2019,Transaction='1221',Unit='Metric tons, thousand',Vintage='SYNTHETIC_TEST_ONLY',CommodityCode='4670',Quantity='100',SourceRow='P');self.b=dict(self.p,CommodityCode='5220',Quantity='20',SourceRow='B');self.proof=dict(Memo='ZD',InclusionVerified=True,VersionReconciled=True)
 def test_mass_and_separate_energy(self):
  r=bounds(self.p,self.b,self.proof,12,10);self.assertEqual((r['LowerUniqueQuantity'],r['UpperUniqueQuantity']),('100','120'));self.assertEqual((r['LowerEnergyMWh'],r['UpperEnergyMWh']),('1160','1400'));self.assertFalse(r['Posting'])
 def test_bio_exceeds_parent(self):
  r=bounds(dict(self.p,Quantity='10'),self.b,self.proof,12,10);self.assertEqual((r['ZUpper'],r['LowerUniqueQuantity'],r['UpperUniqueQuantity']),('10','20','30'));self.assertEqual(r['LowerEnergyMWh'],'200')
 def test_incompatible_pairs_have_no_bounds(self):
  for k,v in [('Country','ID'),('Year',2020),('Transaction','121'),('Unit','TJ'),('Vintage','OTHER_VERSION'),('CommodityCode','5210'),('Quantity',None)]:
   with self.subTest(k=k):
    r=bounds(self.p,dict(self.b,**{k:v}),self.proof,12,10);self.assertEqual(r['Status'],'BOUND_NOT_DERIVABLE_FROM_CURRENT_SOURCE');self.assertIsNone(r['LowerUniqueQuantity'])
 def test_missing_version_or_inclusion_refuses(self):
  for k in ['InclusionVerified','VersionReconciled']:
   r=bounds(self.p,self.b,dict(self.proof,**{k:False}),12,10);self.assertIsNone(r['LowerUniqueQuantity'])
 def test_missing_heat_value_only_mass_derivable(self):
  r=bounds(self.p,self.b,self.proof,12,None);self.assertEqual(r['LowerUniqueQuantity'],'100');self.assertIsNone(r['LowerEnergyMWh'])
 def test_zero_is_distinct_from_missing(self):
  r=bounds(self.p,dict(self.b,Quantity='0'),self.proof,12,10);self.assertEqual(r['LowerUniqueQuantity'],r['UpperUniqueQuantity']);self.assertEqual(r['ZUpper'],'0')
 def test_cached_response_names_and_rows(self):
  r=observations(REPO/'research_inputs/assembly_v1/sources/unsd_targeted/PH_2019.xml');ps=[x for x in r if x['COMMODITY']=='4652' and x['TRANSACTION']=='1221' and x['Year']=='2019'];self.assertEqual(len(ps),1);self.assertEqual(ps[0]['UNIT_MEASURE'],'TN')
class MetadataPreservation(unittest.TestCase):
 def test_bus_and_component_order_are_aligned(self):
  import pypsa
  from refresh_diagnostic_qualification import compare_physical
  n=pypsa.Network();n.add('Bus','B');n.add('Bus','A');n.add('Generator','g2',bus='B',p_nom=2);n.add('Generator','g1',bus='A',p_nom=1)
  n.meta={'fixture':'SYNTHETIC_TEST_ONLY'};m=n.copy();m.buses=m.buses.iloc[::-1];m.generators=m.generators.iloc[::-1]
  self.assertTrue(compare_physical(n,m))
  m.generators.loc['g1','p_nom']=3
  with self.assertRaises(AssertionError):compare_physical(n,m)
 def test_metadata_edit_does_not_change_netcdf_values(self):
  import tempfile
  from netCDF4 import Dataset
  from refresh_diagnostic_qualification import change_meta,meta
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'synthetic_test_only.nc'
   with Dataset(p,'w') as d:d.createDimension('x',2);d.createVariable('capacity','f8',('x',))[:]=[1,2];d.setncattr('meta','{}')
   change_meta(p,dict(artifact_role='SYNTHETIC_TEST_ONLY',solver_allowed=False))
   with Dataset(p) as d:self.assertEqual(list(d.variables['capacity'][:]),[1,2])
   self.assertFalse(meta(p)['solver_allowed'])
if __name__=='__main__':unittest.main()
