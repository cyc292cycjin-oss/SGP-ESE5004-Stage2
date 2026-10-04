"""Synthetic topology/physical-carbon tests; no solver or dispatch calculation."""
from pathlib import Path
import sys,unittest,copy,math
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts_project'))
import carrier_architecture as c
import carbon_architecture as k


def assumption(price=10):
    return dict(price=price,price_unit='EUR/MWh_fuel',source_sha256='SYNTHETIC_TEST_ONLY',source_year=2019,basis='LHV',capacity_mw=10,annual_cap_mwh=100,unlimited_annual_accepted=False)


class CarrierTests(unittest.TestCase):
    def setUp(self):self.f=c.local_blueprint({'SG0':'SG','MY0':'MY'})
    def test_all_11_country_pairs_potential(self):
        f=c.local_blueprint({x+'0':x for x in sorted(c.COUNTRIES)})
        self.assertEqual(c.reachability(f),[]);self.assertTrue(c.validate(f))
        self.assertGreater(len(c.graph(f)),11) # checks pending paths too, not an empty graph
    def test_no_shared_physical_bus(self):
        with self.assertRaises(ValueError):self.f.bus('global gas','gas','',None)
    def test_crossborder_h2_rejected(self):
        with self.assertRaises(ValueError):self.f.add('Link','pipe','SG','H2',inputs=[c.bus_name('SG0','H2')],outputs=[c.bus_name('MY0','H2')])
    def test_crossborder_gas_co2_biomass_ft_rejected(self):
        for carrier in ['gas','co2 captured','solid biomass','oil','lignite','coal']:
            with self.subTest(carrier=carrier),self.assertRaises(ValueError):self.f.add('Link','bad','SG',carrier,inputs=[c.bus_name('SG0',carrier)],outputs=[c.bus_name('MY0',carrier)])
    def test_graph_mutation_detected(self):
        r=self.f.components['Link:SG0 FT'];r['outputs']=[c.bus_name('MY0','oil')]
        self.assertTrue(c.reachability(self.f))
        with self.assertRaises(ValueError):c.validate(self.f)
    def test_shared_pool_mutation_detected(self):
        self.f.buses['bad']={'name':'bad','carrier':'gas','country':'','node':None,'role':'PHYSICAL'}
        with self.assertRaises(ValueError):c.validate(self.f)
    def test_common_price_separate_imports(self):
        for node in ['SG0','MY0']:c.external_import(self.f,node,'gas','common-price',assumption(),accepted=True)
        self.assertEqual(len(self.f.markets),1);self.assertFalse(any('market' in x for x in self.f.buses));self.assertEqual(c.reachability(self.f),[])
    def test_same_market_different_price_rejected(self):
        c.external_import(self.f,'SG0','gas','same',assumption(),accepted=True)
        with self.assertRaises(ValueError):c.external_import(self.f,'MY0','gas','same',assumption(20),accepted=True)
    def test_import_unaccepted_rejected(self):
        with self.assertRaises(ValueError):c.external_import(self.f,'SG0','gas','market',assumption(),accepted=False)
    def test_new_h2_import_rejected(self):
        with self.assertRaises(ValueError):c.external_import(self.f,'SG0','H2','market',assumption(),accepted=True)
    def test_missing_availability_rejected(self):
        a=assumption();a['annual_cap_mwh']=None
        with self.assertRaises(ValueError):c.external_import(self.f,'SG0','gas','market',a,accepted=True)
    def test_negative_import_price_rejected(self):
        with self.assertRaises(ValueError):c.external_import(self.f,'SG0','gas','market',assumption(-1),accepted=True)
    def test_resource_allocation_conserves(self):
        c.allocate_finite_resource(self.f,'solid biomass',100,{'SG0':30,'MY0':70},accepted=True,source='SYNTHETIC',fuel_cost=3)
        stores=[x for x in self.f.components.values() if x['role']=='FINITE_RESOURCE']
        self.assertEqual(sum(x['params']['e_initial'] for x in stores),100);self.assertEqual(c.reachability(self.f),[])
    def test_resource_not_replicated(self):
        with self.assertRaises(ValueError):c.allocate_finite_resource(self.f,'solid biomass',100,{'SG0':100,'MY0':100},accepted=True,source='SYNTHETIC',fuel_cost=3)
    def test_resource_unaccepted_rejected(self):
        with self.assertRaises(ValueError):c.allocate_finite_resource(self.f,'solid biomass',100,{'SG0':100},accepted=False,source='SYNTHETIC',fuel_cost=3)
    def test_co2_local_geology_not_feedstock(self):
        c.carbon_storage(self.f,'SG0',100,accepted=True,source='SYNTHETIC',storage_cost=2)
        self.assertTrue(c.validate(self.f));self.assertEqual(c.reachability(self.f),[])
        self.f.add('Link','withdraw','SG','CO2',inputs=[c.bus_name('SG0','co2 sequestered')],outputs=[c.bus_name('SG0','co2 captured')])
        with self.assertRaises(ValueError):c.validate(self.f)
    def test_geology_missing_resource_rejected(self):
        with self.assertRaises(ValueError):c.carbon_storage(self.f,'SG0',100,accepted=False,source='SYNTHETIC',storage_cost=2)
    def test_demands_not_added_by_carrier(self):
        with self.assertRaises(ValueError):self.f.add('Load','bad','SG','gas',inputs=[c.bus_name('SG0','gas')])
    def test_h2_is_node_local(self):
        f=c.local_blueprint({'SG0':'SG','SG1':'SG'});self.assertNotEqual(c.bus_name('SG0','H2'),c.bus_name('SG1','H2'))
        self.assertFalse(any('pipeline' in r['carrier'].lower() for r in f.components.values()))
    def test_no_new_dac_ammonia_methanol_heat(self):
        self.assertFalse(any(r['carrier'] in ['DAC','NH3','methanol','heat'] for r in self.f.components.values()))


