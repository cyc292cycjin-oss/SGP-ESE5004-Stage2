#!/bin/bash
which pdftotext pdfinfo ogrinfo 2>&1
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
$PY - <<'P'
import importlib
for m in ("pypdf","PyPDF2","fitz","pdfplumber","geopandas","fiona","pyogrio","shapely","osgeo","openpyxl","rasterio","searoute","networkx"):
    try:
        x=importlib.import_module(m); print(m, getattr(x,"__version__","ok"))
    except Exception as e: print(m,"--",type(e).__name__)
P
ls /home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources 2>/dev/null | head
find /home/jin/research/SGP_ESE5004_Stage2 -maxdepth 6 \( -name 'regions_onshore*' -o -name '*gadm*' -o -name 'bus_regions*' -o -name 'gadm_shapes*' -o -name 'country_shapes*' -o -name 'gadm41*' \) 2>/dev/null | head -20
