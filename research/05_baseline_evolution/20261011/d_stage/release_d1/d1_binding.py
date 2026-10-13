"""D-1 2920 V4 binding: identity/time re-binding only. Scientific formulas and thresholds stay in pinned V4."""
from pathlib import Path
import numpy as np
from c02_common import read,write,sha
from d1_model import family

def check_binding(b,parent,rows,cols,families):
    assert b['parent_V4_SHA256']==parent
    assert b['rows']==rows and b['columns']==cols
    assert set(b['constraint_families'])==set(families)
    assert b['snapshots']==b['expected_snapshots'] and b['annual_hours']==8760 and b['hours_per_snapshot']==3
    assert b['V4_formulas_changed'] is False and b['representation_error_deducted'] is False
    assert b['annual_resource_budget_multiplier']==1

def make_binding(root,out,record,expected_snapshots=2920):
    v=read(root/'V4_APPROVED.json');coverage=read(out/'D1_CONSTRAINT_COVERAGE.json')
    b={'binding_id':'GATE6_2920_V4_D1_V1','parent_V4_SHA256':sha(root/'V4_APPROVED.json'),
      'Scheme_A_manifest_SHA256':sha(root/'scheme_a/EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json'),
      'C01R_protocol_SHA256':None,'time_aggregation':'NONE',
      'network_SHA256':sha(out/'gate6_2920_scheme_a_unsolved.nc'),'LP_manifest_SHA256':sha(out/'lp/MATH_PROBLEM.json'),
      'labels_SHA256':sha(out/'mapping/LABELS.json'),'snapshots':record['snapshots'],'expected_snapshots':expected_snapshots,'hours_per_snapshot':3,'source_year':2013,'scientific_year':2050,'annual_hours':8760,
      'rows':record['rows'],'columns':record['columns'],'constraint_families':{r['family']:r['rows'] for r in coverage['families']},
      'V4_formulas_changed':False,'physical_absolute_floor':v['physical_absolute_floor_in_each_equation_native_unit'],
      'physical_relative_budget':v['physical_relative_budget'],'kkt_normalized_budget':v['kkt_normalized_budget'],
      'fixed_inventory':v['fixed_inventory'],'representation_error_deducted':False,'annual_resource_budget_multiplier':1,
      'source_Q_and_Load_binding':'SCHEME_A_2920_EXACT_GROUPS.json','result_vectors_available':False,
      'actual_scientific_acceptance':'NOT_RUN_NO_SOLUTION','native_C_API':'D5_REQUIRED','optimization_authorized':False}
    check_binding(b,sha(root/'V4_APPROVED.json'),record['rows'],record['columns'],v['constraint_blocks'])
    write(out/'GATE6_2920_V4_BINDING.json',b);return b

def synthetic_tests(root,out):
    """Exercise original V4 formulas on tiny manufactured arrays, never optimize."""
    from fixed_resource_acceptance import inventory,obligation
    from v4_algebra_extracted import complete_kkt
    out.mkdir(exist_ok=False);results=[];h=np.full(365,24.);p=np.full(365,1.);q=8760.;e=q-np.cumsum(p*h)
    assert inventory(p,e,q,h,approved=True)['passed'];results.append('normal_inventory_365')
    bad=e.copy();bad[100]-=.1;assert not inventory(p,bad,q,h,approved=True)['passed'];results.append('inventory_violation_rejected')
    bad=p.copy();bad[100]+=.1;assert not obligation(bad,p,h,[q])['passed'];results.append('bus_delivery_violation_rejected')
    a={'start':np.array([0,1,2]),'index':np.array([0,0]),'value':np.array([1.,1.]),'cost':np.array([1.,0.]),
       'col_lower':np.array([0.,-np.inf]),'col_upper':np.array([np.inf,np.inf]),'row_lower':np.array([1.]),'row_upper':np.array([1.])}
    meta={'num_col':2,'num_row':1,'sense':1,'offset':-5.};z=np.array([0.,1.]);pi=np.array([0.]);rc=np.array([1.,0.]);D=np.ones(2);R=np.ones(1);v=read(root/'V4_APPROVED.json')
    k=complete_kkt(meta,a,z,pi,rc,D,R,out/'normal',v);assert k['independent_kkt_pass'];results.append('original_V4_KKT_normal_with_free_variable_and_offset')
    k=complete_kkt(meta,a,z,pi,np.array([1.,.01]),D,R,out/'bad_rc',v);assert not k['independent_kkt_pass'];results.append('free_RC_stationarity_sign_violation_rejected')
    k=complete_kkt(meta,a,np.array([.1,.9]),pi,rc,D,R,out/'bad_comp',v);assert not k['independent_kkt_pass'];results.append('complementarity_gap_rejected')
    try:complete_kkt(meta,a,z[:1],pi,rc,D,R,out/'bad_dim',v)
    except (ValueError,IndexError):results.append('vector_dimension_rejected')
    else:raise AssertionError('bad vector accepted')
    b={'parent_V4_SHA256':sha(root/'V4_APPROVED.json'),'rows':1,'columns':2,'constraint_families':{'known':1},'snapshots':365,'annual_hours':8760,'V4_formulas_changed':False,'representation_error_deducted':False,'annual_resource_budget_multiplier':1}
    for mod in [dict(columns=3),dict(constraint_families={'unknown':1}),dict(annual_resource_budget_multiplier=365)]:
        try:check_binding(dict(b,**mod),b['parent_V4_SHA256'],1,2,{'known'})
        except AssertionError:results.append('binding_reject_'+next(iter(mod)))
        else:raise AssertionError('bad binding accepted')
    result={'status':'SYNTHETIC_NO_SOLVE_PASS','checks':results,'real_daily_V4_pass':False,'model_builds':0,'solver_calls':0,'budget_unchanged':True}
    write(out/'SYNTHETIC_RECEIPT.json',result);return result
