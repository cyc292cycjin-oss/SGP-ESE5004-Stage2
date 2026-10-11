"""Independent bit-neighbour and rational check of design-only output files.
No model, matrix, network or solver access. Prints a receipt; never changes inputs.
Usage: python verification/verify_closure_design.py PATH_TO_ANALYSIS_OUTPUT
"""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,math,struct,sys

def neighbour(x,step):
    assert x>0 and math.isfinite(x)
    bits=struct.unpack('>Q',struct.pack('>d',x))[0]
    return struct.unpack('>d',struct.pack('>Q',bits+step))[0]

def verify(folder):
    folder=Path(folder)
    read=lambda p:json.loads((folder/p).read_text())
    original=read('ALL_385_GROUPS_CLOSURE_LEDGER.json')['groups']
    base={g['bus']:g for g in original}
    receipt=read('ANALYSIS_VALIDATION.json')
    for item in receipt['outputs']:
        b=(folder/item['path']).read_bytes()
        assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256']
    counts={}
    for opt in 'ABC':
        rows=read('OPTION_'+opt+'_SIMULATION.json')['groups']
        assert len(rows)==len(base)==385 and {r['bus'] for r in rows}==set(base)
        equal=0; max_prefix_stock_violation=F(0)
        for r in rows:
            old=base[r['bus']]
            oldq={a['asset']:F(float.fromhex(a['Q_mwh_hex'])) for a in old['accounts']}
            newq=dict(oldq)
            for a in r['account_differences']:
                assert F(float.fromhex(a['before_hex']))==oldq[a['asset']]
                newq[a['asset']]=F(float.fromhex(a['after_hex']))
                assert newq[a['asset']]-oldq[a['asset']]==F(a['delta_mwh']['exact'])
            d=F(float.fromhex(r['load_after_hex'])); D=8760*d; Q=sum(newq.values(),F(0))
            assert D<=Q and Q-D==F(r['remaining_inventory_sum_mwh']['exact'])
            assert all(v>0 for v in newq.values())
            equal+=D==Q
            if opt=='A':
                assert r['load_before_hex']==r['load_after_hex']
                changed=[a for a in newq if newq[a]!=oldq[a]]
                positive=F(old['D_minus_Q_mwh']['exact'])>0
                assert len(changed)==int(positive)
                if positive:
                    k=changed[0]
                    assert k==min(oldq,key=lambda a:(-oldq[a],a))
                    assert Q-newq[k]+F(neighbour(float(newq[k]),-1))<D
            if opt=='B':
                assert newq==oldq
                if F(old['D_minus_Q_mwh']['exact'])>0:
                    assert 8760*F(neighbour(float(d),1))>Q
            if opt=='C': assert D==Q
            # Exact analytic local witness, NOT an LP solve or global certificate:
            # p_i=Q_i*d/Q and e_i(t)=Q_i-3*(t+1)*p_i. Check endpoints and
            # monotonicity imply all intermediate stocks lie in [0,Q_i].
            power=[v*d/Q for v in newq.values()]
            assert sum(power,F(0))==d and all(p>=0 for p in power)
            for q,p in zip(newq.values(),power):
                e_first=q-3*p; e_last=q-8760*p
                assert 0<=e_last<=e_first<=q
                assert q-e_last==8760*p
            # No claim about unchanged other Full-SC constraints or native rows.
        counts[opt]={'groups_checked':385,'exact_equal_groups':equal,
                     'local_stock_prefix_existence':'DERIVATION_UNDER_REUSED_EXCLUSIVE_TOPOLOGY'}
    return {'status':'INDEPENDENT_RATIONAL_AND_BIT_NEIGHBOUR_CHECK_PASS',
            'options':counts,'formal_full_LP_certificates_added':0,'model_builds':0,
            'matrix_reads':0,'solver_calls':0,'scientific_writes':0}

if __name__=='__main__': print(json.dumps(verify(sys.argv[1]),indent=2))
