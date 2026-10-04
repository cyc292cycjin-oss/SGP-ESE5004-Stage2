from pathlib import Path
import unittest,tempfile,json,sys,copy
import numpy as np,pandas as pd,pypsa
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
from assembly_components import merge_input_components,bind_loads,check_global_constraints
from build_research_network import static_validate
from reconcile_unsd_blends import reconcile
from asset_survival import select_asset,remaining_resource

class SourceAndAssetTests(unittest.TestCase):
 def blend(self):
  common=dict(Country='MY',Year=2019,Transaction='1221',Unit='Metric tons,  thousand',Vintage='SYNTHETIC_TEST_ONLY',InclusionVerified=True)
  return [dict(common,CommodityCode=c,Quantity=q,SourceRow=c+' fixture') for c,q in [('DL','100'),('BD','20'),('ZD','15')]]
 def test_compatible_positive_mass_split(self):
  r=reconcile(*self.blend());self.assertEqual(r['FossilMass'],'85');self.assertEqual(r['BioTotalMass'],'20')
 def test_frozen_missing_memo_rejected(self):
  p,b,_=self.blend()
  with self.assertRaisesRegex(ValueError,'memo'):reconcile(p,b,None)
 def test_versions_units_and_national_memo_rejected(self):
  for change in [{'Vintage':'other'},{'Unit':'Terajoules'},{'Transaction':'national'}]:
   p,b,m=self.blend();m.update(change)
   with self.subTest(change=change),self.assertRaises(ValueError):reconcile(p,b,m)
 def original(self):return dict(AssetID='fixture-existing',OriginalCapacity=10.,AssetClass='OBSERVED_EXISTING',CommissioningYear=2020,CommissioningEvidenceVerified=True,RetirementYear=2060,RetirementEvidenceVerified=True)
 def test_surviving_and_retired_strict_boundary(self):
  self.assertEqual(select_asset(self.original())['RetainedCapacity2050'],10)
  r=self.original();r['RetirementYear']=2050;self.assertEqual(select_asset(r)['RetainedCapacity2050'],0)
 def test_unknown_not_zero_or_infinite(self):
  r=self.original();r['CommissioningEvidenceVerified']=False;z=select_asset(r);self.assertIsNone(z['RetainedCapacity2050']);self.assertEqual(z['OriginalCapacity'],10)
 def test_planned_and_optimised_not_inherited(self):
  for k in ['COMMITTED_OR_PLANNED','MODEL_OPTIMISED_ADDITION','UNKNOWN']:
   r=self.original();r['AssetClass']=k;self.assertIsNone(select_asset(r)['RetainedCapacity2050'])
 def test_resource_limit_semantics(self):
  self.assertEqual(remaining_resource(100,10,'TOTAL_CAPACITY'),90);self.assertEqual(remaining_resource(100,10,'ADDITIONAL_POTENTIAL'),100)
  with self.assertRaises(ValueError):remaining_resource(5,10,'TOTAL_CAPACITY')
 def test_2050_not_weather_year(self):self.assertEqual(select_asset(self.original(),2050)['SurvivalStatus'],'SURVIVES_2050')

