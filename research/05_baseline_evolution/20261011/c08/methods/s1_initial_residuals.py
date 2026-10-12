from load import *
print('shapes',x.shape,y.shape,rc.shape)
ax=A@x
vrow=np.maximum(rl-ax,0)+np.maximum(ax-ru,0); vrow[np.isnan(vrow)]=0
vcol=np.maximum(lb-x,0)+np.maximum(x-ub,0)
P=c@x+off
print('P',repr(P),' max row viol',vrow.max(),' n>1e-6',(vrow>1e-6).sum(),' n>1e-3',(vrow>1e-3).sum(),' col viol',vcol.max())
r=c-A.T@y
print('rc diff vs solver: max',np.abs(r-rc).max())
fl,fu=np.isfinite(lb),np.isfinite(ub)
print('cols: free',(~fl&~fu).sum(),' lower-only',(fl&~fu).sum(),' upper-only',(~fl&fu).sum(),' boxed',(fl&fu).sum(), ' fixed',(lb==ub).sum())
gl,gu=np.isfinite(rl),np.isfinite(ru)
print('rows: eq',(rl==ru).sum(),' lo-only',(gl&~gu).sum(),' up-only',(~gl&gu).sum(),' range',(gl&gu&(rl!=ru)).sum(),' free',(~gl&~gu).sum())
# row dual sign: y>0 needs finite rl ; y<0 needs finite ru
bad_y=((y>0)&~gl)|((y<0)&~gu)
print('wrong-sign y',bad_y.sum(),' max|y| among',np.abs(y[bad_y]).max() if bad_y.any() else 0)
np.save('r.npy',r); np.save('ax.npy',ax)
