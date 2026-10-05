import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts_project'))
from source_scope import derive_proofs,apply,validate_scope_registry,validate_scope_record,sha,save,STATUS
from check_assembly_inputs import load_registry,check
REPO=Path(__file__).resolve().parents[2]

class SourceScopeTests(unittest.TestCase):
 def setUp(self):
  import shutil
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.f=Path(self.t.name)/'inputs'
  shutil.copytree(REPO/'research_inputs/assembly_v1',self.f)
 def apply(self):
  apply(self.f,Path(self.t.name)/'report.json');return load_registry(self.f)
 def mutate_source(self,fn):
  p=self.f/'sources/UNSD_2019_SOURCE_CAPSULE.json';x=json.loads(p.read_text());fn(x['records']);save(p,x)
  d=self.f/'sources/BOUNDED_SOURCE_SCOPE_DECISIONS.json';x=json.loads(d.read_text());x['SourcePins'][p.name]=sha(p);save(d,x)
 def test_actual_hierarchy_and_missing_fec(self):
  p=derive_proofs(self.f)
  self.assertEqual(p['BN:coal']['Accounting']['ObservedParentQuantity'],'341.064')
  self.assertEqual(p['TL:gas']['Accounting']['Quantities']['total energy supply'],'0')
  for z in p.values():self.assertIsNone(z['OriginalFEC']);self.assertFalse(z['Accounting']['Posting'])
 def test_no_values_or_raw_rows_changed_and_idempotence(self):
  old=json.loads((self.f/'registry.json').read_text());raw=sha(self.f/'sources/UNSD_2019_SOURCE_CAPSULE.json');a=self.apply();h=sha(self.f/'registry.json');self.apply()
  self.assertEqual(h,sha(self.f/'registry.json'));self.assertEqual(raw,sha(self.f/'sources/UNSD_2019_SOURCE_CAPSULE.json'))
  for before,after in zip(old['records'],a['records']):
   for k in ['InputID','Value','RawValue','BaseValueMWh','BaseSourceRows']:self.assertEqual(before.get(k),after.get(k))
 def test_gate_counts_from_matched_records_not_literal_seven(self):
  a=self.apply();expected={r['InputID'] for r in a['records'] if r.get('Classification')==STATUS}
  gate=check(a['records'],2050,known_unallocated=a.get('known_unallocated_base_accounts'))
  self.assertEqual(expected,set(gate['source_scope_input_ids']));self.assertFalse(expected&set(gate['unresolved_input_ids']));self.assertNotEqual(gate['status'],'INPUT_GATE_ONLY_PASS')
  self.assertTrue(any('InternationalShippingBunker' in k for k in gate['unresolved_input_ids']))
 def test_positive_final_use_refuses(self):
  def fn(rows):
   r=copy.deepcopy(next(r for r in rows if r['Country']=='BN' and r['Commodity']=='Brown coal'));r.update(Transaction='Consumption by households',Quantity='1',PhysicalLine=999999);rows.append(r)
  self.mutate_source(fn)
  with self.assertRaisesRegex(ValueError,'Final-use'):derive_proofs(self.f)
 def test_uncovered_coal_stays_unresolved(self):
  def fn(rows):
   r=copy.deepcopy(next(r for r in rows if r['Country']=='BN' and r['Commodity']=='Brown coal'));r.update(Commodity='Hard coal',PhysicalLine=999999);rows.append(r)
  self.mutate_source(fn)
  with self.assertRaisesRegex(ValueError,'outside authorized'):derive_proofs(self.f)
 def test_gas_upstream_child_not_added_again(self):
  def fn(rows):
   for r in rows:
    if r['Country']=='TL' and r['Transaction']=='Flared':r['Quantity']='1'
  self.mutate_source(fn)
  with self.assertRaisesRegex(ValueError,'upstream hierarchy'):derive_proofs(self.f)
 def test_supply_balance_opposite_flow_refuses(self):
  def fn(rows):
   r=copy.deepcopy(next(r for r in rows if r['Country']=='TL' and r['Transaction']=='exports'));r.update(Transaction='imports',Quantity='1',PhysicalLine=999999);rows.append(r)
  self.mutate_source(fn)
  with self.assertRaisesRegex(ValueError,'Unreviewed TL'):derive_proofs(self.f)
 def test_units_version_country_year_bunker_guards(self):
  a=self.apply();r=next(r for r in a['records'] if r.get('Classification')==STATUS)
  for change in [dict(Country='KH'),dict(Carrier='oil'),dict(Year=2040),dict(Account='InternationalShippingBunker'),dict(Value='0'),dict(RequiredPhysical=True),dict(OutsideCoverageStatus='REPORTED_ZERO')]:
   with self.subTest(change=change),self.assertRaises(ValueError):validate_scope_record(dict(r,**change))
  d=self.f/'sources/BOUNDED_SOURCE_SCOPE_DECISIONS.json';x=json.loads(d.read_text());x['SourcePins']['UNSD_2019_SOURCE_CAPSULE.json']='bad';save(d,x)
  with self.assertRaisesRegex(ValueError,'source revision'):derive_proofs(self.f)
 def test_commodity_parent_children_not_summed(self):
  def fn(rows):
   for r in rows:
    if r['Country']=='BN' and r['Commodity']=='Lignite' and r['Transaction']=='Imports':r['Quantity']='682.128'
  self.mutate_source(fn)
  with self.assertRaisesRegex(ValueError,'hierarchy'):derive_proofs(self.f)
 def test_original_unit_mismatch_refuses(self):
  def fn(rows):
   for r in rows:
    if r['Country']=='TL' and r['Transaction']=='exports':r['Unit']='Metric tons,  thousand'
  self.mutate_source(fn)
  with self.assertRaisesRegex(ValueError,'incompatible'):derive_proofs(self.f)
 def test_audit_missing_lifetime_is_not_zero(self):
  from audit_residual_sources import conditional_capacity
  self.assertIsNone(conditional_capacity({'commissioning_year':2016,'capacity_mw':100},{'Lifetime':None}))
  self.assertEqual(conditional_capacity({'commissioning_year':2016,'capacity_mw':100},{'Lifetime':25}),0)

 def test_avion_never_inherits_ccgt_lifetime(self):
  from asset_survival import select_asset
  e=json.loads((REPO/'research_inputs/asset_survival/GPD_COHORT_SOURCE_REVIEW.json').read_text());r=next(r for r in e['records'] if r['raw']['gppd_idnr']=='WRI1029960')
  self.assertEqual(r['Technology'],'OCGT');life=json.loads((REPO/'research_inputs/asset_survival/lifetime_decisions.json').read_text())['technologies'].get(r['Technology'],{})
  self.assertNotEqual(life.get('ApprovalStatus'),'HUMAN_ACCEPTED')
  z=select_asset(dict(OriginalCapacity=r['raw']['capacity_mw'],AssetClass='OBSERVED_EXISTING',CommissioningYear=2016,CommissioningEvidenceVerified=True,Lifetime=None,LifetimeAccepted=False))
  self.assertEqual(z['SurvivalStatus'],'UNRESOLVED_RETIREMENT_OR_LIFETIME');self.assertIsNone(z['RetainedCapacity2050'])

if __name__=='__main__':unittest.main()
