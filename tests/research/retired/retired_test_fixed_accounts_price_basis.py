"""SYNTHETIC_TEST_ONLY. Qualification failures and official-source transformations.
No solver invocation; a small Linopy variable model tests the real direction hook.
"""
from pathlib import Path
import sys,unittest,copy,tempfile,json
import numpy as np,pandas as pd,pypsa,linopy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
from fixed_accounts import qualify_fixed_accounts,validate_exported_accounting,accounting_report
from price_basis import rebase,read_index,row_basis
from carrier_architecture import add_storage_direction_constraints

def fixture():
 n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=4,freq='3h'));n.snapshot_weightings.loc[:,:]=3.
 n.add('Carrier','Biodiesel');n.add('Bus','resource',carrier='Biodiesel');n.add('Bus','final',carrier='Biodiesel final energy');n.buses['country']='MY'
 n.add('Store','stock',bus='resource',carrier='Biodiesel',e_nom=12.,e_initial=12.,e_cyclic=False)
 n.add('Link','meter',bus0='resource',bus1='final',efficiency=1.,p_nom_extendable=True,p_min_pu=0.)
 n.add('Load','load',bus='final',p_set=1.);n.loads['source_account_id']='MY:road'
 n.meta=dict(purpose='SYNTHETIC_TEST_ONLY',required_constraint_hooks=['install_fragment_constraints'],store_power_rules={'stock':'discharge_only'},biomass_obligation_routes={'stock':dict(buses=['final'],commodity='Biodiesel',source_row='SYNTHETIC_TEST_ONLY',annual_cap_mwh=12.,input_id='MY:road')})
 return n

class FixedTests(unittest.TestCase):
 def test_null_cost_factor_and_quantity_preserved(self):
  n=fixture();r=qualify_fixed_accounts(n)[0];self.assertIsNone(r['UnitPriceEUR2020PerMWh']);self.assertIsNone(r['PhysicalCO2_tPerMWh']);self.assertEqual(r['QuantityMWh'],12.)
 def test_roundtrip_keeps_external_identity(self):
  n=fixture();qualify_fixed_accounts(n)
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'SYNTHETIC_TEST_ONLY.nc';n.export_to_netcdf(p);r=pypsa.Network(p);validate_exported_accounting(r);self.assertEqual(n.meta,r.meta)
 def test_report_cannot_claim_full(self):
  n=fixture();r=accounting_report(n);self.assertIsNone(r['PricedObjective']);self.assertFalse(r['FullSystemCostComplete']);self.assertFalse(r['FullSystemEmissionsComplete'])
  for k in ['claim_full_cost','claim_full_emissions']:
   with self.subTest(k=k),self.assertRaisesRegex(ValueError,'full system'):accounting_report(n,**{k:True})
 def test_free_supply_label_rejected(self):
  n=fixture();qualify_fixed_accounts(n);n.stores.loc['stock','cost_qualification']='FREE'
  with self.assertRaisesRegex(ValueError,'free supply'):validate_exported_accounting(n)
 def test_added_supplier_revokes(self):
  n=fixture();qualify_fixed_accounts(n);n.add('Generator','extra',bus='final',p_nom=2.)
  with self.assertRaisesRegex(ValueError,'Alternative'):qualify_fixed_accounts(n)
  self.assertEqual(n.meta['external_fixed_account_status'],'REVOKED_PENDING_CURRENT_VALIDATION');self.assertEqual(n.stores.at['stock','cost_qualification'],'REVOKED')
 def test_diversion_rejected(self):
  n=fixture();n.add('Bus','other');n.add('Link','divert',bus0='resource',bus1='other',p_nom=1.)
  with self.assertRaisesRegex(ValueError,'diversion'):qualify_fixed_accounts(n)
 def test_carbon_credit_port_rejected(self):
  n=fixture();n.add('Bus','co2');n.links.loc['meter','bus2']='co2';n.links.loc['meter','efficiency2']=-.1
  with self.assertRaisesRegex(ValueError,'carbon-credit'):qualify_fixed_accounts(n)
 def test_unknown_commodity_not_approved(self):
  n=fixture();n.meta['biomass_obligation_routes']['stock']['commodity']='Animal waste'
  with self.assertRaisesRegex(ValueError,'no accepted'):qualify_fixed_accounts(n)
 def test_quantities_do_not_close(self):
  n=fixture();n.loads.loc['load','p_set']=.5
  with self.assertRaisesRegex(ValueError,'strictly fixed'):qualify_fixed_accounts(n)
 def test_weights_change_rejected(self):
  n=fixture();n.snapshot_weightings.loc[:,'objective']=2.
  with self.assertRaisesRegex(ValueError,'weights'):qualify_fixed_accounts(n)
 def test_cyclic_loss_or_extendability_rejected(self):
  for k,v in [('e_cyclic',True),('e_nom_extendable',True),('standing_loss',.1),('e_initial',5.)]:
   n=fixture();n.stores.loc['stock',k]=v
   with self.subTest(k=k),self.assertRaisesRegex(ValueError,'boundary'):qualify_fixed_accounts(n)
 def test_time_price_change_rejected(self):
  n=fixture();n.stores_t.marginal_cost['stock']=[0,1,0,1]
  with self.assertRaisesRegex(ValueError,'Time-varying'):qualify_fixed_accounts(n)
 def test_hook_absence_rejected(self):
  n=fixture();n.meta['required_constraint_hooks']=[]
  with self.assertRaisesRegex(ValueError,'hook'):qualify_fixed_accounts(n)
 def test_real_direction_hook_attached_without_solver(self):
  n=fixture();qualify_fixed_accounts(n);n.model=linopy.Model();n.model.add_variables(coords=[n.snapshots,pd.Index(['stock'],name='Store')],name='Store-p');add_storage_direction_constraints(n)
  c=n.model.constraints['ResearchStoreDirection-stock'];self.assertTrue((c.sign.values=='>=').all());self.assertTrue((c.rhs.values==0).all())
 def test_two_sources_same_fixed_account_sum_once(self):
  n=fixture();n.stores.loc['stock',['e_nom','e_initial']]=6.;n.meta['biomass_obligation_routes']['stock']['annual_cap_mwh']=6.
  n.add('Bus','resource2',carrier='Biogasoline');n.buses.loc['resource2','country']='MY';n.add('Store','stock2',bus='resource2',carrier='Biogasoline',e_nom=6.,e_initial=6.);n.add('Link','meter2',bus0='resource2',bus1='final',p_nom_extendable=True,efficiency=1.)
  n.meta['store_power_rules']['stock2']='discharge_only';n.meta['biomass_obligation_routes']['stock2']=dict(buses=['final'],commodity='Biogasoline',annual_cap_mwh=6.,source_row='SYNTHETIC_TEST_ONLY2',input_id='MY:road')
  self.assertEqual(sum(r['QuantityMWh'] for r in qualify_fixed_accounts(n)),12.)

