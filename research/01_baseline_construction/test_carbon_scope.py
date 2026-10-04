"""One-snapshot accounting fixture, never a scientific system experiment."""
from engineering_review import *
import pypsa

def fixture(nonpower):
    n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=1,freq='h'))
    for c,e in [('gas',0),('AC',0),('heat',0),('co2',-1)]:n.add('Carrier',c,co2_emissions=e)
    for b,c in [('gas','gas'),('power','AC'),('heat','heat'),('co2 atmosphere','co2')]:n.add('Bus',b,carrier=c)
    n.add('Generator','fuel',bus='gas',p_nom=100, marginal_cost=1)
    n.add('Link','power combustion',bus0='gas',bus1='power',bus2='co2 atmosphere',efficiency=.5,efficiency2=.2,p_nom=100,carrier='gas')
    n.add('Load','power demand',bus='power',p_set=1.)
    if nonpower:
        n.add('Link','nonpower combustion',bus0='gas',bus1='heat',bus2='co2 atmosphere',efficiency=.8,efficiency2=.2,p_nom=100,carrier='gas')
        n.add('Load','heat demand',bus='heat',p_set=1.)
    n.add('Store','co2 atmosphere',bus='co2 atmosphere',carrier='co2',e_nom=100,e_min_pu=-1,e_cyclic=False)
    n.add('GlobalConstraint','CO2Limit',carrier_attribute='co2_emissions',sense='<=',constant=100.)
    status,condition=n.optimize(solver_name='highs',log_to_console=False)
    assert status=='ok' and condition=='optimal'
    value=float(n.stores_t.e.at[n.snapshots[-1],'co2 atmosphere'])
    return {'solver_status':status,'termination':condition,'co2_atmosphere_t':value,'dispatch':n.links_t.p0.iloc[0].to_dict(),
     'constraint':str(n.model.constraints['GlobalConstraint-CO2Limit'])}

if __name__=='__main__':
    out={'kind':'SYNTHETIC_UNIT_FIXTURE_NOT_ASEAN_EXPERIMENT','power_only':fixture(False),'with_nonpower':fixture(True)}
    assert np.isclose(out['power_only']['co2_atmosphere_t'],.4)
    assert np.isclose(out['with_nonpower']['co2_atmosphere_t'],.65)
    out['scope_expansion_verified']=True
    (HERE/'CARBON_SCOPE_TEST.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
