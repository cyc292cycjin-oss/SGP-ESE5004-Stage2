"""W08 section 1: reference engine = the I2 engine (work/p1_v4_w07_20261106/I2/scripts) with the two changes of decision 211 (instruction
section 0), copied with asserted text edits (each edit point must occur exactly once). Nothing in the repository or in the I2 folder is written.

    /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_ref_setup.py

Edits (copies in scripts/ref/):
  i2_common.py  SCRATCH from the environment (W08_REF_SCRATCH; one scratch folder per reference run, so two runs can go in parallel);
                I2 = the I2 delivery folder (read only: session deliverables through W07 / G); TABLES / EVID / FIGS -> the scratch folder.
  i2_engine.py  m08b scratch patch: decision 211 item 1 - the residue anchor alignment (decision 210 item 4 a) applies in every anchor mode:
                'ras' (IIa) refits RAS with the residue still in the industry seed of the countries whose balance contains it, then lowers the
                industry anchor by residue x multiplier; 'frozen' (IIb) lowers the frozen industry anchor the same way ('fixedcol' = IId: I2 code).
  i2_chain.py   S1 anchor mode from W08_ANCHOR_MODE (ras = v4 main, decision 211 item 1; fixedcol = IId); S2: W08_ID_PAPER_FW = residue
                (decision 211 item 2, main): the ID fuelwood of the SDMX paper row (1214G) is a self-produced residue (a) - out of the seed and the
                cache, and the (b) item outside the balance keeps only the non-paper part (= I2 sensitivity id_paper_fw_selfuse); purchased = I2.
The I2 scratch inputs (d1_base_S0 / S5p, SDMX capsule, i1code, BIOMASS_POTENTIAL_2050_I2.csv) are copied into each scratch folder.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
I2S = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106/I2/scripts")
REF = HERE / "ref"
I2SCRATCH = Path("/home/jin/v4i2")
SCR = {"main": Path("/home/jin/v4w08/ref_main"), "iid": Path("/home/jin/v4w08/ref_iid"), "i2chk": Path("/home/jin/v4w08/ref_i2chk")}

EDITS = {
    "i2_common.py": [
        ('I2 = Path(__file__).resolve().parents[1]', 'I2 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106/I2")   # W08 copy: I2 delivery folder, read only'),
        ('TABLES = I2 / "tables"', 'import os as _w8os\nSCRATCH = Path(_w8os.environ["W08_REF_SCRATCH"])   # W08 copy: one scratch folder per reference run\nTABLES = SCRATCH / "tables"'),
        ('EVID = I2 / "evidence"', 'EVID = SCRATCH / "evidence"'),
        ('FIGS = I2 / "figures"', 'FIGS = SCRATCH / "figures"'),
        ('SCRATCH = Path("/home/jin/v4i2")                      # scratch copies (instruction section 7)', '# W08 copy: SCRATCH is set above from W08_REF_SCRATCH'),
    ],
    "i2_engine.py": [
        ("""            tfa[c] = {s: A_tfec[c] * _i1w[s] / _i1ws for s in SECTORS}
