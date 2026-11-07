"""V31 W15 stage B 7.1-7.2: run the extraction step of the copied W10 rerank_with_results.py for ONE run directory in its own process (so the
memory of one 2920x3h solved network is released before the next), writing into the W10-format cache keyed by the network SHA256.

  python -I w15b_extract_one.py <rerank_with_results.py> <run dir> <cache dir>
"""
import importlib.util, sys, time
from pathlib import Path

mod_path, run_dir, cache = sys.argv[1:4]
spec = importlib.util.spec_from_file_location("rerank_with_results", mod_path)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
t0 = time.time()
out = m.extract(Path(run_dir), Path(cache))
print(f"EXTRACTED {Path(run_dir).name} -> {out.name} in {time.time() - t0:.0f} s", flush=True)