def event(sector='Power',value=1,identity='x'):
    return dict(EventID=identity,CarbonBatchID=identity,Stage='combustion',Country='SG',Sector=sector,Origin='FOSSIL',
                AtmosphereDelta=value,PolicyWeight=1 if sector=='Power' else 0,Accepted=True)


class CarbonTests(unittest.TestCase):
    def test_power_plus_one(self):
        r=k.views([event()]);self.assertEqual(r['PolicyCO2_Power'],1);self.assertEqual(r['ReportingCO2_FullSystem'],1)
    def test_road_plus_one(self):
        r=k.views([event('Transport')]);self.assertEqual(r['PolicyCO2_Power'],0);self.assertEqual(r['ReportingCO2_FullSystem'],1)
    def nonpower_plus_one(self,sector):
        r=k.views([event(sector)]);self.assertEqual(r['PolicyCO2_Power'],0);self.assertEqual(r['ReportingCO2_FullSystem'],1)
    def test_buildings_plus_one(self):self.nonpower_plus_one('Buildings')
    def test_industry_plus_one(self):self.nonpower_plus_one('Industry')
    def test_agriculture_plus_one(self):self.nonpower_plus_one('Agriculture')
    def test_bunkers_separate(self):
        sectors=['DomesticShipping','InternationalShipping','DomesticAviation','InternationalAviation']
        r=k.views([event(x,1,x) for x in sectors]);self.assertEqual(r['PolicyCO2_Power'],0);self.assertEqual(len(r['ByCountrySector']),4);self.assertEqual(r['ReportingCO2_FullSystem'],4)
    def test_nonpower_not_scope_by_connection(self):
        with self.assertRaises(ValueError):k.classify_record('industrial electricity-connected boiler','gas','Industry','SG',.2,source='test',policy_weight=1,accepted=True)
    def test_shared_scope_unaccepted_rejected(self):
        with self.assertRaises(ValueError):k.classify_record('SMR','gas','Power','SG',.2,source='test',accepted=False)
    def test_shared_allocation_explicit_only(self):
        e=event();split=k.allocate_shared_event(e,{'Power':.3,'Industry':.7},accepted=True)
        r=k.views(split);self.assertEqual(r['PolicyCO2_Power'],.3);self.assertEqual(r['ReportingCO2_FullSystem'],1)
        with self.assertRaises(ValueError):k.allocate_shared_event(e,{'Power':.3,'Industry':.7},accepted=False)
        with self.assertRaises(ValueError):k.views([e]+split)
    def test_shared_allocation_conserves(self):
        with self.assertRaises(ValueError):k.allocate_shared_event(event(),{'Power':.5,'Industry':.6},accepted=True)
    def test_shared_allocation_cannot_hide_transfer_credit(self):
        e=dict(event(),Stage='geological_storage',AtmosphereDelta=-1)
        with self.assertRaises(ValueError):k.allocate_shared_event(e,{'Power':.5,'Industry':.5},accepted=True)
    def test_allocated_event_cannot_be_split_again(self):
        child=k.allocate_shared_event(event(),{'Power':.5,'Industry':.5},accepted=True)[0]
        with self.assertRaises(ValueError):k.allocate_shared_event(child,{'Power':1},accepted=True)
    def test_geothermal_not_omitted(self):
        r=k.classify_record('geothermal','geothermal','Power','SG',.1,source='test',accepted=True)
        self.assertTrue(r['PolicyCO2Power'])
    def test_duplicate_carbon_event(self):
        e=event()
        with self.assertRaises(ValueError):k.views([e,e])
    def test_duplicate_carbon_stage(self):
        e=event();other=dict(e,EventID='different')
        with self.assertRaises(ValueError):k.views([e,other])
    def test_storage_not_second_credit(self):
        e=event();e.update(Stage='geological_storage',AtmosphereDelta=-1)
        with self.assertRaises(ValueError):k.views([e])
    def test_capture_store_once(self):
        events,proof=k.carbon_batch('b','SG','FOSSIL',1,captured=.6,stored=.6,recycled=0,remaining=0,release_sector='Transport',accepted=True)
        self.assertAlmostEqual(k.views(events)['ReportingCO2_FullSystem'],.4)
    def test_recycled_co2_not_neutral(self):
        events,proof=k.carbon_batch('b','SG','RECYCLED_POINT_SOURCE',1,captured=.6,stored=0,recycled=.6,remaining=0,release_sector='Transport',accepted=True)
        r=k.views(events);self.assertAlmostEqual(r['ReportingCO2_FullSystem'],1);self.assertAlmostEqual(r['PolicyCO2_Power'],.4)
    def test_dac_cycle_one_uptake_one_release(self):
        events,proof=k.carbon_batch('b','SG','DAC',1,captured=1,stored=0,recycled=1,remaining=0,release_sector='Transport',producer_sector='Other',policy_weight=0,accepted=True)
        self.assertEqual(k.views(events)['ReportingCO2_FullSystem'],0);self.assertEqual(k.views(events)['PolicyCO2_Power'],0)
    def test_biogenic_no_invented_uptake(self):
        events,proof=k.carbon_batch('b','SG','BIOGENIC',1,captured=0,stored=0,recycled=0,remaining=0,release_sector='Transport',accepted=True)
        self.assertEqual(k.views(events)['ReportingCO2_FullSystem'],1)
    def test_capture_balance_fail(self):
        with self.assertRaises(ValueError):k.carbon_batch('b','SG','FOSSIL',1,captured=.5,stored=.5,recycled=.5,remaining=0,release_sector='Transport',accepted=True)
    def test_missing_origin_no_credit(self):
        with self.assertRaises(ValueError):k.carbon_batch('b','SG','MIXED_UNRESOLVED',1,captured=1,stored=1,recycled=0,remaining=0,release_sector='Transport',accepted=True)
    def test_budget_all_six_years(self):self.assertEqual([k.budget(y,8760)/1e6 for y in k.TRAJECTORY],[1000,820,640,460,280,100])
    def test_budget_time_scale(self):self.assertAlmostEqual(k.budget(2030,4380),410e6)
    def test_unknown_year_rejected(self):
        with self.assertRaises(ValueError):k.budget(2031,8760)
    def test_no_baseline_budget_activation(self):self.assertFalse(k.install_power_policy(None,[],2030,enabled=False,scope_complete=False,expected_hours=8760)['constraint_created'])


