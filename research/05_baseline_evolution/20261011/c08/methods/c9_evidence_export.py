from load import *
import json, math, hashlib, collections
S=np.load('S.npy'); Sr=np.zeros(m,bool); Srows=np.load('Srows.npy'); Sr[Srows]=True
Z='zips/'
k7=json.load(open(Z+'C07_V4_RELIABILITY_REVIEW/research/05_baseline_evolution/20261011/c07/evidence/A_KKT_CLASSIFICATION.json'))
rf7=json.load(open(Z+'C07_V4_RELIABILITY_REVIEW/research/05_baseline_evolution/20261011/c07/evidence/A_ROW_FAMILY_CHECK.json'))
k6=json.load(open(Z+'C06_FINAL_COMPARATIVE_REVIEW/research/05_baseline_evolution/20261011/c06/evidence/C06_KKT_FAILURE_SET_COMPARISON.json'))
st7=np.array([f['column'] for f in k7['failed_columns']])
sg7=np.array([e[0] if isinstance(e,list) else e['index'] for g in k7['dual_sign_failure_groups'] for e in g['entries']],int)
r6=np.array(rf7['C06_transition']['resolved']+rf7['C06_transition']['retained'])
st6=np.array(k6['stationarity_transition']['retained']+k6['stationarity_transition']['new'])
st3=np.array(k6['stationarity_transition']['resolved']+k6['stationarity_transition']['retained'])
s3=np.array([int(s.split(':')[1]) for s in k6['sign_transition']['resolved']])
big=np.abs(y)>1e9
def sha(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
ov={'definition':'block = all columns of the 807 "fixed resource" Stores (Store-e, Store-p) and their 807 "final-energy meter" Links (Link-p, Link-p_nom), plus every row touching them',
 'block_columns':int(S.sum()),'block_rows':int(len(Srows)),'main_columns':int((~S).sum()),'main_rows':int((~Sr).sum()),
 'rows_touching_block_containing_outside_columns':0,'block_nonzero_costs':int((c[S]!=0).sum()),
 'block_column_index_sha256':sha(np.where(S)[0].astype(np.int64)),'block_row_index_sha256':sha(Srows.astype(np.int64)),
 'overlap':{
  'C07A_stationarity_failed_columns':[int(len(st7)),int(S[st7].sum())],
  'C07A_dual_sign_free_RC_failures':[int(len(sg7)),int(S[sg7].sum())],
  'C07A_failed_matrix_rows':[1,int(Sr[3455225])],
  'C06_failed_matrix_rows':[int(len(r6)),int(Sr[r6].sum())],
  'C06_stationarity_failed_columns':[int(len(st6)),int(S[st6].sum())],
  'C03_stationarity_failed_columns':[int(len(st3)),int(S[st3].sum())],
  'C03_dual_sign_failures':[int(len(s3)),int(S[s3].sum())],
  'C07A_rows_with_abs_dual_gt_1e9':[int(big.sum()),int((big&Sr).sum())]},
 'overlap_format':'[total, inside block]',
 'C07A_max_abs_dual_inside_block':float(np.abs(y[Sr]).max()),'C07A_max_abs_dual_outside_block':float(np.abs(y[~Sr]).max()),
 'note':'account/obligation-group failures (C03 377/111, C06 85, C07A 0) concern the 807 accounts, which are by construction inside the block',
 'source':{'C07_review_zip':'outputs/C07_V4_RELIABILITY_REVIEW.zip','C06_review_zip':'outputs/C06_FINAL_COMPARATIVE_REVIEW.zip'}}
json.dump(ov,open('C08_FAILURE_BLOCK_OVERLAP.json','w'),indent=1)
g=json.load(open('groups_sg.json'))
Sg=np.array([r[0] for r in g]); Dg=np.array([r[1] for r in g])
gs={'groups':385,'accounts':807,'accounts_per_group':dict(collections.Counter(str(r[2]) for r in g)),
 'physical_slack_MWh':{'min':float(Sg.min()),'median':float(np.median(Sg)),'max':float(Sg.max())},
 'physical_relative_slack_max':float((Sg/Dg).max()),
 'count_slack_below':{'1e-9':int((Sg<1e-9).sum()),'1e-7':int((Sg<1e-7).sum()),'1e-6':int((Sg<1e-6).sum())},
 'LP_coordinates':'block values in the C03 daily CSC equal physical values divided by 2^k, k in [0,28], exactly for D, Q and slack in all 385 groups',
 'LP_slack_range':['1/9223372036854775808 (~1.08e-19)','~4.13e-16'],
 'solver_FeasibilityTol':1e-6,
 'source':'SCHEME_A_DAILY_EXACT_GROUPS.json (C03 run artifacts) and C03 daily CSC'}
json.dump(gs,open('C08_GROUP_SLACK.json','w'),indent=1)