'''""",
         """            tfa[c] = {s: A_tfec[c] * _i1w[s] / _i1ws for s in SECTORS}
    if _i1os.environ.get("I2_ANCHOR_ADJ") and _i1m in ("ras", "frozen"):
        # ---- W08 scratch-only patch (decision 211 item 1): the residue anchor alignment applies in every anchor mode. 'ras' (IIa): RAS refit
        #      with the residue still in the industry seed of the countries whose national balance contains it (same row / column targets);
        #      then, as in IId, the industry anchor falls by residue x the industry multiplier (other sector anchors and every multiplier kept)
        _w8adj = {c: float(v) for c, v in json.load(open(_i1os.environ["I2_ANCHOR_ADJ"])).items() if c in ASEAN10 and v}
        if _i1m == "ras":
            _w8seed = np.array([[t19[c][s] + (_w8adj.get(c, 0.0) if s == "Industry" else 0.0) for s in SECTORS] for c in ASEAN10])
            _w8X, _w8it, _w8er, _w8ec = ras_split(_w8seed, row_t, col_t)
            for _w8i, c in enumerate(ASEAN10):
                tfa[c] = {s: float(_w8X[_w8i, j]) for j, s in enumerate(SECTORS)}
        for c, _w8r in _w8adj.items():
            tfa[c] = dict(tfa[c]); tfa[c]["Industry"] = tfa[c]["Industry"] / (t19[c]["Industry"] + _w8r) * t19[c]["Industry"]
'''"""),
    ],
    "i2_chain.py": [
        ("import i2_items as IT    # noqa: E402",
         "import i2_items as IT    # noqa: E402\nimport os as _w8os   # noqa: E402\nW08_ANCHOR_MODE = _w8os.environ.get('W08_ANCHOR_MODE', 'ras')   # W08 copy: ras = v4 main (decision 211 item 1), fixedcol = IId\n"
         "W08_ID_PAPER_FW = _w8os.environ.get('W08_ID_PAPER_FW', 'residue')   # W08 copy: residue = decision 211 item 2 (main), purchased = I2 main"),
        ("        self.cache_a = IT.build_cache(c, drop=self.a_drop, scale={(\"ID\", IT.FW_CODE): self.fw_scale})",
         "        self.cache_a = IT.build_cache(c, drop=self.a_drop, scale={(\"ID\", IT.FW_CODE): self.fw_scale})\n"
         "        # W08 copy (decision 211 item 2): the ID fuelwood of the SDMX paper row 1214G as a self-produced residue (a); share of the non-paper rows\n"
         "        fwc = c[(c.country == \"ID\") & (c.code == IT.FW_CODE) & (c.tx != \"121\")]\n"
         "        self.paper_fw_sdmx_mwh = float(fwc[fwc.tx == \"1214G\"].mwh.sum()); self.paper_fw_sdmx_km3 = float(fwc[fwc.tx == \"1214G\"].quantity.sum())\n"
         "        self.sh_nes = float(fwc[fwc.tx != \"1214G\"].mwh.sum()) / float(fwc.mwh.sum())\n"
         "        self.cache_a_paper = IT.build_cache(c, drop=set(self.a_drop) | {(\"ID\", IT.FW_CODE, \"1214G\")}, scale={(\"ID\", IT.FW_CODE): self.fw_scale})"),
        ("        c = dict(c); c.update(d1=I.B.copy(), d1_s0=I.S0, anchor_mode=\"fixedcol\", cache=I.cache_full); return c",
         "        c = dict(c); c.update(d1=I.B.copy(), d1_s0=I.S0, anchor_mode=W08_ANCHOR_MODE, cache=I.cache_full); return c"),
        ("        c[\"ats_add\"] = list(c.get(\"ats_add\", [])) + [(\"ID\", \"biomass\", I.idb_main, I.m_v3[\"ID\"])]   # 210 item 4 b: reading I = v3 ATS industry multiplier\n"
         "        c[\"cache\"] = I.cache_a",
         "        if W08_ID_PAPER_FW == \"residue\":   # W08 copy: decision 211 item 2 (= I2 sensitivity id_paper_fw_selfuse)\n"
         "            c[\"ats_add\"] = list(c.get(\"ats_add\", [])) + [(\"ID\", \"biomass\", I.idb_main * I.sh_nes, I.m_v3[\"ID\"])]\n"
         "            c[\"cache\"] = I.cache_a_paper\n"
         "        else:\n"
         "            c[\"ats_add\"] = list(c.get(\"ats_add\", [])) + [(\"ID\", \"biomass\", I.idb_main, I.m_v3[\"ID\"])]   # 210 item 4 b: reading I = v3 ATS industry multiplier\n"
         "            c[\"cache\"] = I.cache_a"),
    ],
    "i2_items.py": [],
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    REF.mkdir(parents=True, exist_ok=True)
    rec = {}
    for f, edits in EDITS.items():
        src = (I2S / f).read_text()
        for old, new in edits:
            n = src.count(old)
            if n != 1:
                raise SystemExit(f"STOP: edit point in {f} occurs {n} times: {old[:80]}")
            src = src.replace(old, new)
        (REF / f).write_text(src)
        rec[f] = dict(source=str(I2S / f), source_sha256=sha(I2S / f), copy_sha256=sha(REF / f), edits=len(edits))
    for name, s in SCR.items():
        s.mkdir(parents=True, exist_ok=True)
        for f in ("d1_base_S0.csv", "d1_base_S5p.csv", "SDMX_2019_CAPSULE.json", "BIOMASS_POTENTIAL_2050_I2.csv"):
            shutil.copyfile(I2SCRATCH / f, s / f)
        if (s / "i1code").exists():
            shutil.rmtree(s / "i1code")
        shutil.copytree(I2SCRATCH / "i1code", s / "i1code")
        rec[f"scratch_{name}"] = {f: sha(s / f) for f in ("d1_base_S0.csv", "d1_base_S5p.csv", "SDMX_2019_CAPSULE.json", "BIOMASS_POTENTIAL_2050_I2.csv")}
    (REF / "REF_SETUP.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
