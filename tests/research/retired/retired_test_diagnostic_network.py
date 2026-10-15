"""SYNTHETIC_TEST_ONLY guards plus scoped immutable-source regression; no solver."""
from pathlib import Path
import sys,unittest,tempfile,json,copy
from decimal import Decimal
import numpy as np,pandas as pd,pypsa
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts_project'),str(Path(__file__).parent)]
from build_diagnostic_network import GUARDS,verify_guards,assert_input_only,compare_roundtrip,normalise_optional_strings,check_physical_reachability
from build_research_network import load_unbound_recipe,static_validate
from assembly_components import merge_input_components,bind_loads,install_research_constraint_hooks
from reconstruct_base_accounts import account_for_transaction,Reconstruction,commodity,norm,row_id
from residual_account_mapping import official_codes,reconcile_commodity_scope
import test_gate4_assets as fixtures

class DiagnosticTests(unittest.TestCase):
 def network(self):
  n,*_=fixtures.RoundtripTests().setup_network();n.meta.update(**GUARDS,policy_enabled=False,constraint_hook_state='REGISTERED_AND_VALIDATED_NOT_EXECUTED',unmaterialised_scope={'demand_ids':['missing-test'], 'quantity':None});return n
 def test_diagnostic_guard_roundtrip_and_null(self):
  n=self.network();verify_guards(n)
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'SYNTHETIC_TEST_ONLY.nc';n.export_to_netcdf(p);a=pypsa.Network(p);compare_roundtrip(n,a);verify_guards(a);self.assertIsNone(a.meta['unmaterialised_scope']['quantity'])
 def test_diagnostic_cannot_install_optimization_hooks(self):
  with self.assertRaisesRegex(ValueError,'Diagnostic partial'):install_research_constraint_hooks(self.network())
 def test_guard_removal_rejected(self):
  for k in GUARDS:
   n=self.network();n.meta.pop(k)
   with self.subTest(k=k),self.assertRaises(ValueError):verify_guards(n)
 def test_dynamic_input_loss_rejected(self):
  n=self.network();a=n.copy();a.generators_t.p_max_pu.iloc[0,0]+=.1
  with self.assertRaises(AssertionError):compare_roundtrip(n,a)
 def test_metadata_loss_rejected(self):
  n=self.network();a=n.copy();a.meta=copy.deepcopy(n.meta);a.meta.pop('unmaterialised_scope')
  with self.assertRaisesRegex(ValueError,'metadata'):compare_roundtrip(n,a)
 def test_only_optional_string_nulls_normalised(self):
  n=self.network();n.stores['optional_tag']=None;n.stores['unknown_numeric_parameter']=np.nan
  changed=normalise_optional_strings(n);self.assertIn('Store.optional_tag',changed);self.assertTrue(n.stores.unknown_numeric_parameter.isna().all());self.assertIsNone(n.meta['unmaterialised_scope']['quantity'])
 def test_bound_development_base_rejected(self):
  n=self.network()
  with self.assertRaisesRegex(ValueError,'bound demand'):assert_input_only(n)
 def test_bound_development_fragment_rejected(self):
  n=self.network();sub=n.copy()
  with self.assertRaisesRegex(ValueError,'Bound development'):merge_input_components(n,sub)
 def test_bound_json_and_netcdf_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'bound.json';p.write_text(json.dumps({'components':{'load':{'type':'Load'}}}))
   with self.assertRaisesRegex(ValueError,'Bound demand'):load_unbound_recipe(p)
   with self.assertRaisesRegex(ValueError,'unbound JSON'):load_unbound_recipe(p.with_suffix('.nc'))
 def test_duplicate_binding_rejected(self):
  n,r,m,a,d=fixtures.RoundtripTests().setup_network()
  with self.assertRaisesRegex(ValueError,'only once'):bind_loads(n,r,m,a,d)
 def test_foreign_physical_path_rejected(self):
  n,r,*_=fixtures.RoundtripTests().setup_network();n.add('Bus','ID hydrogen',carrier='H2');n.buses.loc['ID hydrogen','country']='ID';n.add('Link','forbidden',bus0='SG H2',bus1='ID hydrogen',carrier='H2',efficiency=1)
  with self.assertRaisesRegex(ValueError,'Cross-country non-electric'):static_validate(n,r,None,[],synthetic_test_only=True)
 def test_supply_path_is_required_but_not_optimisation(self):
  n=self.network();self.assertEqual(check_physical_reachability(n)['loads_reachable'],2)
  n.remove('Link','test BD meter')
  with self.assertRaisesRegex(ValueError,'structural supply'):check_physical_reachability(n)

class NECAliasTests(unittest.TestCase):
 def test_official_leaf_not_other_parent_or_industry(self):
  self.assertEqual(account_for_transaction('Consumption by other consumers not elsewhere specified'),'OtherNEC')
  self.assertEqual(account_for_transaction('Consumption not elsewhere specified (other)'),'OtherNEC')
  for t in ['Consumption by other','Consumption not elsewhere specified (industry)','Consumption by transport']:self.assertIsNone(account_for_transaction(t))
 def test_two_1234_labels_cannot_double_count(self):
  common=dict(Country='MM',Year='2019',Commodity='Liquefied petroleum gas (LPG)',Unit='Metric tons,  thousand',SourceSHA256='SYNTHETIC_TEST_ONLY',Quantity='29')
  p=dict(common,Transaction='Final energy consumption');a=dict(common,Transaction='Consumption not elsewhere specified (other)');b=dict(common,Transaction='Consumption by other consumers not elsewhere specified')
  with self.assertRaisesRegex(ValueError,'duplicate'):reconcile_commodity_scope(p,[a,b])
 def test_frozen_lpg_leaf_closure_without_new_values(self):
  s=ROOT/'research_inputs/assembly_v1/sources';codes=official_codes(s/'unsd_targeted/DSD_Energy.xml');self.assertEqual(codes['CL_TRANSACTION_NRG']['1234'],'Consumption not elsewhere specified (other)')
  b=Reconstruction(json.loads((s/'UNSD_2019_SOURCE_CAPSULE.json').read_text()),json.loads((s/'FROZEN_UPSTREAM_CONVERSIONS.json').read_text()))
  for c in ['MM','TL']:
   rs=[r for r in b.rows if r['Country']==c and commodity(r['Commodity'])=='liquefied petroleum gas (lpg)'];p=next(r for r in rs if norm(r['Transaction'])=='final energy consumption');leaves=[r for r in rs if account_for_transaction(r['Transaction']) is not None];old=copy.deepcopy(leaves)
   result=reconcile_commodity_scope(p,leaves);self.assertEqual(result['Status'],'SOURCE_TOTAL_CLOSED');self.assertEqual(Decimal(result['Difference']),Decimal(0));self.assertEqual(leaves,old);self.assertEqual(len({row_id(r) for r in leaves}),len(leaves))
   without=[r for r in leaves if account_for_transaction(r['Transaction'])!='OtherNEC'];self.assertEqual(reconcile_commodity_scope(p,without)['Status'],'SOURCE_TOTAL_NOT_CLOSED')

if __name__=='__main__':unittest.main()
