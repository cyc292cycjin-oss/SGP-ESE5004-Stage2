#!/bin/bash
mkdir -p /home/jin/v3/pylib
cp -r /mnt/c/Users/20122/miniconda3/Lib/site-packages/pypdf /home/jin/v3/pylib/
ls /home/jin/miniforge3/envs/pypsa-earth/bin | grep -iE 'pdf|poppler|tesseract' | head
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
$PY - <<'P'
import sys; sys.path.insert(0,'/home/jin/v3/pylib')
import pypdf, PIL; print(pypdf.__version__, PIL.__version__)
from pathlib import Path
SRC="/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102/01_industry/225_ewg_apec-energy-statistics-2022.pdf"
out=Path("/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/3b84a8d8-c3d9-4930-9986-da94fd4c6e0e/scratchpad/apec_img"); out.mkdir(parents=True,exist_ok=True)
r=pypdf.PdfReader(SRC)
for i in (47,48,77,78,95,96,125,126,137,138,149,150,161,162):
    pg=r.pages[i-1]
    ims=list(pg.images)
    print(i,len(ims),[ (im.name,len(im.data)) for im in ims][:4])
    for k,im in enumerate(ims):
        (out/f"p{i:03d}_{k}_{im.name}").write_bytes(im.data)
P
