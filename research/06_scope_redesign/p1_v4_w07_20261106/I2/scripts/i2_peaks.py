"""I2 section 3 item 3: composite 'node x carrier' curve weights and the ASEAN industrial peak with the v4 sub-sector energies (G5 recommended
variant MAIN and the G5 sensitivities), re-using G5 scripts/g5_peaks.py. Read only, no solve.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i2_peaks.py

g5_peaks.py and g5_profiles.py are copied to /home/jin/v4i2/g5/code with one edit: V3_KEY gains the v4 sub-sectors (pulp_paper ->
pulp_paper, hvc / hvc_new_plants -> ethylene, methanol / methanol_new_plants -> methanol, glass / lime -> glass_lime, alumina -> alumina,
copper -> copper, pulp_paper_new_lines -> pulp_paper; the G5 PROFILE_INDEX has all these keys). Inputs are staged in scratch folders so
that no G5 deliverable is overwritten:
  --repo  /home/jin/v4i2/g5/repo: research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv = I2 tables/I2_V4_SUBSECTOR_CARRIER.csv
          (I2 final, case main); INDUSTRY_NODE_SHARES_V3.csv = repository table + the ID node shares of the new sub-sectors (I2 rule);
          transport_v3/EV_NODE_TIMEZONE_V3.csv copied;
  --s0    /home/jin/v4i2/g5/s0: evidence/V3_DISPERSED_BY_UNSD_ROW.csv = I2 tables/I2_V4_DISPERSED_BY_UNSD_ROW.csv (I2 final dispersed rows);
  --g5    /home/jin/v4i2/g5/work: PROFILES_8760.parquet, PROFILE_INDEX.csv, WEEK_TEMPLATES_168.csv copied from G5 (read only);
  --network the v3.1 F1 network used by G5 (integrated_2920_3h_unsolved.nc, SHA256 8b5fd663...; base electricity series and static loads).
The run is repeated with the v3 composition (repository tables, G5's own inputs) as the control: it must reproduce G5's
evidence/G5_PEAK_IMPACT_ASEAN.csv. Writes tables/I2_PEAK_IMPACT_ASEAN.csv, tables/I2_PEAK_IMPACT_BY_COUNTRY.csv, tables/I2_CURVE_WEIGHTS.csv
(node x carrier weights of the curve keys, I2 final), evidence/I2_peaks.json.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i2_common as cm   # noqa: E402
from i2_tables import Nodes   # noqa: E402

G5 = cm.G["G5"]
SC = cm.SCRATCH / "g5"
NET = Path("/home/jin/v3fix/dry_20261105T115859Z/pkg/networks/integrated_2920_3h_unsolved.nc")
OLD = 'V3_KEY = {"steel": "steel", "cement": "cement", "ammonia": "ammonia", "nonferrous_nickel": "nickel", "nonferrous_aluminium_primary": "aluminium_primary",\n          "nonferrous_alumina": "alumina", "nonferrous_copper": "copper", "other": "other"}'
NEW = OLD[:-1] + ',\n          # I2 copy: v4 sub-sectors -> G5 curve keys\n          "pulp_paper": "pulp_paper", "pulp_paper_new_lines": "pulp_paper", "hvc": "ethylene", "hvc_new_plants": "ethylene", "methanol": "methanol",\n          "methanol_new_plants": "methanol", "glass": "glass_lime", "lime": "glass_lime", "alumina": "alumina", "copper": "copper"}'
NEWKEYS = ["pulp_paper", "pulp_paper_new_lines", "hvc", "hvc_new_plants", "methanol", "methanol_new_plants", "glass", "lime", "alumina", "copper"]


def stage(tag: str, comp: Path | None, disp: Path | None, ns_extra: pd.DataFrame | None):
    root = SC / tag
    if root.exists():
        shutil.rmtree(root)
    (root / "repo/research_inputs/industry_v3").mkdir(parents=True); (root / "repo/research_inputs/transport_v3").mkdir(parents=True)
    (root / "s0/evidence").mkdir(parents=True); (root / "work/evidence").mkdir(parents=True)
    shutil.copyfile(comp or cm.IND_V3 / "INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv", root / "repo/research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv")
    ns = pd.read_csv(cm.IND_V3 / "INDUSTRY_NODE_SHARES_V3.csv")
    if ns_extra is not None:
        ns = pd.concat([ns, ns_extra], ignore_index=True)
    ns.to_csv(root / "repo/research_inputs/industry_v3/INDUSTRY_NODE_SHARES_V3.csv", index=False, lineterminator="\n")
    shutil.copyfile(cm.REPO / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv", root / "repo/research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv")
    shutil.copyfile(disp or (cm.S2W / "evidence/V3_DISPERSED_BY_UNSD_ROW.csv"), root / "s0/evidence/V3_DISPERSED_BY_UNSD_ROW.csv")
    for f in ("PROFILES_8760.parquet", "PROFILE_INDEX.csv", "WEEK_TEMPLATES_168.csv"):
        shutil.copyfile(G5 / f, root / "work" / f)
    return root


def run(root: Path) -> pd.DataFrame:
    code = SC / "code"
    r = subprocess.run([cm.PY, str(code / "g5_peaks.py"), "--s0", str(root / "s0"), "--repo", str(root / "repo"), "--network", str(NET), "--g5", str(root / "work")],
                       capture_output=True, text=True, env=cm.ENV, cwd=code)
    (root / "log.txt").write_text(r.stdout + "\n--- stderr\n" + r.stderr)
    if r.returncode:
        raise SystemExit(f"STOP: g5_peaks.py failed: {r.stderr[-2000:]}")
    return pd.read_csv(root / "work/evidence/G5_PEAK_IMPACT_ASEAN.csv"), pd.read_csv(root / "work/evidence/G5_PEAK_IMPACT.csv")


def main():
    ev = cm.Evidence("I2_peaks")
    (SC / "code").mkdir(parents=True, exist_ok=True)
    src = (G5 / "scripts/g5_peaks.py").read_text()
    if src.count(OLD) != 1:
        raise SystemExit("STOP: V3_KEY not found once in g5_peaks.py")
    (SC / "code/g5_peaks.py").write_text(src.replace(OLD, NEW)); shutil.copyfile(G5 / "scripts/g5_profiles.py", SC / "code/g5_profiles.py")
    ev.add("code.g5_peaks_copy", dict(source_sha256=cm.sha256(G5 / "scripts/g5_peaks.py"), copy_sha256=cm.sha256(SC / "code/g5_peaks.py"), net_sha256=cm.sha256(NET)), "file",
           "VERIFIED", "-", "G5 scripts copied; only V3_KEY extended")
    # ---- control: v3 composition must reproduce G5
    ctl = stage("v3_control", None, None, None); A3, C3_ = run(ctl)
    ref = pd.read_csv(G5 / "evidence/G5_PEAK_IMPACT_ASEAN.csv")
    m = A3.merge(ref, on="variant", suffixes=("_i2", "_g5"))
    dev = float((m.ac_fixed_peak_3h_gw_i2 - m.ac_fixed_peak_3h_gw_g5).abs().max())
    ev.add("gate.v3_control_reproduces_G5_ASEAN_peaks", dev, "GW (max abs)", "EXACT", "-", "G5 evidence/G5_PEAK_IMPACT_ASEAN.csv vs the I2 control run")
    # ---- I2 final composition
    N = Nodes(); comp = pd.read_csv(cm.TABLES / "I2_V4_SUBSECTOR_CARRIER.csv")
    extra = []
    for k in NEWKEYS:
        if ((comp.country == "ID") & (comp.subsector == k)).any():
            sh, s = N.shares("ID", k, "electricity")
            extra += [dict(country="ID", subsector=k, node=n, share=x) for n, x in sorted(sh.items())]
    v4 = stage("v4_final", cm.TABLES / "I2_V4_SUBSECTOR_CARRIER.csv", cm.TABLES / "I2_V4_DISPERSED_BY_UNSD_ROW.csv", pd.DataFrame(extra))
    A4, C4 = run(v4)
    out = A3.merge(A4, on="variant", suffixes=("_v3", "_v4"))
    out.to_csv(cm.TABLES / "I2_PEAK_IMPACT_ASEAN.csv", index=False, float_format="%.4f", lineterminator="\n")
    bc = C3_[C3_.variant.isin(["FLAT", "MAIN"])].merge(C4[C4.variant.isin(["FLAT", "MAIN"])], on=["country", "variant"], suffixes=("_v3", "_v4"))
    keep = ["country", "variant"] + [c for c in bc.columns if any(c.startswith(p) for p in ("annual_twh", "peak_3h_gw", "ac_fixed_load_peak_change_gw", "ac_fixed_load_peak_change_pct", "peak_over_mean_3h"))]
    bc[keep].to_csv(cm.TABLES / "I2_PEAK_IMPACT_BY_COUNTRY.csv", index=False, float_format="%.4f", lineterminator="\n")
    # ---- curve weights (node x carrier x curve key), I2 final
    comp_c = pd.read_csv(v4 / "work/evidence/G5_INDUSTRY_COMPOSITION.csv")
    comp_c.to_csv(cm.TABLES / "I2_CURVE_WEIGHTS.csv", index=False, float_format="%.3f", lineterminator="\n")
    for r in out.itertuples():
        ev.add(f"asean.{r.variant}", dict(v3_ac_peak_change_gw=r.ac_fixed_peak_change_gw_v3, v4_ac_peak_change_gw=r.ac_fixed_peak_change_gw_v4,
                                          v3_industry_peak_gw=r.industry_peak_3h_gw_v3, v4_industry_peak_gw=r.industry_peak_3h_gw_v4, v4_industry_mean_gw=r.industry_mean_gw_v4),
               "GW", "PROPOSED", "C", "tables/I2_PEAK_IMPACT_ASEAN.csv", "3 h, coincident; change vs the flat curve of the same energy")
    ev.write()
    pd.set_option("display.width", 220)
    print("control dev GW", dev); print(out.round(3).to_string())


if __name__ == "__main__":
    main()
