"""Independent small-evidence checks only: no NetCDF, NPZ, PyPSA or solver."""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import math,json,hashlib,struct
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence'
def read(n):return json.loads((E/n).read_text())
def save(n,j):(E/n).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
checks=[]
def check(name,test,detail):
 assert test,name
 checks.append({'check':name,'status':'PASS','detail':detail})
def round_by_integer_bits(x):
 if not x:return 0.0
 assert x>0
 e=x.numerator.bit_length()-x.denominator.bit_length()
 if x<F(2)**e:e-=1
 assert -1022<=e<=1023
 y=x/(F(2)**(e-52));n,r=divmod(y.numerator,y.denominator)
 if 2*r>y.denominator or (2*r==y.denominator and n%2):n+=1
 return math.ldexp(float(n),e-52)
j=read('C01_LOAD_ANNUAL_EXACT_CHECK.json');p=read('C01_CF_INFLOW_ROUNDING_CHECK.json');inv=read('C01_DYNAMIC_ATTRIBUTE_INVENTORY.json');result=read('C01_RESULT_SUMMARY.json')
allrows=j['records']+p['CF']['records']+p['inflow']['records']
mean_checks=0
for r in allrows:
 old=F(r['annual_original']['exact']);new=F(r['annual_daily']['exact']);delta=F(r['annual_delta_daily_minus_original']['exact']);bound=F(r['annual_half_ULP_bound']['exact'])
 assert new-old==delta and abs(delta)<=bound
 assert (delta==0)==(r['classification']=='EXACT_ANNUAL_PRESERVED')
 assert int(r['nonrepresentable_day_bitmap_hex'],16).bit_count()==r['not_exactly_representable_daily_means']
 ex=r['worst_mean_example'];m=sum((F(float.fromhex(x)) for x in ex['source_8_hex']),F(0))/8
 assert m==F(ex['exact_mean'])
 rn=round_by_integer_bits(m);assert rn.hex()==ex['nearest_hex']
 assert F(rn)-m==F(ex['signed_error']) and abs(F(rn)-m)<=F(ex['half_ulp_bound'])
 mean_checks+=1
check('All asset annual identities and bounds',len(allrows)==2237,'Exact stored Fractions rechecked for 1737 Load + 460 CF + 40 inflow; no source scan repeated')
check('Independent nearest-even integer arithmetic',mean_checks==2237,'Each saved representative bucket recomputed using integer significand rounding, independent of float(Fraction)')
check('Actual dynamic coverage',len(inv['dynamic_attributes'])==3 and not inv['additional_dynamic_attributes'],'Only Load.p_set, Generator.p_max_pu, StorageUnit.inflow')
check('Missing/invalid observations',all(not any(r['invalid_values'].values()) for r in inv['dynamic_attributes']),'No NaN, Inf or negative observations; _FillValue metadata does not imply NULL data')
for key,rows in [('loads',j['records']),('CF',p['CF']['records']),('inflow',p['inflow']['records'])]:
 s=result[key];ds=[F(r['annual_delta_daily_minus_original']['exact']) for r in rows]
 check(key+' classification counts',s['exact_annual']==sum(x==0 for x in ds) and s['positive_drift']==sum(x>0 for x in ds) and s['negative_drift']==sum(x<0 for x in ds),len(rows))
 check(key+' aggregate exact drift',F(s['sum_signed_delta']['exact'])==sum(ds,F(0)) and F(s['sum_absolute_delta']['exact'])==sum(map(abs,ds),F(0)),'Both signed and gross errors checked; no cancellation masquerades as per-asset preservation')
check('Biomass closure',len(j['biomass_groups'])==385 and all(F(g['daily_D_MWh'])==F(g['original_D_MWh'])<=F(g['approved_Q_prime_MWh']) for g in j['biomass_groups']),'807 approved accounts reused, no Q regeneration')
vary=[r for r in j['records'] if not r['constant_source_binary64']]
check('Scope of demand drift',len(vary)==96 and all(r['carrier']=='electricity' for r in vary) and sum(r['classification']!='EXACT_ANNUAL_PRESERVED' for r in vary)==95,'1641 flat and one varying Load exact annually')
check('CF source range issue preserved',p['CF']['summary']['source_above_one_assets']==6 and p['CF']['summary']['source_above_one_values']==44 and p['CF']['summary']['daily_above_one_values']==0,'No clipping performed; input exceeds 1 by one ULP')
obstruct=[r for r in vary if r['classification']!='EXACT_ANNUAL_PRESERVED' and not r['local_same_binade_ULP_lattice_necessary_condition']]
check('Local rounding lattice obstruction',len(obstruct)==86 and all(F(r['required_correction_in_minimum_daily_ULPs']['exact']).denominator!=1 for r in obstruct),'Cannot repair within unchanged daily binades by ordinary integer-ULP changes; remaining 9 not thereby proven repairable')
# Mathematical range conditions for one proposed two-term exact representation;
# no decomposition arrays or corrected means are generated.
maxbits=max(r['maximum_exact_mean_significant_bits'] for r in vary);low=min(r['source_minimum'] for r in vary);high=max(r['source_maximum'] for r in vary)
check('Proposed two-term proof range',maxbits<=57 and low>=16 and high<65536,'Means have at most 57 significant bits. Original exponents >=4 imply exact mean quantum >=2^-51; a <=4-bit remainder is safely representable in binary64.')
candidate={'status':'PROPOSED_NOT_APPLIED','candidate_count':1,'id':'EXACT_NONNEGATIVE_TWO_TERM_DAILY_DEMAND','scope':{'varying_Loads':96,'daily_cells':35040,'inexact_cells_requiring_remainder':31542,'annual_drift_Loads':95,'annual_exact_varying_Loads':1,'maximum_significant_bits':maxbits,'source_MW_min':low,'source_MW_max':high},'construction':'For exact m=N/2^k>=0 in lowest dyadic form, p=bit_length(N). If p<=53 use m. Else q=p-53, H=floor(N/2^q)*2^(q-k), L=(N mod 2^q)*2^-k. m=H+L exactly, H,L>=0. For actual p<=57, L has at most 4 significant bits.','projection_proof':'Keep separate native constants: impose v=L with fixed bounds and S-v=H (S is physical net supply). Eliminating v gives S=H+L=m. Weighted annual sum 24*sum(m)=3*sum(original P). All source Q and physical demands unchanged.','warning':'Ordinary two PyPSA Load entries sharing a Bus are insufficient: float64 groupby may collapse H+L back to rounded m. Future implementation must retain separate terms through CSC/native readback and acceptance/export mapping. This changes numerical representation and requires explicit approval; no production/model implementation in C01.','not_guaranteed':'Numerical enforcement, presolve behavior, solver convergence or V4 PASS not demonstrated. No new supply/negative correction Load/slack is permitted.'}
save('C01_PROPOSED_REPRESENTATION_RULE.json',candidate)
check('Decision classification',result['status']=='C01_REPRESENTATION_DECISION_REQUIRED' and not result['blockers'],'Identities/coverage pass, annual demand representation needs a decision')
receipt={'status':'PASS','checks':checks,'check_count':len(checks),'representative_exact_rounding_checks':mean_checks,'source_full_scan_repeated':False,'models_built':0,'solver_calls':0,'proposed_rule_applied':False}
save('C01_INDEPENDENT_CHECK_RECEIPT.json',receipt)
print(json.dumps({'status':'PASS','checks':len(checks),'buckets_crosschecked':mean_checks,'candidate_rules_proposed':1,'candidate_applied':False}))
