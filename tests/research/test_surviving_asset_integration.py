from pathlib import Path
import sys,copy,json,tempfile,unittest
import numpy as np,pandas as pd,pypsa
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
from unit_asset_survival import reconcile_units
from integrate_surviving_assets import integrate_survivors,install_existing_asset_constraints
from assembly_components import validate_hooks

def parent():
 return dict(AssetID='PPM:test',Country='SG',Technology='Wind',OriginalCapacity=100.,SourceIDs=['old','new'],SourceSubassets=[dict(ID=k,Status='operating',StartYear=y,RetiredYear=None,Capacity=c,Source='SYNTHETIC_TEST_ONLY',SourceSHA256='fixture',Sheet='Units',ExcelRow=i) for i,(k,y,c) in enumerate([('old',2000,40.),('new',2020,60.)],2)],Lifetime=40.,LifetimeSource='SYNTHETIC_TEST_ONLY',OriginalMappedBus='raw-a',CostTreatment='SYNTHETIC_TEST_ONLY',ResourceLimitTreatment='SYNTHETIC_TEST_ONLY',SurvivalStatus='UNRESOLVED_COMMISSIONING')
DECISION=dict(ApprovalStatus='HUMAN_ACCEPTED',DecisionReference='SYNTHETIC_TEST_ONLY',Source='SYNTHETIC_TEST_ONLY')
def evidence():return reconcile_units([parent()],{'Wind':dict(DECISION,Lifetime=40.)})
def network():
 n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01','2013-12-31 21:00',freq='3h'));n.snapshot_weightings.loc[:,:]=3.
 n.add('Carrier','AC');n.add('Carrier','onwind')
 for i in range(100):n.add('Bus','SG '+str(i),carrier='AC');n.buses.loc['SG '+str(i),'country']='SG'
 for x in ['new-a','new-b']:n.add('Generator',x,bus='SG 0',carrier='onwind',p_nom_extendable=True,p_nom_max=150.,p_max_pu=np.linspace(.2,.8,2920),capital_cost=123.)
 n.meta=dict(purpose='SYNTHETIC_TEST_ONLY',solver_allowed=False,target_year=2050,weather_year=2013,required_constraint_hooks=[])
 return n
def contract():
 return dict(mapping={'raw-a':dict(DECISION,Node='SG 0',Country='SG',OriginalPartition='island-a',NodePartition='island-a')},performance={'Wind':dict(DECISION,ComponentType='Generator',Carrier='onwind',Efficiency=.95,FixedOM_EUR_per_MW_e_year=12000.,VariableOM_EUR_per_MWh_e=3.,CostBasis='EXISTING_NO_NEW_CAPEX',PerformanceBasis='SOURCE_EXISTING_EQUIPMENT',ResourceGroup='wind-sg0',Profiles={'p_max_pu':dict(Source='SYNTHETIC_TEST_ONLY',ComponentType='Generator',Component='new-a',Multiplier=1.)})},resource_groups={'wind-sg0':dict(DECISION,Meaning='TOTAL_CAPACITY',LimitMW=150.,NewBuildComponents=[dict(ComponentType='Generator',Name=k,CapacityToMW=1.) for k in ['new-a','new-b']])})

class UnitTests(unittest.TestCase):
 def test_different_year_units_selected_before_aggregation(self):
  e=evidence();by={r['RawUnitID']:r for r in e['records']};self.assertEqual(by['old']['RetainedCapacity2050'],0);self.assertEqual(by['new']['RetainedCapacity2050'],60.)
  self.assertEqual(e['parent_reconciliation'][0]['AcceptedRetainedMW'],60.)
 def test_candidate_lifetimes_not_accepted(self):
  e=reconcile_units([parent()]);self.assertTrue(all(r['RetainedCapacity2050'] is None for r in e['records']));self.assertEqual(sum(r['ConditionalRetainedMW'] or 0 for r in e['records']),60.)
 def test_parent_country_technology_conservation(self):
  e=evidence();self.assertEqual(sum(r['OriginalCapacity'] for r in e['records']),100.);self.assertEqual(e['parent_reconciliation'][0]['SignedCapacityDifference'],0.)
 def test_duplicate_raw_id_rejected(self):
  with self.assertRaisesRegex(ValueError,'Duplicate raw'):reconcile_units([parent(),parent()])
 def test_partial_unknown_keeps_known_part(self):
  p=parent();p['SourceSubassets'][0]['StartYear']=None;e=reconcile_units([p]);self.assertEqual(e['parent_reconciliation'][0]['MissingCommissioningSourceCapacity'],40.);self.assertEqual(e['parent_reconciliation'][0]['KnownCommissioningCapacity'],60.)
 def test_capacity_mismatch_not_normalized(self):
  p=parent();p['OriginalCapacity']=90.;e=reconcile_units([p],{'Wind':dict(DECISION,Lifetime=40.)});self.assertEqual(e['parent_reconciliation'][0]['SignedCapacityDifference'],-10.);self.assertEqual(sum(r['OriginalCapacity'] for r in e['records']),100.);self.assertTrue(all(r['RetainedCapacity2050'] in [None,0] for r in e['records']))

