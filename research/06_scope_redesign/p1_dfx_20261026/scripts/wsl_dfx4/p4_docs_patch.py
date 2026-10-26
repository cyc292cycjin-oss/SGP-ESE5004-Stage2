"""DFX phase 4 close-out: (1) DFX_PROGRESS.md phase-4 row -> done (no instance name), (2) DFX_EVIDENCE.json gets a phase4 entry from
DFX_PHASE4_RESULTS.json, (3) /home/jin/dfx3/sync_work.sh also copies the phase 4 report, evidence/phase4 and scripts/wsl_dfx4.
    python p4_docs_patch.py"""
import json
from pathlib import Path

D = Path("/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026")
# (1) progress row
p = D / "DFX_PROGRESS.md"; t = p.read_text()
lines = t.splitlines(); n = 0
row = ("| 阶段 4（AutoDL 365×24h 筛查） | 完成 | （本提交） | 用户 2026-10-27 会话授权\"授权阶段 4\"（第三批同一实例 West-B，25 核 8470Q / 92 GB，数据盘 100 GB；"
       "连接方式只在会话中，不写入文件）+ 无人值守补充授权。模型在阶段 4 授权前由用户切换为 Opus 5.5（`/model claude-opus-5-5`，约 2026-10-27 03:45 SGT）。"
       "七个替身测试 76 passed / 1 skipped / 0 failed → 上传（20 / 20 SHA256 OK）→ 复用已有环境（ENV_EXACT_MATCH 284 / 284）→ 许可 scp → 预检 OK → "
       "串行 V1 optimal（5,963 s，335 次）、V2 optimal（1,488 s，127 次），GATES_V6 均 ACCEPTED_LAYER2（本批参照重评），无停批；"
       "**B6 14.6153 bn EUR（16.6608 bn USD2020），ΔB6 +3.3155（一阶预测 +3.0596）**，燃料舱受益 −0.237；结果包下载并核对 SHA256，"
       "云端许可删除（`/root/.gurobi` 为空）；`DFX_REPORT_PHASE4.md`、`evidence/phase4/`；辅助脚本 `/home/jin/dfx4/`（镜像 `scripts/wsl_dfx4/`）；"
       "实例目录 `/root/autodl-tmp/dfx_v8`（第三批 / S1 文件不动）；关机见报告第 9 节。**停止，等待审阅** |")
for i, l in enumerate(lines):
    if l.startswith("| 阶段 4（AutoDL 365×24h 筛查）"):
        lines[i] = row; n += 1
assert n == 1, n
p.write_text("\n".join(lines) + "\n")
assert "<INSTANCE>" not in p.read_text()
# (2) evidence index
e = D / "DFX_EVIDENCE.json"; ev = json.loads(e.read_text())
r = json.loads((D / "evidence/phase4/DFX_PHASE4_RESULTS.json").read_text())
ev["phase4"] = dict(
    report="DFX_REPORT_PHASE4.md", evidence_dir="evidence/phase4", scripts="scripts/wsl_dfx4",
    packs={"results_light_final_20261026T223024Z.tar.gz": dict(bytes=4626419, sha256="713b23b9b595b8e537de05e73f308d6a5229bd8ec02baf9b5f0db77b0f4ce3f7"),
           "results_full_final_20261026T223024Z.tar.gz": dict(bytes=355721421, sha256="12fe09043e9b6274d8829648ef48938c4e51b9c6cc15ef05c45dfb5e6cc9d10b")},
    packs_location="work/p1_dfx_20261026/cloud_results/final_20261026T223024Z (not committed)",
    runs={k: {x: v[x] for x in ("termination", "objective_eur", "solve_seconds", "barrier_iterations", "peak_rss_gib", "v6", "v6_provisional", "owen_usable")}
          for k, v in r["runs"].items()},
    b6=r["b6"], delta=r["delta"],
    pre_upload_tests="76 passed / 1 skipped / 0 failed, 1,342 s, HEAD 7e03a3b1 (evidence/phase4/instance/PRE_UPLOAD_TESTS.log)",
    licence_deleted_sgt="2026-10-27 06:33:14", gurobi_dir_entries_after=0,
    model_switch="user /model claude-opus-5-5 before the phase 4 authorisation (about 2026-10-27 03:45 SGT); effort level not observable",
)
e.write_text(json.dumps(ev, indent=1, ensure_ascii=False) + "\n")
# (3) sync script
s = Path("/home/jin/dfx3/sync_work.sh"); st = s.read_text()
if "DFX_REPORT_PHASE4.md" not in st:
    st = st.replace("DFX_REPORT_PHASE3.md DFX_EVIDENCE.json", "DFX_REPORT_PHASE3.md DFX_REPORT_PHASE4.md DFX_EVIDENCE.json")
    st = st.replace("cp $D/evidence/*.json $W/evidence/ 2>/dev/null",
                    "cp $D/evidence/*.json $W/evidence/ 2>/dev/null\nmkdir -p $W/evidence/phase4 $W/scripts/wsl_dfx4; cp -r $D/evidence/phase4/. $W/evidence/phase4/; cp -r $D/scripts/wsl_dfx4/. $W/scripts/wsl_dfx4/ 2>/dev/null")
    s.write_text(st)
assert "DFX_REPORT_PHASE4.md" in s.read_text() and "wsl_dfx4" in s.read_text()
print("progress row replaced:", n, "| evidence keys:", list(ev["phase4"].keys())[:6], "| sync patched")
