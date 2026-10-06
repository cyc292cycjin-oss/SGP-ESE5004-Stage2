"""Portable exact-arithmetic verification of the saved LP contradiction; no solver."""
import argparse,hashlib,json,re
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path

def verify(folder,lp=None):
    folder=Path(folder);proof=json.loads((folder/'EXACT_LP_CONTRADICTION.json').read_text())
    rows=json.loads((folder/'EXACT_LP_CONTRADICTION_ROWS.json').read_text());lhs=defaultdict(D);rhs=D(0)
    if len(rows)!=proof['equation_count']:raise ValueError('Certificate equation count changed')
    for label,row in rows.items():
        factor=D(row['factor']);lines=row['raw_lines']
        if lines[0]!='c'+label+':':raise ValueError('LP row label changed')
        for s in lines[1:]:
            term=re.fullmatch(r'([+-]?[\d.eE+-]+) x(\d+)',s)
            if term:lhs[term[2]]+=factor*D(term[1])
            elif s.startswith('= '):rhs+=factor*D(s.split()[1])
            else:raise ValueError('Non-equation in equality certificate')
    lhs={k:v for k,v in lhs.items() if v}
    expected={str(r['variable_label']):D(r['coefficient']) for r in proof['remaining_lhs']}
    if lhs!=expected or rhs!=D(proof['rhs']) or rhs<=0:raise ValueError('Algebraic contradiction does not reproduce')
    for label,coef in lhs.items():
        b=proof['nonnegative_inventory_bounds_verified_from_actual_lp'][label]
        if coef>=0 or b['raw_lines'][1]!='+1 x'+label or b['raw_lines'][2] not in ['>= -0','>= +0','>= 0']:
            raise ValueError('Required nonnegative bound is absent')
    if lp is not None:
        h=hashlib.sha256()
        with Path(lp).open('rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
        if h.hexdigest()!=proof['original_lp_sha256']:raise ValueError('Original LP hash mismatch')
        targets={int(k):r['raw_lines'] for k,r in rows.items()}
        targets.update({b['constraint_label']:b['raw_lines'] for b in proof['nonnegative_inventory_bounds_verified_from_actual_lp'].values()})
        found={};current=None
        with Path(lp).open() as f:
            for line in f:
                s=line.strip();match=re.fullmatch(r'c(\d+):',s)
                if match:
                    label=int(match[1]);current=label if label in targets else None
                    if current is not None:found[current]=[s]
                elif current is not None and s:
                    found[current].append(s)
                    if s.startswith(('=','<=','>=')):current=None
        if found!=targets:raise ValueError('Certificate rows differ from actual saved LP')
    return {'status':'PASS_EXACT_ALGEBRA','equations':len(rows),'positive_rhs_mwh':str(rhs),'nonnegative_terminal_stocks':len(lhs),'solver_runs':0,'original_lp_verified':lp is not None,'not_a_feasibility_result_for_a_corrected_model':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',required=True);p.add_argument('--lp');a=p.parse_args();print(json.dumps(verify(a.evidence,a.lp),indent=2))
