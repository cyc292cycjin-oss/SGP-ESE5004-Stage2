import math
exec(open('c7.py').read().split('# --- construct greedy')[0])
from fractions import Fraction as F
sa_by={}
for x_ in sa['groups']:
    sa_by[tuple(sorted(a.replace('fixed resource','final-energy meter') for a in x_['accounts']))]=(F(x_['D']),F(x_['Q']),F(x_['slack']))
def is_pow2(f): 
    n,d=f.numerator,f.denominator; return n>0 and (n&(n-1))==0 and (d&(d-1))==0
ok=0; rs=[]
for g,Dg,Qg,sl in res:
    Dp,Qp,Sp=sa_by[g]; r1=Dp/Dg; r2=Qp/Qg
    if r1==r2 and is_pow2(r1) and (Sp==sl*r1): ok+=1
    rs.append(r1)
print('groups where physical = 2^k * LP (D, Q and slack all exact):',ok,'/',len(res))
print('scale exponents range', min(math.log2(r) for r in rs), max(math.log2(r) for r in rs))
