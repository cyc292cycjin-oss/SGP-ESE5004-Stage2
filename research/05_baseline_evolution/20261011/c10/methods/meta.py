import numpy as np, json, bisect
B='/mnt/user-data/uploads/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run/'
vl=np.load(B+'bridge/mapping/vlabels.npy')
LB=json.load(open(B+'artifacts/mapping/LABELS.json'))
MM=json.load(open(B+'bridge/mapping/MAPPING_MANIFEST.json'))
starts=[r['start'] for r in MM['row_ranges']]
def rowfam(i): return MM['row_ranges'][bisect.bisect_right(starts,i)-1]['family']
# column -> (varname, comp name, t)
colinfo={}
def build_cols():
    lab2={}
    for v in LB['variables']:
        lab=np.load(B+'artifacts/mapping/'+v['labels_file'])
        dims=v['dims']; co=v['coordinates']
        for idx,l in np.ndenumerate(lab):
            if l<0: continue
            if len(dims)==2: lab2[int(l)]=(v['name'],co[dims[1]][idx[1]],idx[0])
            elif len(dims)==1: lab2[int(l)]=(v['name'],co[dims[0]][idx[0]],None)
            else: lab2[int(l)]=(v['name'],None,None)
    return [lab2[int(l)] for l in vl]
