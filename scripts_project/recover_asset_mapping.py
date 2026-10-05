"""Recover cached first mapping leg and propose a partition-safe second leg.

The 50-node cache identifies source region/AC partition, never a replacement
100-node topology. Every nearest-node assignment remains PENDING approval.
"""
from pathlib import Path
import argparse,json,hashlib,re,math
import pandas as pd,pypsa

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sid(v):return str(int(float(v))) if str(v).replace('.','',1).isdigit() else str(v)
def distance(a,b):
    lat1,lat2=map(math.radians,[a.y,b.y]);dy=lat2-lat1;dx=math.radians(b.x-a.x)
    return 6371*2*math.asin(min(1,math.sqrt(math.sin(dy/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dx/2)**2)))
def recover(rawmap,map50,simplified,reference):
    a=pd.read_csv(rawmap,index_col=0).iloc[:,0];a.index=a.index.map(sid);a=a.map(sid)
    b=pd.read_csv(map50,index_col=0).iloc[:,0];b.index=b.index.map(sid)
    s=pypsa.Network(simplified);s.determine_network_topology();r=pypsa.Network(reference)
    target=r.buses[r.buses.carrier.isin(['AC','DC'])];rows=[]
    for raw,simple in a.items():
        z=dict(RawBus=raw,SimplifiedBus=simple,Node=None,ApprovalStatus='PENDING',DecisionReference=None,Source='Frozen raw-to-simplified and50-node region-partition labels; constrained nearest100-node candidate',Method='CANDIDATE_SAME_COUNTRY_REGION_AND_ORIGINAL_AC_PARTITION_NEAREST',SourceCountry=None,OriginalPartition=None,NodePartition=None)
        if simple not in s.buses.index or simple not in b.index:z['Status']='NO_COMPATIBLE_SIMPLIFIED_MAPPING';rows.append(z);continue
        sb=s.buses.loc[simple];prefix=str(b.loc[simple]).rsplit(' ',1)[0];suffix=re.search(r'(\d+)$',prefix)
        partition=str(sb.sub_network);z.update(Country=sb.country,SourceCountry=sb.country,OriginalPartition=partition,RegionPartitionPrefix=prefix)
        candidates=target[[x.rsplit(' ',1)[0]==prefix for x in target.index]]
        candidates=candidates[candidates.country==sb.country]
        if not suffix or suffix.group(1)!=partition or not len(candidates):z['Status']='NO_COMPATIBLE_REGION_PARTITION_TARGET';rows.append(z);continue
        chosen=min(candidates.index,key=lambda x:(distance(sb,candidates.loc[x]),x))
        z.update(Node=chosen,NodePartition=partition,DistanceKm=distance(sb,candidates.loc[chosen]),Status='CANDIDATE_NOT_APPROVED',TargetCandidates=len(candidates));rows.append(z)
    return dict(status='PARTIAL_SOURCE_CHAIN_RECOVERED_SECOND_LEG_CANDIDATE_ONLY',full_original_to100_mapping_recovered=False,inputs={str(p):sha(p) for p in [rawmap,map50,simplified,reference]},target_geographical_nodes=len(target),rows=rows,solver_runs=0,topology_changed=False,author_optimised_capacities_used=False)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ['rawmap','map50','simplified','reference','output']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();d=recover(a.rawmap,a.map50,a.simplified,a.reference);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n')
