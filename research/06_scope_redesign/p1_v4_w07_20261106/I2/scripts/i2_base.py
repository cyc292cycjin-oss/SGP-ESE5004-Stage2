"""I2 section 2 item 1: the 2019 base year rebuilt from the UNSD SDMX current database (decision 210 item 1), re-using the I1 rebuild code and its
reproduction gates (instruction section 2.1).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i2_base.py

The I1 scripts i1_common.py, i1_sdmx.py and i1_base.py (as merged into codex/v4-i2-20261106) are copied to /home/jin/v4i2/i1code/scripts with
exactly these edits (each asserted to occur once):
  * i1_common.REPO -> /home/jin/wt_v4_i2 (the I2 worktree), i1_common.SCRATCH -> /home/jin/v4i2 (the I2 scratch folder); the I1 output folders
    (BASE2019_SDMX/, tables/, evidence/) follow the copy (parents[1] = /home/jin/v4i2/i1code), so no I1 deliverable is touched;
  * i1_base.D207_COAL gains ('ID', 'coke oven coke') = 28.20 GJ/t (decision 210 item 1: ID coke keeps 28.20; the SDMX 20.19 is below the physical
    range of coke). S5 of the copy is therefore the I2 base 'S5p'.
The copied i1_sdmx.py rebuilds the capsule from the eleven W12 SDMX responses (read only; SHA256 checked against the W12 registry by I1's code),
i1_base.py runs the gates G1 (BASE_RECONSTRUCTION), G2 (D1 base rows) and G3 (generalised blend rule) and writes d1_base_S0..S5.csv.
I2 checks afterwards: (i) S5p D1 rows = I1's committed S5 column of BASE2019_SDMX_D1_ROWS.csv (the coke factor touches no final-consumption row);
(ii) S0..S4 = I1's committed columns; (iii) the SDMX capsule records = I1's committed SDMX_2019_CAPSULE_RECORDS.csv. Any difference stops the run.
Writes tables/I2_BASE_CHECKS.csv, evidence/I2_base.json; the scratch base files stay in /home/jin/v4i2/.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i2_common as cm  # noqa: E402

CODE = cm.SCRATCH / "i1code" / "scripts"
I1S = cm.G["I1"] / "scripts"
EDITS = {
    "i1_common.py": [('REPO = Path("/home/jin/wt_v4_i1")', 'REPO = Path("/home/jin/wt_v4_i2")'),
                     ('SCRATCH = Path("/home/jin/v4i1")', 'SCRATCH = Path("/home/jin/v4i2")')],
    "i1_base.py": [('D207_COAL = {("ID", "hard coal"): D("20.29")}',
                    'D207_COAL = {("ID", "hard coal"): D("20.29"), ("ID", "coke oven coke"): D("28.20")}   # I2 copy: decision 210 item 1 (ID coke 28.20)')],
    "i1_sdmx.py": [],
}


def copy_code(ev: cm.Evidence) -> None:
    if CODE.parent.exists():
        shutil.rmtree(CODE.parent)
    CODE.mkdir(parents=True)
    for f, edits in EDITS.items():
        src = (I1S / f).read_text()
        for old, new in edits:
            if src.count(old) != 1:
                raise SystemExit(f"STOP: edit point not unique in {f}: {old}")
            src = src.replace(old, new)
        (CODE / f).write_text(src)
        ev.add(f"code.{f}", dict(source_sha256=cm.sha256(I1S / f), copy_sha256=cm.sha256(CODE / f), edits=[e[1] for e in edits]), "file", "VERIFIED", "-",
               f"{I1S / f} -> {CODE / f}", "I1 rebuild code re-used with path / coke edits only")


def run(script: str) -> float:
    t = time.time()
    r = subprocess.run([cm.PY, script], cwd=CODE, capture_output=True, text=True, env=cm.ENV)
    (cm.SCRATCH / f"log_{script}.txt").write_text(r.stdout + "\n--- stderr\n" + r.stderr)
    if r.returncode:
        raise SystemExit(f"STOP: {script} failed: {r.stderr[-3000:]}")
    return time.time() - t


def main():
    ev = cm.Evidence("I2_base")
    cm.SCRATCH.mkdir(parents=True, exist_ok=True)
    copy_code(ev)
    t1 = run("i1_sdmx.py"); t2 = run("i1_base.py")
    ev.add("timing_s", dict(i1_sdmx=t1, i1_base=t2), "s", "VERIFIED", "-", "scratch run")
    checks = []
    # (iii) capsule records vs I1
    mine = pd.read_csv(cm.SCRATCH / "i1code/BASE2019_SDMX/SDMX_2019_CAPSULE_RECORDS.csv", dtype=str, keep_default_na=False)
    ref = pd.read_csv(cm.G["I1"] / "BASE2019_SDMX/SDMX_2019_CAPSULE_RECORDS.csv", dtype=str, keep_default_na=False)
    ok3 = mine.equals(ref)
    checks.append(dict(check="SDMX capsule records = I1 committed", rows=len(mine), result=ok3))
    # (i)/(ii) D1 rows S0..S5 vs I1 committed table (string compare of the numbers after float parse, exact)
    mi = pd.read_csv(cm.SCRATCH / "i1code/BASE2019_SDMX/BASE2019_SDMX_D1_ROWS.csv")
    rf = pd.read_csv(cm.G["I1"] / "BASE2019_SDMX/BASE2019_SDMX_D1_ROWS.csv")
    key = ["country", "sector", "carrier", "account"]
    m = mi.merge(rf, on=key, how="outer", suffixes=("_i2", "_i1"), indicator=True)
    coke = (m.country == "ID") & (m.account == "NonEnergy:Coke-oven coke")
    coke_expected = 791.0 * 1000.0 * (28.20 - 20.1947) / 3.6   # SDMX ID coke: all 791 kt are 'Non-energy uses' (transaction 11); factor 20.1947 -> 28.20
    for s in ("S0", "S1", "S2", "S3", "S4", "S5"):
        dd = (m[f"{s}_i2"].fillna(0.0) - m[f"{s}_i1"].fillna(0.0))
        if s == "S5":
            dev_c = float(dd[coke].sum())
            checks.append(dict(check="D1 row ID NonEnergyUse coal 'NonEnergy:Coke-oven coke': S5p - I1 S5 = 791 kt x (28.20 - 20.1947) / 3.6 (decision 210 item 1; outside T_v2)",
                               rows=1, max_abs_dev_mwh=dev_c - coke_expected, result=bool(abs(dev_c - coke_expected) < 1e-3), note=f"delta {dev_c:.3f} MWh"))
            dd = dd[~coke]
        d = float(dd.abs().max())
        checks.append(dict(check=f"D1 rows {s} = I1 committed BASE2019_SDMX_D1_ROWS.csv {s}" + (" (I2 S5p, every row except the ID NEU coke row)" if s == "S5" else ""),
                           rows=int(len(dd)), unmatched=int((m._merge != "both").sum()), max_abs_dev_mwh=d, result=bool(d == 0.0 and (m._merge == "both").all())))
    # the scratch d1 base S0 file vs I1's scratch S0 file: byte compare (same code, same inputs)
    a = (cm.SCRATCH / "d1_base_S0.csv").read_bytes(); b = Path("/home/jin/v4i1/d1_base_S0.csv").read_bytes() if Path("/home/jin/v4i1/d1_base_S0.csv").exists() else b""
    checks.append(dict(check="scratch d1_base_S0.csv byte-identical to I1 scratch d1_base_S0.csv", rows="", result=(a == b), note=f"sha256 {cm.sha256_bytes(a)[:16]}"))
    shutil.copyfile(cm.SCRATCH / "d1_base_S5.csv", cm.SCRATCH / "d1_base_S5p.csv")
    import json
    gates = json.loads((cm.SCRATCH / "i1code/evidence/I1_1b_base.json").read_text())["entries"]
    for e in gates:
        if e["id"].startswith("I1_1b_base.gate."):
            checks.append(dict(check=e["id"].replace("I1_1b_base.", "I1 code gate "), rows="", result=bool(e["value"]), note=e["locator"]))
    cm.write_csv(checks, cm.TABLES / "I2_BASE_CHECKS.csv")
    for c in checks:
        ev.add(f"check.{c['check'][:90]}", bool(c["result"]), "bool", "VERIFIED", "A", "tables/I2_BASE_CHECKS.csv", str(c.get("max_abs_dev_mwh", "")))
    ev.add("base.S5p_sha256", cm.sha256(cm.SCRATCH / "d1_base_S5p.csv"), "sha256", "EXACT", "A", "/home/jin/v4i2/d1_base_S5p.csv")
    ev.write()
    bad = [c for c in checks if not c["result"]]
    print(pd.DataFrame(checks).to_string())
    if bad:
        raise SystemExit("STOP: base reproduction failed: " + "; ".join(c["check"] for c in bad))


if __name__ == "__main__":
    main()
