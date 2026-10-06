"""SYNTHETIC_TEST_ONLY: no optimizer variables, no solver."""
from pathlib import Path
import sys, unittest, numpy as np, pandas as pd, pypsa
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'scripts_project'),str(R/'tests/research')]
from validate_fullsc_final import numeric_inputs
from fixed_accounts import validate_fixed_accounts,qualify_fixed_accounts
from test_fixed_accounts_price_basis import fixture
class PhysicalChecks(unittest.TestCase):
 def port_fixture(self):
  n=pypsa.Network();n.add('Bus','a');n.add('Bus','b');n.add('Link','x',bus0='a',bus1='b',p_nom=1.);n.links['bus3']='';n.links['efficiency3']=np.nan;return n
 def test_unconnected_port_has_no_coefficient(self):
  self.assertTrue(any(x['Meaning']=='NON_APPLICABLE_UNCONNECTED_LINK_PORT' for x in numeric_inputs(self.port_fixture())))
 def test_connected_port_missing_coefficient_rejects(self):
  n=self.port_fixture();n.links.loc['x','bus3']='b'
  with self.assertRaisesRegex(ValueError,'efficiency3'):numeric_inputs(n)
 def test_missing_real_cost_rejects(self):
  n=self.port_fixture();n.links.loc['x','capital_cost']=np.nan
  with self.assertRaisesRegex(ValueError,'capital_cost'):numeric_inputs(n)
 def test_pending_animal_structural_proof_does_not_accept_boundary(self):
  n=fixture();n.stores.loc['stock','carrier']='Animal waste';n.buses.loc['resource','carrier']='Animal waste';n.meta['biomass_obligation_routes']['stock']['commodity']='Animal waste'
  r=validate_fixed_accounts(n,structure_only=True)[0]
  self.assertEqual(r['BoundaryAcceptance'],'PENDING_ADDITIONAL_COMMODITY_BOUNDARY');self.assertIsNone(r['DecisionReference']);self.assertIsNone(r['PhysicalCO2_tPerMWh'])
  with self.assertRaisesRegex(ValueError,'no accepted'):qualify_fixed_accounts(n)
 def test_pending_commodity_still_fails_diversion(self):
  n=fixture();n.stores.loc['stock','carrier']='Animal waste';n.buses.loc['resource','carrier']='Animal waste';n.meta['biomass_obligation_routes']['stock']['commodity']='Animal waste';n.add('Bus','extra');n.add('Link','divert',bus0='resource',bus1='extra',p_nom=1.)
  with self.assertRaisesRegex(ValueError,'diversion'):validate_fixed_accounts(n,structure_only=True)
if __name__=='__main__':unittest.main()