class RoundtripTests(unittest.TestCase):
 def setup_network(self):
  n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01','2013-12-31 21:00',freq='3h'));n.snapshot_weightings.loc[:,:]=3.
  for c in ['AC','H2','Biodiesel','biomass final energy']:n.add('Carrier',c,co2_emissions=0)
  n.add('Bus','SG test',carrier='AC');n.buses.loc['SG test','country']='SG'
  n.meta=dict(purpose='SYNTHETIC_TEST_ONLY',synthetic_geographical_nodes=1,solver_allowed=False,target_year=2050,approved_global_constraints=['test_grid_limit'],approved_coupling_paths=['electrolysis'],required_constraint_hooks=['install_fragment_constraints'])
  n.add('GlobalConstraint','test_grid_limit',type='transmission_volume_expansion_limit',constant=100)
  sub=pypsa.Network();sub.set_snapshots(n.snapshots);sub.snapshot_weightings=n.snapshot_weightings.copy()
  for c in ['AC','H2','Biodiesel','biomass final energy']:sub.add('Carrier',c,co2_emissions=0)
  for b,c in [('SG test','AC'),('SG H2','H2'),('SG BD','Biodiesel'),('SG bio final','biomass final energy')]:sub.add('Bus',b,carrier=c);sub.buses.loc[b,'country']='SG'
  sub.add('Generator','test electric supply',bus='SG test',carrier='AC',p_nom=3,p_max_pu=np.linspace(.3,.9,2920))
  sub.add('Link','test electrolysis',bus0='SG test',bus1='SG H2',carrier='H2 Electrolysis',efficiency=.7,p_nom_extendable=True)
  sub.add('Store','test BD resource',bus='SG BD',carrier='Biodiesel',e_nom=2,e_initial=2,e_cyclic=False)
  sub.add('Link','test BD meter',bus0='SG BD',bus1='SG bio final',efficiency=1,p_nom_extendable=True)
  sub.meta=dict(solver_allowed=False,store_power_rules={'test BD resource':'discharge_only'},external_annual_caps={'test electric supply':5000.})
  merge_input_components(n,sub)
  records=[dict(InputID='test-electric',Year=2050,Kind='DEMAND',Classification='REQUIRED_PHYSICAL',Value='1',Country='SG',Carrier='electricity',Account='Astar'),dict(InputID='test-bio',Year=2050,Kind='DEMAND',Classification='REQUIRED_PHYSICAL',Value='2',Country='SG',Carrier='biomass',Account='RoadResidualFuel')]
  manifest={'records':[dict(InputID=r['InputID'],Nodes=['SG test'],ArrayKey=r['InputID']) for r in records]};arrays={r['InputID']:np.full((2920,1),float(r['Value'])/8760) for r in records}
  dest={'test-electric@SG test':dict(bus='SG test',carrier='electricity',source_carrier='electricity',account='Astar',sector='Astar'),'test-bio@SG test':dict(bus='SG bio final',carrier='biomass',source_carrier='biomass',account='RoadResidualFuel',sector='Transport')}
  bind_loads(n,records,manifest,arrays,dest);n.meta['biomass_obligation_routes']={'test BD resource':dict(buses=['SG bio final'],annual_cap_mwh=2.,commodity='Biodiesel')}
  return n,records,manifest,arrays,dest
 def test_successful_export_roundtrip(self):
  n,r,*_=self.setup_network();before=static_validate(n,r,None,[],synthetic_test_only=True)
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'SYNTHETIC_TEST_ONLY.nc';n.export_to_netcdf(p);again=pypsa.Network(p)
   after=static_validate(again,r,None,[],synthetic_test_only=True)
   self.assertEqual(before,after);self.assertEqual(n.meta,again.meta)
   np.testing.assert_array_equal(n.generators_t.p_max_pu.values,again.generators_t.p_max_pu.values)
   self.assertEqual(again.loads.loc['test-bio@SG test','account'],'RoadResidualFuel')
   self.assertEqual(again.stores.at['test BD resource','e_nom'],2.)
   report=dict(purpose='SYNTHETIC_TEST_ONLY',status='EXPORT_READBACK_PASS',actual_network_validation=after,loads=len(again.loads),dynamic_input_roundtrip=True,metadata_and_hook_roundtrip=True,solver_runs=0,production_network_claim=False)
   output=ROOT/'results_project/assembly_v1_tests';output.mkdir(parents=True,exist_ok=True);(output/'EXPORT_ROUNDTRIP_TEST_RECEIPT.json').write_text(json.dumps(report,indent=2)+'\n')
 def test_no_unapproved_required_SMR(self):
  n,r,*_=self.setup_network();self.assertEqual(static_validate(n,r,None,[],synthetic_test_only=True)['actual_coupling_paths'],['electrolysis'])
  n.meta['approved_coupling_paths'].append('FT')
  with self.assertRaisesRegex(ValueError,'approved actual'):static_validate(n,r,None,[],synthetic_test_only=True)
 def test_valid_system_constraint_and_policy_rejection(self):
  n,*_=self.setup_network();self.assertTrue(check_global_constraints(n));n.add('GlobalConstraint','CO2Limit',type='primary_energy',carrier_attribute='co2_emissions',constant=100);n.meta['approved_global_constraints'].append('CO2Limit')
  with self.assertRaisesRegex(ValueError,'carbon policy'):check_global_constraints(n)
 def test_destination_mismatch(self):
  n,r,m,a,d=self.setup_network();d['test-bio@SG test']['source_carrier']='oil'
  n.mremove('Load',n.loads.index)
  with self.assertRaisesRegex(ValueError,'incompatible'):bind_loads(n,r,m,a,d)
 def test_biomass_diversion_fails(self):
  n,r,*_=self.setup_network();n.add('Link','bad diversion',bus0='SG BD',bus1='SG test',efficiency=.3,p_nom_extendable=True)
  with self.assertRaisesRegex(ValueError,'diversion'):static_validate(n,r,None,[],synthetic_test_only=True)
 def test_biomass_extra_resource_fails(self):
  n,r,*_=self.setup_network();n.stores.loc['test BD resource','e_nom']=3
  with self.assertRaisesRegex(ValueError,'cap differs'):static_validate(n,r,None,[],synthetic_test_only=True)
 def test_hidden_biomass_supply_fails(self):
  n,r,*_=self.setup_network();n.add('Generator','extra bio',bus='SG BD',carrier='Biodiesel',p_nom_extendable=True)
  with self.assertRaisesRegex(ValueError,'Extra biomass'):static_validate(n,r,None,[],synthetic_test_only=True)
 def test_production_does_not_accept_synthetic_node_contract(self):
  n,r,*_=self.setup_network()
  with self.assertRaisesRegex(ValueError,'bus count'):static_validate(n,r,None,[])
 def test_metadata_hook_loss_fails(self):
  n,r,*_=self.setup_network();n.meta['required_constraint_hooks']=[]
  with self.assertRaisesRegex(ValueError,'hook'):static_validate(n,r,None,[],synthetic_test_only=True)
 def test_actual_carbon_port_and_ownership(self):
  n,r,*_=self.setup_network()
  for carrier in ['gas','co2 atmosphere','CCGT']:n.add('Carrier',carrier,co2_emissions=0.)
  n.add('Bus','SG gas',carrier='gas');n.buses.loc['SG gas','country']='SG'
  n.add('Bus','test atmosphere',carrier='co2 atmosphere');n.buses.loc['test atmosphere','country']=''
  n.add('Link','test power',bus0='SG gas',bus1='SG test',bus2='test atmosphere',carrier='CCGT',efficiency=.5,efficiency2=.2,p_nom_extendable=True)
  m=[dict(component_type='Link',component='test power',carrier='CCGT',sector='Power',country='SG',coefficient=.2,policy_weight=1.,source='SYNTHETIC_TEST_ONLY',accepted=True)]
  self.assertEqual(static_validate(n,r,None,m,synthetic_test_only=True)['carbon_components'],1)
  for patch in [dict(coefficient=.3),dict(country='ID')]:
   bad=[dict(m[0],**patch)]
   with self.subTest(patch=patch),self.assertRaises(ValueError):static_validate(n,r,None,bad,synthetic_test_only=True)
if __name__=='__main__':unittest.main(verbosity=2)
