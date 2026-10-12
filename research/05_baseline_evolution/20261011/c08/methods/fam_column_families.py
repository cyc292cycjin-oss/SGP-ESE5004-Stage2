import numpy as np, json
B='/mnt/user-data/uploads/ResearchWorkspaces/ASEAN/outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run/'
vl=np.load(B+'bridge/mapping/vlabels.npy')
d=json.load(open(B+'artifacts/mapping/LABELS.json'))
mx=int(vl.max())+1
fam=np.full(mx,-1,np.int16); names=[]
for k,v in enumerate(d['variables']):
    lab=np.load(B+'artifacts/mapping/'+v['labels_file']).ravel(); lab=lab[lab>=0]
    fam[lab]=k; names.append(v['name'])
colfam=fam[vl]; assert (colfam>=0).all()
np.save('colfam.npy',colfam); json.dump(names,open('famnames.json','w'))
