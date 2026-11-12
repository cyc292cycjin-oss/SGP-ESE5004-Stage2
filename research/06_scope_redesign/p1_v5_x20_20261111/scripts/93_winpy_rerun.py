"""环境一致性核查（用户 11-12 要求）：本会话中用 Windows 侧 Python 运行过并产出文件（或日志）的命令，在 WSL 项目环境（pypsa-earth）中重跑，
与原产出比对：先逐字节，再 CRLF -> LF 后逐字节，最后按数值（相对差 <= 1e-12；字符串列逐字相同）。重跑产出写在 cache/winpy_rerun/out/，原件不动。
清单（evidence/WINDOWS_PYTHON_COMMANDS.csv 人工核对后）：
  W1 scripts/08_summarise_x10.py（A 段，只打印）             -> logs/08_summarise_x10.log
  W2 scripts/10_s1_boundary.py（A 段，只打印）               -> logs/10_s1_boundary.log
  W3 scripts/23_osm_dup_fetch.py（B 段 2-2；含 OSM API 下载） -> cache/osm/DUP_GROUPS_V5.csv、cache/osm/WAY_TAGS_V5.csv（入库 OSM_WAY_TAGS_V5.csv 是其 LF 副本）
       不重新下载：重复组由同一预建库重算；标签由已存的 API 响应（downloads/osm，OSM_API_LOG.tsv 的顺序）解析，代码与原脚本相同
  W4 scripts/25_ember_solar_cf.py（B 段 Q12）               -> cache/q12/EMBER_SOLAR_CF_{YEARS,SUMMARY}.csv、_LOG.json（入库 *_V5.csv 是其 LF 副本）
  W5 C-2 预检（C 段，内联代码）                               -> evidence/C2_PRECHECK_CLASS_TABLE.csv、C2_PRECHECK.json
  W6 用户点名的 B 段 x20_smoke_eval.py（命令记录显示它在 WSL 运行）-> SMOKE56_OWEN_SIGNS_V5.csv、evidence/SMOKE56_V5_RESULTS.json、SMOKE56_NEW_HYDRO_BUILT.csv
  W7 两次用 Windows Python 做的文本替换（v5_gem_coord_data.py、scripts/36_registry_chain.sh）：核对替换后的文本在、替换前的文本不在
  不能重跑：scripts/24_ngcp_pages.py 与 pypdf 检索（logs/24_ngcp_pages.log、24b_ngcp_terms.log）——WSL 项目环境没有 pypdf / pdftotext。
用法：python 93_winpy_rerun.py   输出 evidence/WINDOWS_PYTHON_RERUN.json、WINDOWS_PYTHON_RERUN.csv"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111"); S = D / "scripts"
WT = Path("/home/jin/wt_v5_x20"); PY = "/home/jin/miniforge3/envs/pypsa-earth/bin/python"
R = D / "cache/winpy_rerun"; O = R / "out"; RS = R / "scripts"
for p in (O, RS):
    p.mkdir(parents=True, exist_ok=True)
TOL = 1e-12
rows = []


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def wslpaths(src: str, extra: dict | None = None) -> str:
    """Windows path literals -> WSL paths (D:\\... -> /mnt/d/..., \\\\wsl.localhost\\Ubuntu\\home\\jin -> /home/jin)"""
    def d(m):
        return '"' + "/mnt/d/" + m.group(1).replace("\\", "/") + '"'
    s = re.sub(r'r"D:\\([^"]*)"', d, src)
    s = re.sub(r'r"\\\\wsl\.localhost\\Ubuntu\\home\\jin\\([^"]*)"', lambda m: '"/home/jin/' + m.group(1).replace("\\", "/") + '"', s)
    for a, b in (extra or {}).items():
        s = s.replace(a, b)
    return s


def cmp_bytes(a: Path, b: Path) -> dict:
    x, y = a.read_bytes(), b.read_bytes()
    return dict(bytes_identical=x == y, identical_after_crlf_to_lf=x.replace(b"\r\n", b"\n") == y.replace(b"\r\n", b"\n"))


def cmp_csv(a: Path, b: Path, sep=",") -> dict:
    r = cmp_bytes(a, b)
    if r["identical_after_crlf_to_lf"]:
        r.update(numeric_equal=True, max_rel_diff=0.0); return r
    A, B = pd.read_csv(a, sep=sep), pd.read_csv(b, sep=sep)
    if list(A.columns) != list(B.columns) or A.shape != B.shape:
        r.update(numeric_equal=False, why=f"shape/columns {A.shape} {B.shape}"); return r
    mx, ok = 0.0, True
    for c in A.columns:
        if pd.api.types.is_numeric_dtype(A[c]) and pd.api.types.is_numeric_dtype(B[c]):
            x, y = A[c].to_numpy(float), B[c].to_numpy(float)
            both = np.isnan(x) & np.isnan(y); d = np.abs(x - y) / np.maximum(np.maximum(np.abs(x), np.abs(y)), 1e-300)
            d = np.where(both | (x == y), 0.0, d); mx = max(mx, float(np.nanmax(d)) if len(d) else 0.0)
            ok &= bool(np.all(d <= TOL))
        else:
            ok &= bool((A[c].astype(str) == B[c].astype(str)).all())
    r.update(numeric_equal=ok, max_rel_diff=mx); return r


def cmp_json(a, b, ignore=(), path="") -> list:
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in ignore:
                continue
            if k not in a or k not in b:
                out.append(f"{path}/{k}: only in one"); continue
            out += cmp_json(a[k], b[k], ignore, f"{path}/{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: list length {len(a)} vs {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            out += cmp_json(x, y, ignore, f"{path}[{i}]")
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if not (a == b or abs(a - b) <= TOL * max(abs(a), abs(b))):
            out.append(f"{path}: {a} vs {b}")
    elif a != b and not (isinstance(a, float) and isinstance(b, float) and np.isnan(a) and np.isnan(b)):
        out.append(f"{path}: {str(a)[:60]} vs {str(b)[:60]}")
    return out


def add(item, original: Path, rerun: Path, result: dict, note=""):
    rows.append(dict(item=item, original=str(original.relative_to(D)) if str(original).startswith(str(D)) else str(original), original_sha256=sha(original),
                     rerun=str(rerun.relative_to(D)), rerun_sha256=sha(rerun), **result, note=note))


def run_script(name: str, src: str, log: Path):
    p = RS / name; p.write_text(src, encoding="utf-8")
    env = dict(os.environ, PYTHONHASHSEED="0")
    with open(log, "w", encoding="utf-8") as f:
        rc = subprocess.run([PY, str(p)], stdout=f, stderr=subprocess.STDOUT, env=env).returncode
    return rc


# W1 / W2: print-only A-segment scripts -> compare the logs
for n, logname in (("08_summarise_x10.py", "08_summarise_x10.log"), ("10_s1_boundary.py", "10_s1_boundary.log")):
    rl = O / logname; rc = run_script("w_" + n, wslpaths((S / n).read_text(encoding="utf-8")), rl)
    res = cmp_bytes(D / "logs" / logname, rl); res["rerun_exit"] = rc
    a_l = (D / "logs" / logname).read_bytes().replace(b"\r\n", b"\n").decode("utf-8", "replace").split("\n"); b_l = rl.read_text(encoding="utf-8").split("\n")
    diff = [(i, x, y) for i, (x, y) in enumerate(zip(a_l, b_l)) if x != y]
    enc_only = all("�" in x for _, x, _ in diff) and len(a_l) == len(b_l)
    res.update(numeric_equal=bool(res["identical_after_crlf_to_lf"] or enc_only), differing_lines=len(diff) + abs(len(a_l) - len(b_l)),
               encoding_only=bool(enc_only and diff), differing_line_numbers=[i + 1 for i, _, _ in diff][:10])
    add("W1" if n.startswith("08") else "W2", D / "logs" / logname, rl, res, "print-only script; stdout log compared")

# W3: OSM duplicate groups (same prebuilt CSVs) and way tags from the stored API responses (no new download)
src = (S / "23_osm_dup_fetch.py").read_text(encoding="utf-8")
head = src.split("log = []; total = 0; recs = []")[0]
offline = wslpaths(head, {'D / "cache/osm"': f'Path("{O}/osm")', 'D / "downloads/osm"': f'Path("{O}/osm_downloads_unused")'}) + f'''
recs = []
L = pd.read_csv("{D}/downloads/osm/OSM_API_LOG.tsv", sep="\\t")
for r in L.itertuples():
    if int(r.status) == 200:
        recs += json.loads(open("{D}/downloads/osm/" + r.file, "rb").read())["elements"]
rows = []
for e in recs:
    t = e.get("tags", {{}})
    rows.append(dict(way=str(e["id"]), version=e.get("version"), timestamp=e.get("timestamp"), power=t.get("power"), voltage=t.get("voltage"),
                     cables=t.get("cables"), circuits=t.get("circuits"), name=t.get("name"), operator=t.get("operator")))
tags = pd.DataFrame(rows)
tags.to_csv(OUT_C / "WAY_TAGS_V5.csv", index=False)
print("tags", len(tags))
'''
rc = run_script("w_23_osm_offline.py", offline, O / "23_osm_offline.log")
for f in ("DUP_GROUPS_V5.csv", "WAY_TAGS_V5.csv"):
    res = cmp_csv(D / "cache/osm" / f, O / "osm" / f); res["rerun_exit"] = rc
    add("W3", D / "cache/osm" / f, O / "osm" / f, res, "recomputed offline (no new OSM request)")
res = cmp_csv(WT / "research_inputs/corridors/OSM_WAY_TAGS_V5.csv", O / "osm/WAY_TAGS_V5.csv"); res["rerun_exit"] = rc
add("W3", WT / "research_inputs/corridors/OSM_WAY_TAGS_V5.csv", O / "osm/WAY_TAGS_V5.csv", res, "committed input = LF copy of the Windows output")

# W4: Ember solar CF (Q12)
src = wslpaths((S / "25_ember_solar_cf.py").read_text(encoding="utf-8"), {'"/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/cache/q12"': f'"{O}/q12"'})
rc = run_script("w_25_ember_solar_cf.py", src, O / "25_ember_solar_cf.log")
for f in ("EMBER_SOLAR_CF_YEARS.csv", "EMBER_SOLAR_CF_SUMMARY.csv"):
    res = cmp_csv(D / "cache/q12" / f, O / "q12" / f); res["rerun_exit"] = rc
    add("W4", D / "cache/q12" / f, O / "q12" / f, res)
    ri = WT / "research_inputs/renewable_v5" / f.replace(".csv", "_V5.csv")
    res = cmp_csv(ri, O / "q12" / f); res["rerun_exit"] = rc
    add("W4", ri, O / "q12" / f, res, "committed input = LF copy of the Windows output")
a, b = json.loads((D / "cache/q12/EMBER_SOLAR_CF_LOG.json").read_text()), json.loads((O / "q12/EMBER_SOLAR_CF_LOG.json").read_text())
diffs = cmp_json(a, b, ignore=("ember",))
add("W4", D / "cache/q12/EMBER_SOLAR_CF_LOG.json", O / "q12/EMBER_SOLAR_CF_LOG.json", dict(bytes_identical=False, identical_after_crlf_to_lf=False, numeric_equal=not diffs, json_diffs=diffs[:5]),
    "the 'ember' path string differs (Windows vs WSL path); ember_sha256 and rows compared")

# W5: C-2 pre-check (same code as the Windows run of 2026-11-12T02:09:33Z)
pre = f'''import json
import pandas as pd
D = "{D}"
c = pd.read_csv(D + "/profiles/onwind_q_c3/S4A_PROFILE_CLASSES.csv"); c = c[c.tech == "onwind"]
ref = pd.read_csv(D + "/evidence/ONWIND_SANITY_V5_B_SEGMENT.csv").set_index("country")
rows = []
for var in ("calibrated_modern", "calibrated_gwa_v5", "calibrated_gwa_v5q"):
    x = c[c.variant == var]
    for cc, d in x.groupby("country"):
        pot = d.potential_mw.sum()
        cfa = (d.potential_mw * d.cf_annual_weighted).sum() / pot
        cfs = (d.potential_mw * d.cf_series_mean).sum() / pot
        r = ref.loc[cc]
        rows.append(dict(variant=var, country=cc, potential_mw=pot, cf_annual_weighted=cfa, cf_series_mean=cfs, reference=r.gwa_gross_over_r,
                         ratio_precheck=cfa / r.gwa_gross_over_r, ratio_series=cfs / r.gwa_gross_over_r))
t = pd.DataFrame(rows)
t["threshold_applies"] = t.potential_mw >= 1000.0
t["in_band"] = t.ratio_precheck.between(0.8, 1.25)
p = t.pivot(index="country", columns="variant", values="ratio_precheck").round(3)
p["network_B_ratio"] = ref.v5_over_reference.round(3); p["potential_GW"] = t[t.variant == "calibrated_gwa_v5q"].set_index("country").potential_mw.div(1000).round(2)
p["applies"] = p.potential_GW >= 1.0
p["q_in_band"] = p.calibrated_gwa_v5q.between(0.8, 1.25)
t.to_csv("{O}/C2_PRECHECK_CLASS_TABLE.csv", index=False, lineterminator="\\n")
fail = p[p.applies & ~p.q_in_band].index.tolist()
json.dump(dict(rule="X20_C2_ONWIND_SUBGRID_SPEC.md sections 5 and 7: potential-weighted cf_annual_weighted of the c3 class table / (GWA IEC3 gross / r) of ONWIND_SANITY_V5.csv; band [0.8, 1.25] for countries with candidate potential >= 1 GW",
               ratios_q=p.calibrated_gwa_v5q.to_dict(), applies=p.applies.to_dict(), out_of_band=fail, passed=not fail), open("{O}/C2_PRECHECK.json", "w"), indent=1)
'''
rc = run_script("w_c2_precheck.py", pre, O / "c2_precheck.log")
res = cmp_csv(D / "evidence/C2_PRECHECK_CLASS_TABLE.csv", O / "C2_PRECHECK_CLASS_TABLE.csv"); res["rerun_exit"] = rc
add("W5", D / "evidence/C2_PRECHECK_CLASS_TABLE.csv", O / "C2_PRECHECK_CLASS_TABLE.csv", res,
    "reference = the ONWIND_SANITY_V5.csv of that time (B segment), now archived as evidence/ONWIND_SANITY_V5_B_SEGMENT.csv")
a, b = json.loads((D / "evidence/C2_PRECHECK.json").read_text()), json.loads((O / "C2_PRECHECK.json").read_text())
diffs = cmp_json(a, b); r5 = cmp_bytes(D / "evidence/C2_PRECHECK.json", O / "C2_PRECHECK.json"); r5.update(numeric_equal=not diffs, json_diffs=diffs[:5], rerun_exit=rc)
add("W5", D / "evidence/C2_PRECHECK.json", O / "C2_PRECHECK.json", r5)

# W6: the B-segment smoke evaluation named by the user (ran in WSL; rerun with another output tag)
env = dict(os.environ, PYTHONHASHSEED="0", X20_SMOKE="smoke56", X20_TAG="_WSLRERUN")
with open(O / "x20_smoke_eval_rerun.log", "w") as f:
    rc = subprocess.run([PY, str(S / "x20_smoke_eval.py")], stdout=f, stderr=subprocess.STDOUT, env=env).returncode
pairs = [(D / "SMOKE56_OWEN_SIGNS_V5.csv", D / "SMOKE56_OWEN_SIGNS_V5_WSLRERUN.csv"), (D / "evidence/SMOKE56_NEW_HYDRO_BUILT.csv", D / "evidence/SMOKE56_NEW_HYDRO_BUILT_WSLRERUN.csv")]
for a_, b_ in pairs:
    res = cmp_csv(a_, b_); res["rerun_exit"] = rc
    tgt = O / b_.name; tgt.write_bytes(b_.read_bytes()); b_.unlink()
    add("W6", a_, tgt, res, "B segment ran in WSL (67b_run.sh); rerun for confirmation")
b_ = D / "evidence/SMOKE56_V5_RESULTS_WSLRERUN.json"; tgt = O / b_.name; tgt.write_bytes(b_.read_bytes()); b_.unlink()
diffs = cmp_json(json.loads((D / "evidence/SMOKE56_V5_RESULTS.json").read_text()), json.loads(tgt.read_text()))
r6 = cmp_bytes(D / "evidence/SMOKE56_V5_RESULTS.json", tgt); r6.update(numeric_equal=not diffs, json_diffs=diffs[:5], rerun_exit=rc)
add("W6", D / "evidence/SMOKE56_V5_RESULTS.json", tgt, r6, "B segment ran in WSL (67b_run.sh); rerun for confirmation")

# W7: text replacements made with Windows Python (interpreter-independent str.replace): new text present, old text absent
g = (WT / "scripts_project/v5_gem_coord_data.py").read_text(encoding="utf-8"); r_ = (S / "36_registry_chain.sh").read_text(encoding="utf-8")
checks = dict(v5_gem_coord_data_new1='for s in ("FLEET_ADDITIONS_2050", "FLEET_ADDITIONS_2050_V5", "FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050")' in g,
              v5_gem_coord_data_new2='src_tab = next((s for s in ("FLEET_ADDITIONS_2050_V5", "FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050")' in g,
              v5_gem_coord_data_old1_absent='FLEET_ADDITIONS_2050{s}.csv", dtype={"gem_unit_id": str}).set_index("gem_unit_id") for s in ("", "_V5")}' not in g,
              registry_chain_placeholders_first="# placeholders first: every *_registry.py assembles all FRAGMENTS / CORRECTIONS" in r_,
              registry_chain_old_block_absent=r_.count("placeholder $f.csv (header only") == 1)
rows.append(dict(item="W7", original="scripts_project/v5_gem_coord_data.py; scripts/36_registry_chain.sh", original_sha256="", rerun="", rerun_sha256="",
                 bytes_identical=None, identical_after_crlf_to_lf=None, numeric_equal=all(checks.values()), note=json.dumps(checks)))

T = pd.DataFrame(rows); T.to_csv(D / "evidence/WINDOWS_PYTHON_RERUN.csv", index=False, lineterminator="\n")
summary = dict(tolerance_rel=TOL, items=int(len(T)), all_equal=bool(T.numeric_equal.fillna(False).astype(bool).all()),
               not_rerunnable=["scripts/24_ngcp_pages.py -> logs/24_ngcp_pages.log", "pypdf term search -> logs/24b_ngcp_terms.log (WSL project env has no pypdf / pdftotext)"],
               rows=T.drop(columns=["original_sha256", "rerun_sha256"]).to_dict("records"))
(D / "evidence/WINDOWS_PYTHON_RERUN.json").write_text(json.dumps(summary, indent=1, default=str) + "\n")
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
print(T[["item", "original", "bytes_identical", "identical_after_crlf_to_lf", "numeric_equal", "max_rel_diff"]].to_string())
print("ALL_EQUAL", summary["all_equal"])
