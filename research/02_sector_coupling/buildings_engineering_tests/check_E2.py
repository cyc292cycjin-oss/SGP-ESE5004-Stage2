"""Isolated frozen-function tests on labelled synthetic fixtures; NO optimizer.
Usage: python check_candidate_fixes.py --repo PATH --fix E1|E2|E4 --output JSON
Exit 1 is expected on the frozen baseline, and required before each candidate patch.
"""
from pathlib import Path
from types import SimpleNamespace as NS
from itertools import product
import argparse, ast, json, logging, warnings
import numpy as np
import pandas as pd
import pypsa, pytz
warnings.filterwarnings('ignore',category=FutureWarning)

def load(path,names,env):
    tree=ast.parse(path.read_text());body=[]
    for x in tree.body:
        if isinstance(x,ast.FunctionDef) and x.name in names:body.append(x)
        if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in x.targets):body.append(x)
    exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),env)

def fixture(repo,r=6.,s=4.,potential=.3):
    env=dict(pd=pd,np=np,pypsa=pypsa,logger=logging.getLogger('audit'),get=lambda x,y:x)
    load(repo/'scripts/_helpers.py',['safe_divide'],env)
    load(repo/'scripts/prepare_sector_network.py',['normalize_by_country','p_set_from_scaling','add_residential','add_services','add_heat','create_nodes_for_heat_sector'],env)
    n=pypsa.Network(); n.set_snapshots(pd.date_range('2013-01-01',periods=2,freq='h'))
    n.snapshot_weightings.loc[:,:]=np.array([[2.],[3.]])
    for nm,c in [('SG0','AC'),('SG0 oil','oil'),('SG0 gas','gas'),('SG0 biomass','solid biomass'),('co2 atmosphere','co2')]:n.add('Bus',nm,carrier=c)
    n.buses['location']='SG0';n.buses['country']='SG'
    n.add('Load','SG0',bus='SG0',carrier='AC',p_set=[20e6/5]*2)
    heat=pd.DataFrame({(sec+' '+use,'SG0'):[q*share*1e6/5]*2 for sec,q in [('residential',r),('services',s)] for use,share in [('space',.6),('water',.4)]},index=n.snapshots)
    profiles={'heat':heat,'cop':pd.DataFrame({'SG0':[3.,3.]},index=n.snapshots),'solar':pd.DataFrame({'SG0':[0.,0.]},index=n.snapshots),'district':pd.DataFrame({'district heat share':[0.]},index=['SG0'])}
    costs=pd.DataFrame({'efficiency':[3.,3.,3.,1.,1.],'fixed':[10.,10.,10.,0.,0.],'lifetime':[20.,20.,20.,20.,20.],'CO2 intensity':[0.,0.,0.,.2,.2]},index=['decentral ground-sourced heat pump','decentral air-sourced heat pump','central air-sourced heat pump','oil','gas'])
    env.update(countries=['SG'],investment_year=2030,options={'district_heating':{'potential':potential,'progress':1.,'district_heating_loss':.15},'reduce_space_heat_exogenously':False,'time_dep_hp_cop':False,'tes':False,'boilers':False,'solar_thermal_collector':{'enable':False},'chp':False,'micro_chp':False},
      pop_layout=pd.DataFrame({'urban':[.6],'rural':[.4],'fraction':[1.],'ct':['SG']},index=['SG0']),
      read_csv_nafix=lambda name,**kw:profiles[name].copy(),
      spatial=NS(nodes=pd.Index(['SG0']),**{f:NS(nodes=pd.Index(['SG0 '+f])) for f in ['oil','gas','biomass']}))
    et=pd.DataFrame({'total residential space':[r*.6],'total residential water':[r*.4],'residential heat oil':[r*2/3],'residential heat gas':[0.],'residential heat biomass':[0.],'residential oil':[1.],'residential gas':[0.],'residential biomass':[0.],'electricity residential':[7.],'services electricity':[3.],'services oil':[0.],'services gas':[0.],'services biomass':[0.]},index=['SG'])
    return n,env,costs,et,profiles

def amounts(n):return n.loads_t.p_set.mul(n.snapshot_weightings.generators,axis=0).sum()/1e6

