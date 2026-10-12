from load import *
from meta import rowfam
import pickle
ci=pickle.load(open('colinfo.pkl','rb'))
R=A.tocsr()
nm='BN:2050:Buildings:ResidentialFuel:biomass@BN4 0 Charcoal final-energy meter'
for j in [j for j,(v,n,t) in enumerate(ci) if n==nm and t in (0,)]:
    print('COL',j,ci[j],'cost',c[j])
    for p in range(A.indptr[j],A.indptr[j+1]):
        i=A.indices[p]; ks=R.indices[R.indptr[i]:R.indptr[i+1]]; vs=R.data[R.indptr[i]:R.indptr[i+1]]
        print('   row',i,rowfam(i),'rl/ru',rl[i],ru[i],'nnz',len(ks),'|',[(ci[k][0],(ci[k][1] or '')[-55:],ci[k][2],float(a)) for k,a in zip(ks,vs)][:8])