class IntegrationTests(unittest.TestCase):
 def test_real_existing_component_cost_and_profile_roundtrip(self):
  n=network();c=contract();r=integrate_survivors(n,evidence(),c,profile_network=n);name='existing_survivor::GEM:new'
  self.assertEqual(n.generators.at[name,'p_nom'],60.);self.assertFalse(n.generators.at[name,'p_nom_extendable']);self.assertEqual(n.generators.at[name,'capital_cost'],0.)
  self.assertEqual(n.generators.at[name,'efficiency'],.95);self.assertEqual(n.generators.at[name,'marginal_cost'],3.);self.assertEqual(n.meta['existing_annual_fixed_om_eur'],720000.)
  self.assertEqual(n.generators.at['new-a','capital_cost'],123.);self.assertEqual(n.generators.at['new-a','p_nom_max'],90.)
  from pypsa.descriptors import get_activity_mask
  self.assertTrue(get_activity_mask(n,'Generator')[name].all()) #2050 selection independent of2013 weather
  validate_hooks(n)
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'SYNTHETIC_TEST_ONLY.nc';n.export_to_netcdf(p);b=pypsa.Network(p);validate_hooks(b)
   self.assertEqual(b.meta,n.meta);self.assertEqual(len(b.buses),100);self.assertEqual(b.generators.at[name,'source_unit_id'],'new');self.assertEqual(b.generators.at[name,'p_nom'],60.)
   np.testing.assert_array_equal(b.generators_t.p_max_pu[name],n.generators_t.p_max_pu[name]);self.assertEqual(b.snapshots[0].year,2013)
  out=ROOT/'results_project/assembly_v1_tests';out.mkdir(parents=True,exist_ok=True)
  (out/'SURVIVOR_INTEGRATION_ROUNDTRIP.json').write_text(json.dumps(dict(purpose='SYNTHETIC_TEST_ONLY',status='PASS',surviving_electric_capacity_mw=60.,remaining_shared_new_limit_mw=90.,annual_fixed_om_eur=720000.,geographical_nodes=100,snapshots=2920,source_identity_and_profiles_preserved=True,solver_runs=0),indent=2)+'\n')
 def test_cross_country_rejected(self):
  n=network();c=contract();c['mapping']['raw-a']['Country']='MY'
  with self.assertRaisesRegex(ValueError,'country'):integrate_survivors(n,evidence(),c,n)
 def test_cross_partition_rejected(self):
  n=network();c=contract();c['mapping']['raw-a']['NodePartition']='island-b'
  with self.assertRaisesRegex(ValueError,'partition'):integrate_survivors(n,evidence(),c,n)
 def test_candidate_mapping_keeps_stock_pending(self):
  n=network();c=contract();c['mapping']['raw-a']['ApprovalStatus']='PENDING';r=integrate_survivors(n,evidence(),c,n);self.assertEqual(r['integrated_units'],0);self.assertEqual(len(r['pending_qualified_units']),1)
 def test_additional_potential_not_deducted(self):
  n=network();c=contract();c['resource_groups']['wind-sg0']['Meaning']='ADDITIONAL_POTENTIAL';integrate_survivors(n,evidence(),c,n);self.assertEqual(n.generators.at['new-a','p_nom_max'],150.)
 def test_shared_potential_hook_and_fom_constant_without_solver(self):
  import linopy
  n=network();integrate_survivors(n,evidence(),contract(),n);n.model=linopy.Model()
  x=n.model.add_variables(lower=0,coords=[pd.Index(['new-a','new-b'],name='Generator-ext')],name='Generator-p_nom');n.model.add_objective(x.sum())
  install_existing_asset_constraints(n)
  fixed=n.model.variables['Research-existing-FOM-constant'];self.assertEqual(float(fixed.lower),1.);self.assertEqual(float(fixed.upper),1.)
  self.assertIn(720000.,n.model.objective.expression.coeffs.values);self.assertEqual(float(n.model.constraints['ResearchExistingResource-wind-sg0'].rhs),90.)
  self.assertEqual(len(n.model.constraints['ResearchExistingResource-wind-sg0'].coeffs.values),2)
  with self.assertRaisesRegex(ValueError,'already'):install_existing_asset_constraints(n)
 def test_existing_om_not_silently_zero(self):
  n=network();c=contract();c['performance']['Wind']['FixedOM_EUR_per_MW_e_year']=0.
  with self.assertRaisesRegex(ValueError,'zero'):integrate_survivors(n,evidence(),c,n)
 def test_old_efficiency_not_auto_upgraded(self):
  n=network();c=contract();c['performance']['Wind']['PerformanceBasis']='2050_NEW_TECH'
  with self.assertRaisesRegex(ValueError,'boundary'):integrate_survivors(n,evidence(),c,n)
 def test_repeated_integration_rejected(self):
  n=network();integrate_survivors(n,evidence(),contract(),n)
  with self.assertRaisesRegex(ValueError,'already'):integrate_survivors(n,evidence(),contract(),n)
 def test_existing_thermal_is_physical_fuel_link(self):
  n=network();c=contract();p=c['performance']['Wind'];p.update(ComponentType='Link',Carrier='CCGT existing',FuelCarrier='gas',PhysicalCO2_t_per_MWh_fuel=.2,Efficiency=.4,Profiles={},ResourceGroup='EXISTING_ONLY_NO_NEW_CANDIDATE',ExistingOnlyEvidence='SYNTHETIC_TEST_ONLY')
  integrate_survivors(n,evidence(),c,n);name='existing_survivor::GEM:new';self.assertEqual(n.links.at[name,'p_nom'],150.);self.assertAlmostEqual(n.links.at[name,'marginal_cost'],1.2);self.assertEqual(n.meta['existing_carbon_components'][0]['coefficient'],.2)
 def test_survivors_aggregated_after_unit_selection(self):
  n=network();e=reconcile_units([parent()],{'Wind':dict(DECISION,Lifetime=100.)});r=integrate_survivors(n,e,contract(),n)
  self.assertEqual(r['integrated_units'],2);self.assertEqual(r['integrated_components'],1);self.assertEqual(r['integrated_capacity_mw'],100.)
  self.assertEqual(len({v['component'] for v in n.meta['existing_unit_components'].values()}),1);validate_hooks(n)
 def test_hydro_storage_input_survives_roundtrip(self):
  n=network();source=network();source.add('StorageUnit','source hydro',bus='SG 0',p_nom=100.,inflow=np.linspace(1.,3.,2920))
  c=contract();c['performance']['Wind'].update(ComponentType='StorageUnit',Carrier='hydro',Efficiency=.9,EfficiencyStore=1.,MaxHours=12.,CyclicStateOfCharge=True,Profiles={'inflow':dict(Source='SYNTHETIC_TEST_ONLY',ComponentType='StorageUnit',Component='source hydro',Multiplier=.6)},ResourceGroup='EXISTING_ONLY_NO_NEW_CANDIDATE',ExistingOnlyEvidence='SYNTHETIC_TEST_ONLY')
  integrate_survivors(n,evidence(),c,source);name='existing_survivor::GEM:new'
  self.assertEqual(n.storage_units.at[name,'p_nom'],60.);self.assertEqual(n.storage_units.at[name,'max_hours'],12.)
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'hydro.nc';n.export_to_netcdf(p);b=pypsa.Network(p);np.testing.assert_array_equal(n.storage_units_t.inflow[name],b.storage_units_t.inflow[name]);validate_hooks(b)
 def test_combustion_cannot_bypass_fuel_carbon_ports(self):
  n=network();e=evidence();next(r for r in e['records'] if r['SurvivalStatus']=='SURVIVES_2050')['Technology']='Hard Coal';c=contract();c['performance']['Hard Coal']=c['performance']['Wind']
  with self.assertRaisesRegex(ValueError,'combustion'):integrate_survivors(n,e,c,n)
 def test_optimised_or_changed_capacity_cannot_replace_original_stock(self):
  n=network();e=evidence();next(r for r in e['records'] if r['SurvivalStatus']=='SURVIVES_2050')['RetainedCapacity2050']=150.
  with self.assertRaisesRegex(ValueError,'original source'):integrate_survivors(n,e,contract(),n)
if __name__=='__main__':unittest.main(verbosity=2)
