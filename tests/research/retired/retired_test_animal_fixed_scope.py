"""SYNTHETIC_TEST_ONLY; explicit additional scope, no solver/model variables."""
from pathlib import Path
import sys,unittest,tempfile,pypsa
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'scripts_project'),str(R/'tests/research')]
from fixed_account_scope import load_scope
from fixed_accounts import qualify_fixed_accounts,validate_exported_accounting
from test_fixed_accounts_price_basis import fixture
def animal():
 n=fixture();scope=load_scope(R);s=scope[0];q=float(s['ExpectedAnnualMWh'])
 n.meta['additional_fixed_account_scope']=scope;n.buses['country']='PH';n.buses.at['resource','carrier']='Animal waste';n.stores.at['stock','carrier']='Animal waste';n.stores.loc['stock',['e_nom','e_initial']]=q;n.loads.at['load','p_set']=q/12;n.loads.at['load','source_account_id']=s['SourceAccountID'];n.meta['biomass_obligation_routes']['stock'].update(commodity='Animal waste',annual_cap_mwh=q,source_row=s['SourceRow'],input_id=s['SourceAccountID']);return n
class AnimalScopeTests(unittest.TestCase):
 def test_dense_input_is_read_once_per_current_validation(self):
  from unittest.mock import patch
  n=animal()
  with patch.object(n,'get_switchable_as_dense',wraps=n.get_switchable_as_dense) as spy:
   qualify_fixed_accounts(n);self.assertEqual(spy.call_count,1)
 def test_actual_scope_with_valid_structure_keeps_unknowns_null(self):
  n=animal();r=qualify_fixed_accounts(n)[0];self.assertIsNone(r['UnitPriceEUR2020PerMWh']);self.assertIsNone(r['PhysicalCO2_tPerMWh']);self.assertIn('ANIMAL-WASTE',r['DecisionReference'])
 def test_not_extended_to_other_country(self):
  n=animal();n.buses['country']='ID'
  with self.assertRaisesRegex(ValueError,'no accepted'):qualify_fixed_accounts(n)
 def test_not_extended_to_other_source_row(self):
  n=animal();n.meta['biomass_obligation_routes']['stock']['source_row']='OTHER'
  with self.assertRaisesRegex(ValueError,'no accepted'):qualify_fixed_accounts(n)
 def test_changed_quantity_rejected_even_if_structure_balances(self):
  n=animal();n.stores.loc['stock',['e_nom','e_initial']]*=2;n.loads.at['load','p_set']*=2;n.meta['biomass_obligation_routes']['stock']['annual_cap_mwh']*=2
  with self.assertRaisesRegex(ValueError,'source quantity changed'):qualify_fixed_accounts(n)
 def test_scope_and_null_ledger_survive_readback(self):
  n=animal();qualify_fixed_accounts(n)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'SYNTHETIC_TEST_ONLY.nc';n.export_to_netcdf(p);r=pypsa.Network(p);validate_exported_accounting(r);self.assertEqual(n.meta,r.meta)
 def test_authorization_does_not_waive_diversion(self):
  n=animal();n.add('Bus','other');n.add('Link','divert',bus0='resource',bus1='other',p_nom=1.)
  with self.assertRaisesRegex(ValueError,'diversion'):qualify_fixed_accounts(n)
if __name__=='__main__':unittest.main()
