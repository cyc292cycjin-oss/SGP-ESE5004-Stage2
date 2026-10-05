"""SYNTHETIC_TEST_ONLY fixtures; no solver. Frozen-source regressions explicit."""
import sys,json,copy,unittest,tempfile
from pathlib import Path
import numpy as np,pandas as pd,pypsa
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'));sys.path.insert(0,str(Path(__file__).parent))
from residual_account_mapping import reconcile_commodity_scope
from reconstruct_base_accounts import Reconstruction,commodity,row_id
from selected_closure import retirement_upper_bound,DECISION,validate_allocated_resources,resource_profile
from asset_survival import select_asset

def cohort():
 return dict(AssetClass='OBSERVED_EXISTING',OriginalCapacity=10.,CommissioningYear=2016.25,CommissioningEvidenceVerified=False,ReportedPlantYear=2016.25,ReportedPlantYearSource='SYNTHETIC_SOURCE',CohortMethod='ASSEMBLY_V1_REPORTED_PLANT_COHORT_PROXY',CohortDecisionReference=DECISION+'#D',Lifetime=40,LifetimeAccepted=True)

class CohortBoundTests(unittest.TestCase):
 def test_known_duplicate_is_represented_elsewhere_not_missing_or_retired(self):
  from selected_closure import qualify_cohort_identity
  r=qualify_cohort_identity(select_asset(cohort()),'DUPLICATE_EXISTING_GEM_SITE');self.assertEqual(r['SurvivalStatus'],'NOT_INHERITED_DUPLICATE_SOURCE');self.assertEqual(r['RetainedCapacity2050'],0);self.assertEqual(r['OriginalCapacity'],10);self.assertIn('NOT_PHYSICALLY_RETIRED',r['InventoryDisposition'])
 def test_different_source_id_does_not_prove_independence(self):
  from selected_closure import qualify_cohort_identity
  r=qualify_cohort_identity(select_asset(cohort()),'DIFFERENT_SOURCE_ID_ONLY');self.assertEqual(r['SurvivalStatus'],'UNRESOLVED_PHYSICAL_IDENTITY');self.assertIsNone(r['RetainedCapacity2050'])
 def test_fractional_year_never_rounded(self):
  r=select_asset(cohort());self.assertEqual(r['CommissioningYear'],2016.25);self.assertEqual(r['RetirementYear'],2056.25);self.assertEqual(r['RetainedCapacity2050'],10)
 def test_cohort_requires_explicit_approval_and_source(self):
  for key in ['CohortDecisionReference','ReportedPlantYearSource','ReportedPlantYear']:
   r=cohort();r.pop(key)
   with self.subTest(key=key):self.assertEqual(select_asset(r)['SurvivalStatus'],'UNRESOLVED_COMMISSIONING')
 def test_true_retirement_priority(self):
  r=cohort();r.update(RetirementYear=2040,RetirementEvidenceVerified=True);self.assertEqual(select_asset(r)['RetainedCapacity2050'],0)
 def test_planned_cannot_become_existing(self):
  r=cohort();r['AssetClass']='COMMITTED_OR_PLANNED';self.assertTrue(select_asset(r)['SurvivalStatus'].startswith('NOT_INHERITED'))
 def bound(self):
  r=cohort();r.update(CommissioningYear=None,Lifetime=25,OperatingObservation=dict(Year=2025,EvidenceKind='DATED_OPERATING_SOURCE_SNAPSHOT',Verified=True,Source='SYNTHETIC2025 operating roster'));return r
 def test_upper_bound_proof_without_fabricated_year(self):
  r=retirement_upper_bound(self.bound());self.assertIsNone(r['CommissioningYear']);self.assertIsNone(r['RetirementYear']);self.assertEqual(r['RetirementUpperBound'],2050);self.assertEqual(r['RetainedCapacity2050'],0)
 def test_download_date_not_operating_evidence(self):
  r=self.bound();r['OperatingObservation']['EvidenceKind']='DOWNLOAD_DATE';self.assertIsNone(retirement_upper_bound(r))
 def test_planned_or_longer_life_stays_pending(self):
  r=self.bound();r['AssetClass']='COMMITTED_OR_PLANNED';self.assertIsNone(retirement_upper_bound(r));r=self.bound();r['Lifetime']=40;self.assertIsNone(retirement_upper_bound(r))

class ZeroDirectionalCostTests(unittest.TestCase):
 def test_signed_flows_and_port_swap_have_zero_fee(self):
  for reverse in [False,True]:
   n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=1));n.snapshot_weightings.loc[:,:]=3;n.add('Carrier','AC');n.add('Bus','a',carrier='AC');n.add('Bus','b',carrier='AC');n.add('Generator','g',bus='a',p_nom_extendable=True,capital_cost=1)
   n.add('Link','l',bus0='b' if reverse else 'a',bus1='a' if reverse else 'b',p_nom=100,p_min_pu=-1,efficiency=1,capital_cost=5,marginal_cost=0);n.optimize.create_model();label=int(n.model['Link-p'].labels.values[0,0]);e=n.model.objective.expression;cost=float(e.coeffs.where(e.vars==label,0).sum());self.assertEqual(cost*100,0);self.assertEqual(cost*-100,0);self.assertEqual(n.links.at['l','capital_cost'],5);self.assertEqual(n.model.status,'initialized')

class ResourceAllocationTests(unittest.TestCase):
 def test_missing_beneficiary_revokes_resource_qualification(self):
  ledger=[dict(ResourceIdentity='r',RecipientNode='a',AllocationShare=1.,AllocatedEmaxMWh=10.,OriginalEmaxMWh=10.,RecipientUnits=['u'])]
  with self.assertRaisesRegex(ValueError,'beneficiary'):validate_allocated_resources(dict(resource_reallocation=ledger,performance={}),None,[])
 def test_duplicate_or_extra_resource_rejected(self):
  r=dict(ResourceIdentity='r',RecipientNode='a',AllocationShare=1.,AllocatedEmaxMWh=10.,OriginalEmaxMWh=10.,RecipientUnits=['u'])
  for rows in [[r,r],[dict(r,AllocationShare=2.)],[dict(r,AllocatedEmaxMWh=20.)]]:
   with self.assertRaises(ValueError):validate_allocated_resources(dict(resource_reallocation=rows,performance={}),None,['u'])

if __name__=='__main__':unittest.main()
