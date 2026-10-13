import numpy as np, scipy.sparse as sp, json
B='/mnt/user-data/uploads/ResearchWorkspaces/ASEAN/outputs/'
M=B+'c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run/bridge/math_problem/'
V=B+'c07_daily_diagnostic/c07a_daily122_20261012T162928Z_0d9301f2/cloud_run/canonical_raw_for_V4/vectors/'
L=lambda f: np.load(M+f)
n,m=2450005,6042238
A=sp.csc_matrix((L('value.npy'),L('index.npy'),L('start.npy')),shape=(m,n))
rl,ru,c,lb,ub=L('row_lower.npy'),L('row_upper.npy'),L('cost.npy'),L('col_lower.npy'),L('col_upper.npy')
x,y,rc=np.load(V+'X.npy'),np.load(V+'Pi.npy'),np.load(V+'RC.npy')
off=-12788967.997821666
