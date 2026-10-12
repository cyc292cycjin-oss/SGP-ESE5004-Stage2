from load import *
from meta import *
import pickle
ci=build_cols(); pickle.dump(ci,open('colinfo.pkl','wb'))
fr=[j for j,(v,nm,t) in enumerate(ci) if nm and nm.endswith('fixed resource')]
import collections
print('fixed-resource cols by var',collections.Counter(ci[j][0] for j in fr))
stores=sorted({ci[j][1] for j in fr}); print('n fixed-resource stores',len(stores))
# pick one store, day 0 and 1: list rows
s=stores[0]; print('example',s)
R=A.tocsr()
for j in [j for j in fr if ci[j][1]==s and ci[j][2] in (0,1,364)]:
    print('COL',j,ci[j],'cost',c[j],'lb/ub',lb[j],ub[j])
    for p in range(A.indptr[j],A.indptr[j+1]):
        i=A.indices[p]; ks=R.indices[R.indptr[i]:R.indptr[i+1]]; vs=R.data[R.indptr[i]:R.indptr[i+1]]
        print('   row',i,rowfam(i),'rl/ru',rl[i],ru[i],'|',[(ci[k][0],(ci[k][1] or '')[-45:],ci[k][2],round(a,6)) for k,a in zip(ks,vs)][:6])
