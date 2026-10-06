"""Portable no-solver verifier for the saved exact local certificate/witness."""
import argparse,json,hashlib
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
import numpy as np

def verify(folder):
    reports=json.loads((folder/'EXACT_LOCAL_DIAGNOSIS_VERIFICATION.json').read_text())['blocks'];checks=[]
    for r in reports:
        num=r['group'];path=folder/f'block_{num}.npz'
        if hashlib.sha256(path.read_bytes()).hexdigest()!=r['local_binary_sha256']:raise ValueError('Binary evidence hash mismatch')
        d=np.load(path);cl=d['constraint_labels'];vl=d['variable_labels'];source=json.loads((folder/f'block_{num}_rows.json').read_text())
        coeff=d['data'];ix=d['indices'];ptr=d['indptr'];lhs=defaultdict(Fraction);rhs=Fraction(0);count=0
        for i,label in enumerate(cl):
            name=source[str(label)];factor=24 if name=='Bus-nodal_balance' else 1 if name=='Store-energy_balance' else None
            if factor is None:continue
            if d['row_lower'][i]!=d['row_upper'][i]:raise ValueError('Certificate uses a nonequality')
            rhs+=factor*Fraction(float(d['row_lower'][i]));count+=1
            for j in range(ptr[i],ptr[i+1]):lhs[int(vl[ix[j]])]+=factor*Fraction(float(coeff[j]))
        lhs={str(k):v for k,v in lhs.items() if v}
        claimed=r['exact_binary64_algebra']
        if count!=claimed['equations'] or rhs!=Fraction(claimed['rhs']) or lhs!={k:Fraction(v) for k,v in claimed['nonzero_lhs'].items()}:raise ValueError('Certificate algebra mismatch')
        for bound in r['terminal_nonnegative_bounds']:
            i=list(cl).index(bound['row']);js=list(range(ptr[i],ptr[i+1]))
            if len(js)!=1 or int(vl[ix[js[0]]])!=bound['variable'] or coeff[js[0]]!=1 or d['row_lower'][i]!=0:raise ValueError('Nonnegative stock bound mismatch')
        if r['exact_rational_witness_feasible']:
            values={int(k):Fraction(v) for k,v in json.loads((folder/f'block_{num}_rational_feasible_witness.json').read_text()).items()}
            if set(values)!=set(map(int,vl)):raise ValueError('Witness label mismatch')
            for i,label in enumerate(cl):
                value=sum((Fraction(float(coeff[j]))*values[int(vl[ix[j]])] for j in range(ptr[i],ptr[i+1])),Fraction(0))
                lo,hi=d['row_lower'][i],d['row_upper'][i]
                if (np.isfinite(lo) and value<Fraction(float(lo))) or (np.isfinite(hi) and value>Fraction(float(hi))):raise ValueError('Witness row violation '+str(label))
            for i,label in enumerate(vl):
                v=values[int(label)];lo,hi=d['var_lower'][i],d['var_upper'][i]
                if (np.isfinite(lo) and v<Fraction(float(lo))) or (np.isfinite(hi) and v>Fraction(float(hi))):raise ValueError('Witness variable bound violation')
            conclusion='VERIFIED_EXACT_FEASIBLE_LOCAL_WITNESS'
        else:
            if rhs<=0 or any(v!=-1 for v in lhs.values()) or set(lhs)!={str(b['variable']) for b in r['terminal_nonnegative_bounds']}:raise ValueError('No sufficient nonnegative-stock contradiction')
            conclusion='VERIFIED_EXACT_BINARY64_LOCAL_CONTRADICTION'
        checks.append(dict(group=num,status='PASS',conclusion=conclusion,equations=count,rows=len(cl),columns=len(vl)))
    return dict(status='PASS',solver_runs=0,checks=checks)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();print(json.dumps(verify(a.evidence),indent=2))