class PriceTests(unittest.TestCase):
 def test_actual_official_series_identity(self):
  d=read_index(ROOT/'research_inputs/prices/sources/ECB_EA20_GDP_DEFLATOR.csv');self.assertAlmostEqual(d[2020],100.);self.assertGreater(d[2023],d[2020])
 def test_unadjusted_value_rebased(self):
  value,factor=rebase(120.,2023,{2020:100.,2023:120.});self.assertEqual(value,100.);self.assertEqual(factor,100/120)
 def test_already_2020_not_adjusted_twice(self):
  self.assertEqual(rebase(120.,2015,{2020:100.,2015:80.},already_model_year=2020),(120.,1.))
 def test_unknown_price_year_rejected(self):
  for y in [None,float('nan'),0,2024]:
   with self.subTest(y=y),self.assertRaises(ValueError):rebase(5.,y,{2020:100.})
 def test_prior_currency_year_is_metadata_not_current_basis(self):
  r=pd.Series(dict(technology='gas',parameter='fuel',value=24.568,unit='EUR/MWh_th',source='frozen',currency_year=2010))
  pre=pd.DataFrame([r]).set_index(['technology','parameter']);self.assertEqual(row_basis(r,pre)[0],2020)
 def test_changed_source_cannot_borrow_prior_rebase(self):
  r=pd.Series(dict(technology='gas',parameter='fuel',value=1.,unit='EUR/MWh',source='a',currency_year=2010));pre=pd.DataFrame([r]).set_index(['technology','parameter']);r['value']=2.
  with self.assertRaisesRegex(ValueError,'prior transformation'):row_basis(r,pre)
 def test_unadjusted_parameter_excluded_by_upstream_filter(self):
  r=pd.Series(dict(technology='biomass boiler',parameter='pelletizing cost',value=1.,unit='EUR/MWh',source='a',currency_year=2019));pre=pd.DataFrame([r]).set_index(['technology','parameter']);self.assertEqual(row_basis(r,pre)[0],2019)
 def test_wrong_region_rejected(self):
  d=pd.read_csv(ROOT/'research_inputs/prices/sources/ECB_EA20_GDP_DEFLATOR.csv');d['REF_AREA']='I8'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'fixture.csv';d.to_csv(p,index=False)
   with self.assertRaisesRegex(ValueError,'definition'):read_index(p)
 def test_production_price_layer_derived_fom_and_nonmonetary_unchanged(self):
  p=ROOT/'results_project/assembly_v1/assets/model_cost_layer.json'
  if not p.exists():self.skipTest('Actual cost layer not yet generated')
  layer=json.loads(p.read_text())
  for r in layer['rows']:
   if r['Status']=='ALREADY_EUR2020_UNCHANGED':self.assertEqual(r['ModelValue'],r['PreparedValue'])
   if r['Parameter']=='FOM':self.assertEqual(r['ModelValue'],r['OriginalValue'])
   if r['Parameter']=='monetary_FOM':
    t=layer['tables'][str(r['TechnologyYear'])];d=pd.DataFrame(t['values'],index=t['index'],columns=t['columns'])
    self.assertAlmostEqual(r['ModelValue'],d.at[r['Technology'],'investment']*d.at[r['Technology'],'FOM']/100)
 def test_actual_ft_vom_uses_output_energy_basis(self):
  p=ROOT/'results_project/assembly_v1/assets/carrier_fragment.json'
  if not p.exists():self.skipTest('Production recipe not yet generated')
  raw=json.loads(p.read_text());layer=json.loads(p.with_name('model_cost_layer.json').read_text());r=next(r for r in layer['rows'] if r['TechnologyYear']==2050 and r['Technology']=='Fischer-Tropsch' and r['Parameter']=='VOM')
  components=[z for z in raw['components'].values() if z['carrier']=='Fischer-Tropsch'];self.assertEqual(len(components),100)
  for z in components:self.assertAlmostEqual(z['params']['marginal_cost'],r['ModelValue']*z['params']['efficiency'])

if __name__=='__main__':unittest.main(verbosity=2)
