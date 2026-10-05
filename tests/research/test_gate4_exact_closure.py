"""SYNTHETIC_TEST_ONLY alterations; exact real-source request coverage. NO SOLVER."""
from pathlib import Path
import sys,json,copy,unittest,tempfile
import numpy as np,pandas as pd,pypsa,linopy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'));sys.path.insert(0,str(Path(__file__).parent))
from reconstruct_base_accounts import reconstruct
from residual_account_mapping import build_crosswalk,validate_crosswalk,official_codes,reconcile_commodity_scope
from fixed_accounts import accounting_report
from integrate_surviving_assets import install_existing_asset_constraints
from test_fixed_accounts_price_basis import fixture

class MappingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.s=ROOT/'research_inputs/assembly_v1/sources';cls.result=reconstruct(cls.s)
  cls.rows=build_crosswalk(cls.result,cls.s,json.loads((ROOT/'research_inputs/assembly_v1/registry.json').read_text()),json.loads((ROOT/'research/04_model_assembly/gate4/UNSD_TARGETED_RETRIEVAL_RECEIPT.json').read_text()))
 def test_every_overlap_has_request(self):
  self.assertEqual(len(self.rows),len(self.result['biofuel_overlap']));validate_crosswalk(self.result,self.rows,self.s)
 def test_missing_mapping_rejected(self):
  with self.assertRaisesRegex(ValueError,'no exact'):validate_crosswalk(self.result,self.rows[1:],self.s)
 def test_service_agriculture_inversion_rejected(self):
  rows=copy.deepcopy(self.rows);next(r for r in rows if r['Country']=='ID' and r['Account']=='ServicesFuel')['Transaction']='1232'
  with self.assertRaisesRegex(ValueError,'transaction mismatch'):validate_crosswalk(self.result,rows,self.s)
 def test_official_codes(self):
  c=official_codes(self.s/'unsd_targeted/DSD_Energy.xml')['CL_TRANSACTION_NRG'];self.assertIn('commerce',c['1235']);self.assertIn('agriculture',c['1232'])
 def test_wrong_country_year_or_commodity_rejected(self):
  for key,value in [('Country','MY'),('Year',2020),('MemoSDMXCode','5212')]:
   rows=copy.deepcopy(self.rows);rows[0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):validate_crosswalk(self.result,rows,self.s)
 def test_id_services_already_requested(self):
  r=next(r for r in self.rows if r['Country']=='ID' and r['Account']=='ServicesFuel');self.assertEqual(r['Transaction'],'1235');self.assertTrue(r['PriorTargetedQueryCovered']);self.assertFalse(r['SourceOverlapResolved'])
 def test_petroleum_identity_not_crossed(self):
  for r in self.rows:self.assertEqual(r['ParentCommodity'].lower(),'gas oil/ diesel oil' if r['MemoCommodity']=='ZD' else 'motor gasoline')

class BalanceTests(unittest.TestCase):
 def rows(self):
  p=dict(Country='X',Year=2019,Commodity='test',Unit='TJ',SourceSHA256='SYNTHETIC',Quantity='10',Transaction='Final energy consumption');a=dict(p,Quantity='7',Transaction='Consumption by road');b=dict(p,Quantity='3',Transaction='Consumption not elsewhere specified (transport)');return p,[a,b]
 def test_exact_total_closure(self):
  p,parts=self.rows();self.assertEqual(reconcile_commodity_scope(p,parts)['Status'],'SOURCE_TOTAL_CLOSED')
 def test_real_gap_not_renamed_resolution(self):
  p,parts=self.rows();parts[1]['Quantity']='2';self.assertEqual(reconcile_commodity_scope(p,parts)['Difference'],'1')
 def test_parent_missing_not_zero(self):self.assertIsNone(reconcile_commodity_scope(None,[])['Difference'])
 def test_vintage_mismatch_rejected(self):
  p,parts=self.rows();parts[1]['SourceSHA256']='NEW'
  with self.assertRaisesRegex(ValueError,'scope'):reconcile_commodity_scope(p,parts)
 def test_duplicate_use_rejected(self):
  p,parts=self.rows()
  with self.assertRaisesRegex(ValueError,'duplicate'):reconcile_commodity_scope(p,parts+[parts[0]])
 def test_parent_cannot_be_added_to_children(self):
  p,parts=self.rows()
  with self.assertRaisesRegex(ValueError,'Non-leaf'):reconcile_commodity_scope(p,parts+[p])

def synthetic_link(reverse=False):
 n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=1,freq='3h'));n.snapshot_weightings.loc[:,:]=3.
 n.add('Carrier','AC');n.add('Bus','a',carrier='AC');n.add('Bus','b',carrier='AC');n.add('Generator','g',bus='a',p_nom=100,marginal_cost=0)
 n.add('Link','l',bus0='b' if reverse else 'a',bus1='a' if reverse else 'b',p_nom=100,p_min_pu=-1,efficiency=1,marginal_cost=.01)
 n.optimize.create_model();return n

class DirectionTests(unittest.TestCase):
 def test_actual_pypsa_signed_linear_objective(self):
  self.assertEqual(pypsa.__version__,'0.30.3');n=synthetic_link();label=int(n.model['Link-p'].labels.values[0,0]);e=n.model.objective.expression
  coefficient=float(e.coeffs.where(e.vars==label,0).sum());self.assertAlmostEqual(coefficient,.03);self.assertAlmostEqual(coefficient*100,3);self.assertAlmostEqual(coefficient*-100,-3)
 def test_bus_orientation_changes_same_physical_transfer_cost(self):
  n=synthetic_link(True);label=int(n.model['Link-p'].labels.values[0,0]);e=n.model.objective.expression;coefficient=float(e.coeffs.where(e.vars==label,0).sum())
  self.assertAlmostEqual(coefficient*(-100),-3);self.assertNotEqual(coefficient*(-100),coefficient*abs(-100))
 def test_no_solver_run(self):
  n=synthetic_link();self.assertEqual(n.model.status,'initialized');self.assertEqual(len(n.links_t.p0.columns),0)

class FixedInclusionTests(unittest.TestCase):
 def test_unverified_objective_inclusion_rejected(self):
  n=fixture();n.meta['existing_annual_fixed_om_eur']=100
  with self.assertRaisesRegex(ValueError,'inclusion'):accounting_report(n,priced_objective=102)
 def test_installed_known_fom_not_added_again(self):
  n=fixture();n.meta['existing_annual_fixed_om_eur']=100;n.model=linopy.Model();x=n.model.add_variables(lower=1,upper=1,name='SYNTHETIC_FIXED_ONE');n.model.add_objective(2*x);install_existing_asset_constraints(n)
  r=accounting_report(n,priced_objective=102);self.assertTrue(r['KnownFixedCostIncludedInPricedObjective']);self.assertEqual(r['KnownFixedCostToAddToPricedObjective'],0);self.assertEqual(r['KnownFixedCost'],100);self.assertFalse(r['PendingFixedCostIncludedInPricedObjective'])
 def test_unbuilt_objective_inclusion_is_null(self):
  n=fixture();r=accounting_report(n);self.assertIsNone(r['KnownFixedCostIncludedInPricedObjective']);self.assertIsNone(r['KnownFixedCostToAddToPricedObjective'])

if __name__=='__main__':unittest.main()
