from load import *
import math
R=A.tocsr()
nnz_row=np.diff(R.indptr)
sing=nnz_row==1
print('singleton rows',sing.sum(),' rows with 0 nnz',(nnz_row==0).sum())
si=np.where(sing)[0]; sj=R.indices[R.indptr[si]]; sa=R.data[R.indptr[si]]
# implied column bounds from singleton rows: rl<=a x<=ru
lo=np.where(sa>0, rl[si]/sa, ru[si]/sa); hi=np.where(sa>0, ru[si]/sa, rl[si]/sa)
L2=lb.copy(); U2=ub.copy()
np.maximum.at(L2,sj,lo); np.minimum.at(U2,sj,hi)
print('cols w/ finite L2',np.isfinite(L2).sum(),' finite U2',np.isfinite(U2).sum(),' both',(np.isfinite(L2)&np.isfinite(U2)).sum(),' none',(~np.isfinite(L2)&~np.isfinite(U2)).sum())
# r' = c - A_ns^T y  (exclude singleton rows)
yns=y.copy(); yns[sing]=0
# fix wrong-sign duals on nonsingleton rows -> 0 (Neumaier)
gl,gu=np.isfinite(rl),np.isfinite(ru)
bad=((yns>0)&~gl)|((yns<0)&~gu); print('wrong-sign y on non-singleton rows',bad.sum()); yns[bad]=0
rp=c-A.T@yns
# row term
rowterm=np.where(yns>0, yns*np.where(gl,rl,0), np.where(yns<0, yns*np.where(gu,ru,0),0))
# column term: min_{L2<=x<=U2} rp x
need_L=rp>0; need_U=rp<0
infL=need_L&~np.isfinite(L2); infU=need_U&~np.isfinite(U2)
inf=infL|infU
print('cols making bound -inf:',inf.sum(),' sum|rp| there',np.abs(rp[inf]).sum(),' max',np.abs(rp[inf]).max() if inf.any() else 0)
colterm=np.zeros(n)
colterm[need_L&~inf]=rp[need_L&~inf]*L2[need_L&~inf]
colterm[need_U&~inf]=rp[need_U&~inf]*U2[need_U&~inf]
Dfin=math.fsum(rowterm)+math.fsum(colterm)+off
P=math.fsum(c*x)+off
print('P',P,' D(finite part, ignoring inf cols)',Dfin,' gap',P-Dfin,' rel',(P-Dfin)/abs(P))
np.save('L2.npy',L2);np.save('U2.npy',U2);np.save('rp.npy',rp);np.save('inf.npy',inf);np.save('sing.npy',sing)
# where are inf cols relative to x magnitude
print('|x| at inf cols: max',np.abs(x[inf]).max() if inf.any() else 0, ' rp*x contribution sum',math.fsum(np.abs(rp[inf]*x[inf])))