def test_e1(repo):
    results=[]
    for r,s,p in [(6.,4.,.3),(0.,4.,.3),(6.,0.,.3),(6.,4.,0.),(6.,4.,1.)]:
        n,env,costs,et,_=fixture(repo,r,s,p)
        env['add_heat'](n,costs,'heat','solar','cop','cop','district');before=amounts(n)
        heat_i=n.loads.index[n.loads.carrier.str.contains('heat')]
        assert np.isclose(before[heat_i].sum(),(r+s)*(1+.6*p*.15))
        service_i=heat_i[heat_i.str.contains('services')]
        service_before=n.loads_t.p_set[service_i].copy()
        env['add_residential'](n,costs,et);after=amounts(n)
        residential_i=heat_i[heat_i.str.contains('residential')]
        checks={
          'services_unchanged':np.allclose(n.loads_t.p_set[service_i],service_before),
          'services_allocation_conserved':np.isclose(after[service_i].sum(),s*(1+.6*p*.15)),
          'residential_remaining_plus_DH_loss_conserved':np.isclose(after[residential_i].sum(),r/3*(1+.6*p*.15)),
          'fixed_residential_fuel_unchanged':np.isclose(after['SG0 residential oil'],1+r*2/3),
          'direct_residential_unchanged':np.isclose(after['SG0'],7),
          'finite_nonnegative_heat':bool(np.isfinite(n.loads_t.p_set[heat_i]).all().all() and (n.loads_t.p_set[heat_i]>=0).all().all()),
          'distributed_heat_pumps_remain':int(n.links.index.str.contains('decentral|rural').sum())==4,
        }
        env['add_services'](n,costs,et)
        checks['services_direct_conserved']=np.isclose(amounts(n)['SG0 services electricity'],3.)
        results.append(dict(fixture=dict(R_TWh=r,S_TWh=s,potential=p,hours=[2,3]),checks={k:bool(v) for k,v in checks.items()},before=before.to_dict(),after=after.to_dict()))
    return results

def prepared(repo,annual,daily):
    env=dict(pd=pd,np=np,pypsa=pypsa,pytz=pytz,product=product)
    load(repo/'scripts/prepare_heat_data.py',['generate_periodic_profiles','prepare_heat_data','normalize_heat_profile'],env)
    n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=24,freq='h'))
    profiles=pd.DataFrame(1.,index=range(24),columns=[f'{s} {u} {d}' for s in ['residential','services'] for u in ['space','water'] for d in ['weekday','weekend']])
    totals=pd.DataFrame({f'{t} {s} {u}':[annual if u=='space' else 2.] for t in ['total','electricity'] for s in ['residential','services'] for u in ['space','water']},index=['SG']);totals['district heat share']=0.
    env.update(pop_layout=pd.DataFrame({'ct':['SG'],'fraction':[1.]},index=['SG0']),options={'solar_thermal_collector':{'cf_correction':1.}},
      snakemake=NS(input=NS(cop_air_total='cop',cop_soil_total='cop',solar_thermal_total='solar',energy_totals_name='totals',heat_demand_total='daily',heat_profile='profile')),
      read_csv_nafix=lambda name,**kw:totals.copy() if name=='totals' else profiles.copy(),
      xr=NS(open_dataarray=lambda name:NS(to_pandas=lambda:pd.DataFrame({'SG0':[daily if name=='daily' else 1.]*24},index=n.snapshots))))
    return env['prepare_heat_data'](n)[1]

def test_e2(repo):
    results=[]
    for annual,daily,raise_expected in [(6.,0.,True),(0.,0.,False),(6.,1.,False),(6.,float('nan'),True),(6.,-1.,True),(-1.,1.,True)]:
        try:
            h=prepared(repo,annual,daily)
            ok=not raise_expected and np.isfinite(h.values).all() and np.allclose(h['residential space'].sum().values,annual*1e6) and np.allclose(h['services water'].sum().values,2e6)
            detail=dict(space_TWh=h['residential space'].sum().iloc[0]/1e6,water_TWh=h['services water'].sum().iloc[0]/1e6,finite=bool(np.isfinite(h.values).all()))
        except ValueError as e:ok=raise_expected;detail={'raised':str(e)}
        results.append(dict(fixture=f'annual={annual},daily={daily}',checks={'fail_or_conserve_as_required':bool(ok)},detail=detail))
    n,env,costs,et,p=fixture(repo);p['heat'].iloc[0,0]=np.nan
    try:env['add_heat'](n,costs,'heat','solar','cop','cop','district');ok=False;detail='invalid imported profile silently accepted'
    except ValueError as e:ok=True;detail=str(e)
    results.append(dict(fixture='invalid imported CSV profile',checks={'consumer_rejects_nan':ok},detail=detail))
    return results

def test_e4(repo):
    n,env,_,_,_=fixture(repo)
    n.add('Link','synthetic retained DC link',bus0='SG0',bus1='SG0',carrier='DC',p_nom=0.)
    n.add('Load','SG0 services electricity',bus='SG0',carrier='services electricity',p_set=[3e6/5]*2)
    load(repo/'scripts/final_asean_adjustment.py',['strip_network','carrier_to_keep'],env)
    after=env['strip_network'](n,env['carrier_to_keep']);a=amounts(after)
    return [dict(fixture='power-only filter; no recalibration',checks={'service_load_retained':'SG0 services electricity' in after.loads.index,'direct_electricity_conserved':bool(np.isclose(a.sum(),23.))},before=amounts(n).to_dict(),after=a.to_dict())]

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--fix',choices=['E1','E2','E4'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    tests={'E1':test_e1,'E2':test_e2,'E4':test_e4}[a.fix](a.repo)
    ok=all(all(x['checks'].values()) for x in tests)
    result=dict(fix=a.fix,synthetic_only=True,optimizer_called=False,tests=tests,all_pass=ok,pypsa=pypsa.__version__,pandas=pd.__version__)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({'fix':a.fix,'all_pass':ok,'cases':len(tests)}));raise SystemExit(0 if ok else 1)
