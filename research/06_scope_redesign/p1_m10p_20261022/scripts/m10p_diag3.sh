E=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022/evidence
/home/jin/miniforge3/envs/pypsa-earth/bin/python - $E <<'P'
import json, sys
from pathlib import Path
E = Path(sys.argv[1])
r = json.loads((E / "M10P_NETWORK_REBUILD.json").read_text()); d = json.loads((E / "M10P_NETWORK_CONTENT_DIFF.json").read_text())
for n in r["networks"]:
    print(n["scenario"], n["file"], n["bytes"], n["sha256"], n["reference_sha256"])
for k, v in d.items():
    print(k, v["meta_differences"], v["data_differences_count"], v["snapshots_equal"], v["snapshot_weightings_differ"])
P
grep -rn "bus_mapping_source" /home/jin/wt_m10p_20261022/scripts_project/*.py | head -5
cat $E/M10P_BUILD_STATUS.txt
