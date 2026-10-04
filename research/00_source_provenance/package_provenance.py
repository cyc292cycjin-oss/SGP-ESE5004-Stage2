"""Create a portable source-audit bundle; leave large author network caches separate."""
from validate_provenance import ROOT,files,digest
from pathlib import Path
import zipfile,json
dest=ROOT.parents[1]/'outputs/source_provenance_20260930.zip'
dest.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files():z.write(p,'source_provenance/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
print(json.dumps({'path':str(dest),'bytes':dest.stat().st_size,'sha256':digest(dest),'excludes':'cache/ contains the two large author networks; member paths and hashes remain in bundle'},indent=2))
