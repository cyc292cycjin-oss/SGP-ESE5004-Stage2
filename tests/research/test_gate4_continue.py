from pathlib import Path
import unittest,sys,json,copy,tempfile,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
from reconstruct_base_accounts import reconstruct,Reconstruction
from check_assembly_inputs import load_registry,check,validate_records,ACCEPTED
class SourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.folder=ROOT/'research_inputs/assembly_v1';cls.base=reconstruct(cls.folder/'sources');cls.lookup={(r['Country'],r['Account'],r['Carrier']):r for r in cls.base['accounts']}
 def test_domestic_navigation_in_is_selected(self):
  z=[r for r in self.base['selected_rows'] if r['Country']=='SG' and r['Account']=='DomesticShippingFuel']
  self.assertTrue(any(r['RawValue']=='76' and 'in domestic navigation' in r['Transaction'].lower() for r in z))
 def test_aviation_gasoline_is_not_lost(self):
  z=[r for r in self.base['selected_rows'] if r['Country']=='SG' and r['Account']=='InternationalAviationBunker' and r['Commodity']=='Aviation gasoline']
  self.assertEqual(len(z),1);self.assertAlmostEqual(float(z[0]['MWh']),639.6)
 def test_industry_aggregate_not_added_to_children(self):
  z=self.lookup['TH','IndustryFinalEnergy','coal'];self.assertTrue(z['ExcludedOverlappingRows']);self.assertLess(float(z['ValueMWh']),6e7)
  selected=[r for r in self.base['selected_rows'] if r['Country']=='TH' and r['Account']=='IndustryFinalEnergy' and r['Carrier']=='coal']
  self.assertTrue(all('manufacturing, construction' in r['Transaction'].lower() for r in selected))
 def test_missing_bunker_not_zero_from_domestic_FEC(self):
  for c in ['BN','LA','TL']:
   z=self.lookup[c,'InternationalShippingBunker','oil'];self.assertIsNone(z['ValueMWh']);self.assertEqual(z['Status'],'UNRESOLVED')
 def test_tl_transport_NEC_not_road_diesel(self):
  rows=[r for r in self.base['selected_rows'] if r['Country']=='TL' and r['Account']=='RoadResidualFuel']
  self.assertFalse(any(r['Commodity']=='Gas Oil/ Diesel Oil' for r in rows))
  raw=json.loads((self.folder/'sources/KNOWN_UNALLOCATED_BASE_ACCOUNTS.json').read_text())
  self.assertTrue(any(r['Country']=='TL' and r['RawValue']=='62.98' for r in raw))
 def test_gcv_operation_specific_not_blanket_gas(self):
  conv=Reconstruction(json.loads((self.folder/'sources/UNSD_2019_SOURCE_CAPSULE.json').read_text()),json.loads((self.folder/'sources/FROZEN_UPSTREAM_CONVERSIONS.json').read_text()))
  ng={'Commodity':'Natural gas (including LNG)','Quantity':'4','Unit':'Terajoules'}
  self.assertEqual(float(conv.convert(ng)[0]),1000.)
  bio=dict(ng,Commodity='Biogases');self.assertAlmostEqual(float(conv.convert(bio)[0]),4/.0036)
  with self.assertRaises(ValueError):conv.convert(dict(ng,Unit='MWh/year'))
 def test_no_nonenergy_row_is_a_combustion_obligation(self):
  self.assertTrue(self.base['nonenergy_reference']);self.assertFalse(any('non-energy' in r['Transaction'].lower() for r in self.base['selected_rows']))
 def test_blended_biofuel_pairs_are_not_qualified_by_growth(self):
  # Frozen pre-retrieval capsule; production IDs may later be legitimately closed.
  import shutil
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)
   shutil.copyfile(ROOT/'tests/research/fixtures/missing_blend_memo.json',path/'UNSD_2019_SOURCE_CAPSULE.json')
   shutil.copyfile(self.folder/'sources/FROZEN_UPSTREAM_CONVERSIONS.json',path/'FROZEN_UPSTREAM_CONVERSIONS.json')
   missing=reconstruct(path)
  lookup={(r['Country'],r['Account'],r['Carrier']):r for r in missing['accounts']}
  self.assertEqual(lookup['ID','RoadResidualFuel','oil']['Status'],'UNRESOLVED_BIOFUEL_OVERLAP')
  self.assertEqual(lookup['ID','RoadResidualFuel','biomass']['Status'],'UNRESOLVED_BIOFUEL_OVERLAP')
 def test_road_growth_exact_and_reference_not_posted(self):
  from decimal import Decimal as D
  data=load_registry(self.folder);r=[r for r in data['records'] if r['Year']==2050 and r['Account']=='RoadResidualFuel' and r['AssemblyStatus']==ACCEPTED]
  self.assertTrue(r)
  for x in r:
   self.assertAlmostEqual(float(x['Value']),float(D(x['BaseValueMWh'])*D('374.9')/D('145.2')),places=5)
   self.assertEqual(x['MethodID'],'ASSEMBLY_V1_ROAD_NON_ELECTRIC_TRANSPORT_GROWTH_PROXY')
  for c in {x['Country'] for x in r}:
   local=[x for x in r if x['Country']==c];base=sum(float(x['BaseValueMWh']) for x in local);future=sum(float(x['Value']) for x in local)
   if base>0:
    for x in local:self.assertAlmostEqual(float(x['BaseValueMWh'])/base,float(x['Value'])/future)
  for x in data['records']:
   if x['Account']=='RoadParent':self.assertFalse(x['Posting']);self.assertFalse(x['EnforceExactTotal']);self.assertEqual(x['ReferenceRole'],'ROAD_TOTAL_REFERENCE_ONLY')
 def test_decisions_and_final_electricity(self):
  data=load_registry(self.folder);r=[r for r in data['records'] if r['Year']==2050 and r['Account']=='Astar']
  self.assertEqual(len(r),11);self.assertAlmostEqual(sum(float(x['Value']) for x in r if x['Country']!='TL'),2616750000.)
  self.assertGreater(float(next(x for x in r if x['Country']=='TL')['Value']),0)
  for x in data['records']:
   if x['Year']==2050 and x['Account'] in ['ResidentialFuel','ServicesFuel','IndustryFinalEnergy','AgricultureFinalEnergy'] and x['AssemblyStatus']==ACCEPTED:
    self.assertEqual(x['GrowthRatioBaseYear'],2022);self.assertEqual(x['ProjectBaseYear'],2019)

class LayeredGateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=load_registry(ROOT/'research_inputs/assembly_v1')
 def qualified_fixture(self):
  # Explicit synthetic unit-test fixture, never production scientific inputs.
  rows=copy.deepcopy(self.data['records'])
  for r in rows:
   if r['Year']==2050 and r['Kind']=='DEMAND':
    r.update(AssemblyStatus=ACCEPTED,Classification='REQUIRED_PHYSICAL',Value='1',Unit='MWh/year',SourceQualified=True,Source='SYNTHETIC_TEST_FIXTURE',SourceSHA256='f'*64,Transformation='Test fixture1MWh',ProjectionEvidence='TEST_ONLY',TargetReady=False,ZeroEvidence='',ExclusionEvidence='')
  return rows
 def test_numeric_pass_stops_only_at_allocation(self):
  r=check(self.qualified_fixture(),2050);self.assertTrue(r['NUMERIC_INPUT_READY']);self.assertFalse(r['ALLOCATION_READY']);self.assertEqual(r['status'],'BLOCKED_ALLOCATION')
 def test_text_is_not_an_allocation(self):
  rows=self.qualified_fixture()
  for r in rows:r.update(SpatialEvidence='claimed allocation',TemporalEvidence='claimed profile',TargetReady=True)
  self.assertFalse(check(rows,2050)['ALLOCATION_READY'])
 def test_errors_still_fail(self):
  good=self.qualified_fixture()
  for patch in [{'Unit':'TWh/year'},{'SourceSHA256':''},{'Value':None}]:
   z=copy.deepcopy(next(r for r in good if r['Year']==2050 and r['Kind']=='DEMAND'));z.update(patch)
   with self.subTest(patch=patch),self.assertRaises(ValueError):validate_records([z])
  with self.assertRaises(ValueError):check(good+[good[0]],2050)
 def test_actual_array_positive_and_tamper(self):
  rows=self.qualified_fixture();d=[r for r in rows if r['Year']==2050 and r['Kind']=='DEMAND'];arrays={'weights':np.full(2920,3.),'snapshots':np.arange(np.datetime64('2013-01-01T00'),np.datetime64('2014-01-01T00'),np.timedelta64(3,'h')).astype('U19')};manifest=[]
  for i,r in enumerate(d):
   x=np.full((2920,1),1/8760);key='a'+str(i);arrays[key]=x
   manifest.append(dict(InputID=r['InputID'],Country=r['Country'],Nodes=[r['Country']+' test node'],NodeCountries=[r['Country']],ArrayKey=key,ArraySHA256=hashlib.sha256(x.tobytes()).hexdigest()))
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);np.savez_compressed(p/'allocations.npz',**arrays)
   (p/'geographic_nodes.json').write_text(json.dumps({r['Country']+' test node':{'country':r['Country']} for r in d}))
   (p/'allocation_manifest.json').write_text(json.dumps(dict(arrays_file='allocations.npz',arrays_sha256=hashlib.sha256((p/'allocations.npz').read_bytes()).hexdigest(),geographic_nodes_file='geographic_nodes.json',geographic_nodes_sha256=hashlib.sha256((p/'geographic_nodes.json').read_bytes()).hexdigest(),records=manifest)))
   r=check(rows,2050,p);self.assertTrue(r['ALLOCATION_READY']);self.assertEqual(r['status'],'INPUT_GATE_ONLY_PASS');self.assertFalse(r['NETWORK_STATICALLY_VALIDATED'])
   mp=p/'allocation_manifest.json';saved=mp.read_text();bad=json.loads(saved);bad['records'][0]['Nodes']=['ID test node']
   if bad['records'][0]['Country']=='ID':bad['records'][0]['Nodes']=['SG test node']
   mp.write_text(json.dumps(bad))
   with self.assertRaises(ValueError):check(rows,2050,p)
   mp.write_text(saved)
   with (p/'allocations.npz').open('ab') as f:f.write(b'tamper')
   with self.assertRaises(ValueError):check(rows,2050,p)
 def test_unsupported_exclusion_fails(self):
  r=self.qualified_fixture();x=next(z for z in r if z['Year']==2050 and z['Kind']=='DEMAND');x.update(Classification='SOURCE_SUPPORTED_NOT_APPLICABLE',Value=None,AssemblyStatus='PENDING',ExclusionEvidence='No row')
  with self.assertRaises(ValueError):check(r,2050)
 def test_unowned_positive_blocks_even_qualified_numeric(self):
  self.assertFalse(check(self.qualified_fixture(),2050,known_unallocated=[{'MWh2019':1}])['NUMERIC_INPUT_READY'])
 def test_nonbinding_fossil_market_has_no_arbitrary_big_m(self):
  from carrier_architecture import local_blueprint,external_import
  f=local_blueprint({'SG2 0':'SG'})
  a=dict(price=24.568,price_unit='EUR/MWh_fuel',source_sha256='test-frozen-price',source_year=2020,basis='FROZEN',capacity_mw=None,annual_cap_mwh=None,unlimited_annual_accepted=True,unlimited_capacity_accepted=True)
  k=external_import(f,'SG2 0','gas','shared-price-only',a,accepted=True);p=f.components[k]['params']
  self.assertEqual(p['p_nom'],0);self.assertTrue(p['p_nom_extendable']);self.assertEqual(p['p_nom_max'],float('inf'));self.assertEqual(p['capital_cost'],0)
  with self.assertRaises(ValueError):external_import(f,'SG2 0','oil','shared-price-only',dict(a,capacity_mw=1e9),accepted=True)
 def test_guarded_builder_does_not_export_incomplete_inputs(self):
  from build_research_network import build
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)
   # No allocation folder: production source failures must stop before assets.
   status=build(ROOT,None,p/'missing_assets.json',p/'network.nc',p/'receipt.json')
   self.assertEqual(status,2);self.assertFalse((p/'network.nc').exists());self.assertEqual(json.loads((p/'receipt.json').read_text())['solver_runs'],0)
if __name__=='__main__':unittest.main(verbosity=2)
