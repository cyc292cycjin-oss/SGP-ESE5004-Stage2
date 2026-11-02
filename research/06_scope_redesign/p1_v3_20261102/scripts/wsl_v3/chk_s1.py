import json, logging, sys
from pathlib import Path
W = Path("/home/jin/wt_v3_20261102"); sys.path.insert(0, str(W / "scripts_project"))
import pypsa
logging.disable(logging.WARNING)
src = (W / "tests/research/test_s1_built_networks.py").read_text()
print(src[:1100])
import re
print(open(W / "scripts_project/build_research_network.py").read().split("\n")[70:80])
