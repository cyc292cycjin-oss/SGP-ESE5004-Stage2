"""Synthetic accounting contract checks; NOT a PyPSA patch or input generator.

Reject deliberate account corruption using independent reference totals. All
numbers are artificial MWh/MW fixtures, never ASEAN empirical observations.
"""
from pathlib import Path
import json, math

HERE=Path(__file__).resolve().parent
ROWS=[]
ATOL=1e-10

def close(a,b):
    if not math.isfinite(a) or not math.isfinite(b) or abs(a-b)>ATOL:
        raise ValueError(f'Identity mismatch: {a} != {b}')

def verify(x):
    required=('A','O','R','S','hR','hS','B','C','direct','coolR','cookR','otherR',
              'coolS','cookS','otherS','weights')
    if any(k not in x or x[k] is None for k in required):raise ValueError('Missing account')
    n=len(x['weights'])
    if any(len(x[k])!=n for k in required):raise ValueError('Snapshot mismatch')
    for k in required:
        if any(v is None or not math.isfinite(v) or v<0 for v in x[k]):raise ValueError(k)
    if any(w<=0 for w in x['weights']):raise ValueError('Invalid physical weight')
    for t in range(n):
        close(x['A'][t],x['O'][t]+x['R'][t]+x['S'][t])
        close(x['R'][t],x['B'][t]+x['hR'][t])
        close(x['S'][t],x['C'][t]+x['hS'][t])
        close(x['B'][t],x['coolR'][t]+x['cookR'][t]+x['otherR'][t])
        close(x['C'][t],x['coolS'][t]+x['cookS'][t]+x['otherS'][t])
        close(x['direct'][t],x['O'][t]+x['B'][t]+x['C'][t])
        close(x['A'][t],x['direct'][t]+x['hR'][t]+x['hS'][t])
    close(sum(w*a for w,a in zip(x['weights'],x['A'])),
          sum(w*(d+r+s) for w,d,r,s in zip(x['weights'],x['direct'],x['hR'],x['hS'])))

def fixture():
    return dict(A=[100.,130.],O=[30.,40.],R=[40.,50.],S=[30.,40.],
                hR=[10.,15.],hS=[5.,10.],B=[30.,35.],C=[25.,30.],
                direct=[85.,105.],coolR=[10.,15.],cookR=[5.,5.],otherR=[15.,15.],
                coolS=[8.,10.],cookS=[2.,3.],otherS=[15.,17.],weights=[2.,3.])

def case(name,func,reject=False):
    raised=False;detail=''
    try:func()
    except ValueError as exc:raised=True;detail=str(exc)
    passed=raised==reject
    ROWS.append(dict(case=name,expected='REJECT' if reject else 'PASS',
                     actual='REJECT' if raised else 'PASS',passed=passed,detail=detail))
    assert passed,name

def mutated(key,values):
    x=fixture();x[key]=values;verify(x)

def fuel_contract(total,heating,cooking,other,unclassified):
    if any(v is None or not math.isfinite(v) or v<0 for v in [total,heating,cooking,other,unclassified]):
        raise ValueError('Missing/invalid fuel partition')
    close(total,heating+cooking+other+unclassified)

def useful_heat(F,share,performance,basis,performance_basis):
    if any(v is None for v in (F,share,performance,basis,performance_basis)):
        raise ValueError('Missing conversion evidence')
    if not 0<=share<=1 or F<0 or performance<=0:raise ValueError('Invalid conversion')
    if basis!=performance_basis:raise ValueError('Energy-basis mismatch')
    return F*share*performance

def main():
    case('snapshot_country_year_identity',lambda:verify(fixture()))
    case('historical_heat_subtracted_twice',lambda:mutated('direct',[70.,80.]),True)
    case('services_added_twice',lambda:mutated('direct',[110.,135.]),True)
    case('cooling_removed',lambda:mutated('direct',[67.,80.]),True)
    case('cooking_electric_removed',lambda:mutated('direct',[78.,97.]),True)
    case('endogenous_HP_input_preloaded',lambda:mutated('direct',[88.,109.]),True)
    case('missing_historical_electric_heat',lambda:mutated('hR',None),True)
    case('negative_residual',lambda:mutated('O',[-1.,40.]),True)
    # Weighted national integral is unchanged (+3*2-2*3=0); pointwise error must fail.
    case('annual_balance_hides_snapshot_error',lambda:mutated('direct',[88.,103.]),True)
    case('nonfinite_source',lambda:mutated('R',[float('nan'),50.]),True)
    case('cooking_fuel_preserved',lambda:fuel_contract(100.,30.,40.,20.,10.))
    case('cooking_fuel_deleted',lambda:fuel_contract(100.,30.,0.,20.,10.),True)
    case('unknown_enduse_not_zero',lambda:fuel_contract(100.,30.,40.,20.,None),True)
    case('useful_service_unit_identity',lambda:close(useful_heat(100.,.25,.8,'LHV','LHV'),20.))
    case('electric_HP_COP_allowed',lambda:close(useful_heat(100.,.25,3.,'electricity','electricity'),75.))
    case('missing_enduse_share_rejected',lambda:useful_heat(100.,None,.8,'LHV','LHV'),True)
    case('missing_efficiency_rejected',lambda:useful_heat(100.,.25,None,'LHV','LHV'),True)
    case('HHV_LHV_mismatch_rejected',lambda:useful_heat(100.,.25,.8,'HHV','LHV'),True)
    out=dict(synthetic_only=True,model_patch=False,model_inputs_written=0,solver_runs=0,
             rows=ROWS,all_pass=all(r['passed'] for r in ROWS))
    (HERE/'evidence/ACCOUNTING_CONTRACT_TESTS.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(dict(checks=len(ROWS),all_pass=out['all_pass'])))

if __name__=='__main__':main()
