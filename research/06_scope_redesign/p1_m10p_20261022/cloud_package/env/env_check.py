"""M10P environment check (S4N supplement 01 B3 practice): the environment running this script against ENV_LOCK.txt (pip list --format=freeze of
the local reference environment). The key packages must be identical - python, pypsa, linopy, xarray, pandas, numpy, scipy, gurobipy, netCDF4,
h5netcdf, dask, pyomo, highspy; every other difference is listed as information.

    <environment python> env_check.py ENV_LOCK.txt [--out ENV_CHECK.json]      exit 0 = key packages identical, 1 = not
"""
import argparse
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

KEY = ["pypsa", "linopy", "xarray", "pandas", "numpy", "scipy", "gurobipy", "netcdf4", "h5netcdf", "dask", "pyomo", "highspy"]
PIP = re.compile(r"^([A-Za-z0-9_.\-]+)==([^=\s]+)$")


def norm(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def parse(lines) -> dict:
    return {norm(m.group(1)): m.group(2) for m in (PIP.match(x.strip()) for x in lines) if m}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("lock", type=Path); ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    text = a.lock.read_text().splitlines()
    want = parse(text)
    py_lock = next((x.split()[-1] for x in text if x.startswith("# Python ")), None)
    have = parse(subprocess.run([sys.executable, "-m", "pip", "list", "--format=freeze"], capture_output=True, text=True).stdout.splitlines())
    key = {k: dict(lock=want.get(k), instance=have.get(k), equal=want.get(k) == have.get(k)) for k in KEY}
    key["python"] = dict(lock=py_lock, instance=platform.python_version(), equal=py_lock == platform.python_version())
    res = dict(key_packages=key, key_all_equal=all(v["equal"] for v in key.values()), lock_packages=len(want), instance_packages=len(have),
               only_lock=sorted(set(want) - set(have)), only_instance=sorted(set(have) - set(want)),
               version_differences={k: [want[k], have[k]] for k in sorted(set(want) & set(have)) if want[k] != have[k]})
    if a.out:
        a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(dict(key_all_equal=res["key_all_equal"], key={k: (v["lock"], v["instance"]) for k, v in key.items() if not v["equal"]},
                          counts=[res["lock_packages"], res["instance_packages"]], only_lock=res["only_lock"][:20], only_instance=res["only_instance"][:20],
                          n_version_differences=len(res["version_differences"]))))
    sys.exit(0 if res["key_all_equal"] else 1)


if __name__ == "__main__":
    main()
