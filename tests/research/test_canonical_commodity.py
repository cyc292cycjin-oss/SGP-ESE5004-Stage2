"""SYNTHETIC_TEST_ONLY fixtures; no solver. Frozen-source regressions explicit."""
import sys,json,copy,unittest,tempfile
from pathlib import Path
import numpy as np,pandas as pd,pypsa
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'));sys.path.insert(0,str(Path(__file__).parent))
from residual_account_mapping import reconcile_commodity_scope
from reconstruct_base_accounts import Reconstruction,commodity,row_id
import test_gate4_exact_closure as prior_tests

class CanonicalTests(unittest.TestCase):
 def test_alias_parent_and_leaf_labels_preserved(self):
  p,rs=prior_tests.BalanceTests().rows();p['Commodity']='Natural Gas';rs[0]['Commodity']='Natural gas (including LNG)';rs[1]['Commodity']='natural gas';old=copy.deepcopy((p,rs));a=reconcile_commodity_scope(p,rs);self.assertEqual(a['Status'],'SOURCE_TOTAL_CLOSED');self.assertEqual((p,rs),old);self.assertEqual(a['RawParentCommodity'],'Natural Gas')
 def test_distinct_fuels_never_fuzzy_match(self):
  for label in ['Biogasoline','Biodiesel','Natural gas liquids','Liquefied petroleum gas (LPG)']:
   p,rs=prior_tests.BalanceTests().rows();p['Commodity']='Motor gasoline';rs[0]['Commodity']=label;rs[1]['Commodity']='motor gasoline'
   with self.subTest(label=label),self.assertRaisesRegex(ValueError,'commodity'):reconcile_commodity_scope(p,rs)
 def test_other_scope_dimensions_still_rejected(self):
  for k,v in [('Country','Y'),('Year',2020),('Unit','kt'),('SourceSHA256','revision2')]:
   p,rs=prior_tests.BalanceTests().rows();rs[0][k]=v
   with self.subTest(k=k),self.assertRaises(ValueError):reconcile_commodity_scope(p,rs)
 def test_alias_duplicate_not_double_counted(self):
  p,rs=prior_tests.BalanceTests().rows();p['Commodity']='Natural Gas'
  for r in rs:r['Commodity']='natural gas'
  with self.assertRaisesRegex(ValueError,'duplicate'):reconcile_commodity_scope(p,rs+[dict(rs[0],Commodity='Natural gas (including LNG)')])
 def test_declared_precision_not_gap_filling(self):
  p,rs=prior_tests.BalanceTests().rows();rs[1]['Quantity']='3.000000000000001';r=reconcile_commodity_scope(p,rs);self.assertEqual(r['Status'],'SOURCE_TOTAL_CLOSED_WITH_FLOAT_PRECISION');self.assertNotEqual(r['Difference'],'0')
  rs[1]['Quantity']='3.0000001';self.assertEqual(reconcile_commodity_scope(p,rs)['Status'],'SOURCE_TOTAL_NOT_CLOSED')
 def test_frozen_my_alias_regression_and_row_identity(self):
  folder=ROOT/'research_inputs/assembly_v1/sources';b=Reconstruction(json.loads((folder/'UNSD_2019_SOURCE_CAPSULE.json').read_text()),json.loads((folder/'FROZEN_UPSTREAM_CONVERSIONS.json').read_text()))
  from reconstruct_base_accounts import norm,account_for_transaction
  for product,expected in [('liquefied petroleum gas (lpg)','1212.702'),('natural gas (including lng)','364167.199')]:
   rs=[r for r in b.rows if r['Country']=='MY' and commodity(r['Commodity'])==product];p=next(r for r in rs if norm(r['Transaction'])=='final energy consumption');parts=[r for r in rs if account_for_transaction(r['Transaction']) not in [None,'InternationalShippingBunker','InternationalAviationBunker']];before=copy.deepcopy(parts);out=reconcile_commodity_scope(p,parts);self.assertEqual(out['Status'],'SOURCE_TOTAL_CLOSED');self.assertEqual(out['ParentRawValue'],expected);self.assertEqual(out['ExclusiveUsesRawValue'],expected);self.assertEqual(parts,before);self.assertEqual(len({row_id(r) for r in parts}),len(parts))

if __name__=='__main__':unittest.main()
