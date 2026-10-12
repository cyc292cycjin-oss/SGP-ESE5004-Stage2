from load import *
from meta import rowfam
import pickle, collections
ci=pickle.load(open('colinfo.pkl','rb'))
fr_names={n for (v,n,t) in ci if n and n.endswith('fixed resource')}
meters={n.replace('fixed resource','final-energy meter') for n in fr_names}
S=np.array([ (n in fr_names) or (n in meters) for (v,n,t) in ci])
print('subsystem cols',S.sum(),collections.Counter(ci[j][0] for j in np.where(S)[0]))
print('meters found in LP', len({ci[j][1] for j in np.where(S)[0] if ci[j][0]=='Link-p'}))
# grow closure: rows touching S; columns in those rows
R=A.tocsr()
rows=np.unique(A[:,np.where(S)[0]].indices)
cols_in=np.unique(R[rows].indices)
outside=cols_in[~S[cols_in]]
print('rows touching S',len(rows),' outside cols in those rows',len(outside))
if len(outside): print(collections.Counter((ci[k][0],ci[k][1][-30:] if ci[k][1] else None) for k in outside).most_common(10))
# load-bus rows: which rows contain only meter Link-p? and loads
fam=collections.Counter(rowfam(i).split('-BN')[0].split('-ID')[0][:40] for i in rows)
print(fam.most_common(15))
print('costs in S: nonzero',(c[S]!=0).sum(),' max|c|',np.abs(c[S]).max())
np.save('S.npy',S); np.save('Srows.npy',rows)
