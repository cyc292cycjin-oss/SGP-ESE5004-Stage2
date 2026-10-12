from load import *
import json, pickle, collections
S=np.load('S.npy'); Srows=np.zeros(m,bool); Srows[np.load('Srows.npy')]=True
Z='zips/'
k7=json.load(open(Z+'C07_V4_RELIABILITY_REVIEW/research/05_baseline_evolution/20261011/c07/evidence/A_KKT_CLASSIFICATION.json'))
rf7=json.load(open(Z+'C07_V4_RELIABILITY_REVIEW/research/05_baseline_evolution/20261011/c07/evidence/A_ROW_FAMILY_CHECK.json'))
k6=json.load(open(Z+'C06_FINAL_COMPARATIVE_REVIEW/research/05_baseline_evolution/20261011/c06/evidence/C06_KKT_FAILURE_SET_COMPARISON.json'))
st7=np.array([f['column'] for f in k7['failed_columns']])
sg7=[]
for g in k7['dual_sign_failure_groups']:
    for e in g.get('entries',g.get('failures',[])): sg7.append(e[0] if isinstance(e,list) else e.get('index'))
print('C07A stationarity fails',len(st7),' in block',S[st7].sum())
print('C07A sign fails listed',len(sg7),' in block',S[np.array(sg7,int)].sum() if sg7 else 'n/a', ' groups',len(k7['dual_sign_failure_groups']), list(k7['dual_sign_failure_groups'][0].keys()))
print('C07A failed row 3455225 in block',Srows[3455225])
c6rows=json.load(open(Z+'C07_V4_RELIABILITY_REVIEW/research/05_baseline_evolution/20261011/c07/evidence/A_ROW_FAMILY_CHECK.json'))['C06_transition']
r6=np.array(c6rows['resolved']+c6rows['retained']); print('C06 failed rows',len(r6),' in block',Srows[r6].sum())
st6=np.array(k6['stationarity_transition']['retained']+k6['stationarity_transition']['new'])
print('C06 stationarity',len(st6),' in block',S[st6].sum())
st3=np.array(k6['stationarity_transition']['resolved']+k6['stationarity_transition']['retained'])
print('C03 stationarity',len(st3),' in block',S[st3].sum())
s3=np.array([int(s.split(':')[1]) for s in k6['sign_transition']['resolved']]); print('C03 sign fails',len(s3),' in block',S[s3].sum())
big=np.abs(y)>1e9; print('huge |y|>1e9 rows',big.sum(),' in block',(big&Srows).sum(),' max|y| outside block',np.abs(y[~Srows]).max())