class PyPSAFragmentTests(unittest.TestCase):
    def setUp(self):self.f=c.local_blueprint({'SG0':'SG','MY0':'MY'})
    def test_unaccepted_fragment_rejected(self):
        with self.assertRaises(ValueError):c.to_pypsa_fragment(self.f,['t0'],[8760],component_ids=['Link:SG0 FT'])
    def test_distinct_external_generators_and_no_loads(self):
        keys=[c.external_import(self.f,n,'gas','same',assumption(),accepted=True) for n in ['SG0','MY0']]
        net=c.to_pypsa_fragment(self.f,['t0'],[8760],component_ids=keys)
        self.assertEqual(len(net.generators),2);self.assertTrue(net.loads.empty);self.assertEqual(set(net.buses.country),{'SG','MY'})
        self.assertTrue((net.generators.p_min_pu==0).all());self.assertEqual(net.generators.marginal_cost.tolist(),[10,10])
    def test_geological_store_cannot_discharge(self):
        c.carbon_storage(self.f,'SG0',100,accepted=True,source='SYNTHETIC',storage_cost=2)
        keys=[key for key,r in self.f.components.items() if r['role']=='PERMANENT_STORAGE']
        net=c.to_pypsa_fragment(self.f,['t0'],[8760],component_ids=keys)
        self.assertEqual(net.meta['store_power_rules']['SG0 geological inventory'],'charge_only');self.assertFalse(net.stores.e_cyclic.iloc[0]);self.assertEqual(net.stores.capital_cost.iloc[0],2)
        self.assertTrue(net.stores.e_nom_extendable.iloc[0]);self.assertEqual(net.stores.e_nom_max.iloc[0],100);self.assertEqual(net.stores.e_nom.iloc[0],0)
        import linopy
        net.model=linopy.Model();net.model.add_variables(coords=[net.snapshots,pd.Index(net.stores.index,name='Store')],name='Store-p')
        c.add_storage_direction_constraints(net)
        self.assertTrue((net.model.constraints['ResearchStoreDirection-SG0 geological inventory'].sign.values=='<=').all())
    def test_ft_multiinput_physical_signs(self):
        r=self.f.components['Link:SG0 FT'];r.update(accepted=True,source='SYNTHETIC',params=dict(
            bus_order=[c.bus_name('SG0',x) for x in ['H2','oil','co2 captured','electricity']],
            efficiency=.5,efficiency2=-.1,efficiency3=-.2,p_nom=1.,p_min_pu=0.))
        net=c.to_pypsa_fragment(self.f,['t0'],[8760],component_ids=['Link:SG0 FT'])
        self.assertLess(net.links.efficiency2.iloc[0],0);self.assertLess(net.links.efficiency3.iloc[0],0);self.assertTrue(net.loads.empty)
    def test_ft_wrong_co2_sign_rejected(self):
        r=self.f.components['Link:SG0 FT'];r.update(accepted=True,params=dict(bus_order=[c.bus_name('SG0',x) for x in ['H2','oil','co2 captured','electricity']],efficiency=.5,efficiency2=.1,efficiency3=-.2))
        with self.assertRaises(ValueError):c.to_pypsa_fragment(self.f,['t0'],[8760],component_ids=['Link:SG0 FT'])
    def test_conversion_reverse_flow_rejected(self):
        r=self.f.components['Link:SG0 electrolysis'];r.update(accepted=True,source='SYNTHETIC',params=dict(efficiency=.7,p_min_pu=-1))
        with self.assertRaises(ValueError):c.to_pypsa_fragment(self.f,['t0'],[8760],component_ids=['Link:SG0 electrolysis'])
    def test_atmosphere_is_reporting_not_cap_or_feedstock(self):
        r=self.f.components['Link:SG0 SMR'];r.update(accepted=True,source='SYNTHETIC',params=dict(
            bus_order=[c.bus_name('SG0','gas'),c.bus_name('SG0','H2'),'ReportingCO2 atmosphere'],efficiency=.7,efficiency2=.2,p_nom=1.))
        n=c.to_pypsa_fragment(self.f,['t0'],[8760],component_ids=['Link:SG0 SMR'])
        self.assertEqual(n.carriers.at['co2 atmosphere','co2_emissions'],0)
        self.assertEqual(n.meta['atmosphere_role'],'ALLOWED_ACCOUNTING_GLOBAL');self.assertIn('ReportingCO2 atmosphere inventory',n.stores.index)
        self.assertTrue(n.global_constraints.empty)
    def test_industrial_coal_energy_and_carbon_same_flow(self):
        key=c.combustion_accounting_interface(self.f,'SG0','coal','Industry',.3,accepted=True,source='SYNTHETIC')
        n=c.to_pypsa_fragment(self.f,['t0'],[8760],component_ids=[key]);link=n.links.iloc[0]
        self.assertEqual(link.bus0,c.bus_name('SG0','coal'));self.assertEqual(link.efficiency,1)
        self.assertEqual(link.efficiency2,.3);self.assertTrue(n.loads.empty)
    def test_missing_fuel_factor_does_not_create_carbon_meter(self):
        with self.assertRaises(ValueError):c.combustion_accounting_interface(self.f,'SG0','coal','Industry',None,accepted=False,source='')
    def policy_network(self):
        import pypsa,linopy,xarray as xr
        n=pypsa.Network();n.set_snapshots(pd.Index(['t0','t1'],name='snapshot'))
        n.snapshot_weightings.loc[:,:]=4380.
        # Construct variables directly, without any solve or dispatch.
        n.model=linopy.Model();n.model.add_variables(lower=0,coords=[n.snapshots,pd.Index(['power','road'],name='Link')],name='Link-p')
        return n
    def test_real_linopy_constraint_only_power_terms(self):
        n=self.policy_network()
        terms=[dict(variable='Link-p',dimension='Link',component=x,sector='Power' if x=='power' else 'Transport',coefficient=1,policy_weight=1 if x=='power' else 0,accepted=True,source='SYNTHETIC') for x in ['power','road']]
        r=k.install_power_policy(n,terms,2030,enabled=True,scope_complete=True,expected_hours=8760)
        con=n.model.constraints['Research-PolicyCO2_Power']
        self.assertEqual(float(con.rhs),820e6);self.assertFalse(r['reporting_constraint_created'])
        ids=set(con.vars.values.flatten());power=set(n.model['Link-p'].labels.sel(Link='power').values.flatten());road=set(n.model['Link-p'].labels.sel(Link='road').values.flatten())
        self.assertTrue(power.issubset(ids));self.assertFalse(road&ids)
    def test_pending_scope_blocks_constraint(self):
        with self.assertRaises(ValueError):k.install_power_policy(self.policy_network(),[],2030,enabled=True,scope_complete=False,expected_hours=8760)
    def test_legacy_cap_coexistence_rejected(self):
        n=self.policy_network();n.add('GlobalConstraint','CO2Limit',type='primary_energy',constant=1)
        with self.assertRaises(ValueError):k.install_power_policy(n,[],2030,enabled=True,scope_complete=True,expected_hours=8760)
    def test_annual_import_availability_constraint(self):
        import linopy
        key=c.external_import(self.f,'SG0','gas','m',assumption(),accepted=True)
        n=c.to_pypsa_fragment(self.f,['t0'],[8760],component_ids=[key]);n.model=linopy.Model()
        n.model.add_variables(lower=0,coords=[n.snapshots,pd.Index(n.generators.index,name='Generator')],name='Generator-p')
        c.add_external_annual_caps(n);self.assertEqual(len(n.model.constraints),1)
        self.assertEqual(float(n.model.constraints['ResearchImportAnnual-SG0 external gas'].rhs),100)


if __name__=='__main__':unittest.main(verbosity=2)
