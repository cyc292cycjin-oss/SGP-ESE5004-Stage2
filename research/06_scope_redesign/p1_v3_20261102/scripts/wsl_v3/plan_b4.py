"""Supplement 04 section 2.4 item 4 and bookkeeping: screening plan, deployment list, progress, before the solve."""
D = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/"


def patch(f, pairs):
    p = D + f; s = open(p, encoding="utf-8", newline="").read()
    for a, b in pairs:
        assert s.count(a) == 1, a[:70]
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8", newline="").write(s)


patch("RUN_PLAN_SCREEN_V3.md", [
    ("规则见 `V3_RULES.md`，网络登记见 `RUN_PLAN_V3.md` 第 15.1 节，预测见第 11、15.5 节。", "规则见 `V3_RULES.md`，网络登记见 `RUN_PLAN_V3.md` 第 19.1 节，预测见第 11、15.5、17.4、19.5 节。"),
    ("修订桥三步：v2（DFX V1）→ V4 → V5 → V1。全部含 X1b，专线为单向（补充 03）。", "修订桥三步：v2（DFX V1）→ V4 → V5 → V1。全部含 X1b，专线为单向（补充 03），只输送存量电站出力（补充 04，第 179 项）。"),
    ("v3 一体化 LP 比 v2 大 4.0 %（10,376,145 对 9,975,377 行）。", "v3 一体化 LP 比 v2 大 4.0 %（10,377,240 对 9,975,377 行）。"),
    ("实测的 25 核 / 92 GiB（West-B 8470Q）满足下限，但只能串行。\n", "实测的 25 核 / 92 GiB（West-B 8470Q）满足下限，但只能串行。\n\n**补充 04 核对（2026-11-03）：** 第 179 项只给每个时段加 5 列、15 行，365×24h 一体化 +5,475 行（+0.05 %，相对上一版）。第 3、4、5 节的时限、规格、机时和费用都不需要改；干跑峰值见 `V3_REPORT_SUPPLEMENT04.md`。\n"),
    ("| `LA_EXPORT_UTILISATION.csv` | LA 各国家对，APG 线路与专线分列：可用容量、出口、进口、平均利用率、满载小时 | 第 2.4 节 |\n", "| `LA_EXPORT_UTILISATION.csv` | LA 各国家对，APG 线路与专线分列：可用容量、出口、进口、平均利用率、满载小时。第 179 项后专线年均利用率的结构上界约 50 %（`evidence/SOURCE_LINE_BOUND_V3.json`，只含水电、径流、风电），按这个上界读 | 第 2.4 节 |\n"),
])
patch("V3_DEPLOY_FILES.md", [
    ("## 1. 两边共用\n", "**补充 04 更新（2026-11-03）：** 第 179 项（专线只输送存量电站出力）后网络再次重建，现行登记见 `RUN_PLAN_V3.md` 第 19 节，现行筛查包是 `work/p1_v3_20261102/screen_package_v3_bound/`，`screen_package_v3/`、`screen_package_v3_oneway/` 已作废，保留不用。\n\n## 1. 两边共用\n"),
])
patch("V3_PROGRESS.md", [
    ("## 恢复点", """| 补充 04 代码、规则、测试 | 完成：源母线、源链路、静态检查、第 179 项测试；规则 `V3_RULES.md` 第 2.4 节 | `6e92d7b6` |
| 补充 04 重建与登记 | 完成：7 个网络，静态与路径检查通过，完全隔离逐字节相同；容量表与预测在 `RUN_PLAN_V3.md` 第 19 节 | 构建 `6e92d7b6`，登记本次提交 |

## 恢复点"""),
    ("补充 04 未开始，按 `V3_REVIEW_DECISIONS_SUPP03.md` 第 2 节在新会话执行，先读 `V3_HANDOFF_SUPP04.md`。额度：本机 Gurobi 2 次，计算 2 小时，磁盘 20 GB。", "补充 04：运行 `bash /home/jin/v3/smoke_s4.sh --confirmed <确认时间>`（用户已答复不必再问，见 `RUN_PLAN_V3.md` 第 19.3 节），之后 `dry_s4.sh`、`pkg_s4.sh`、全量测试、`V3_REPORT_SUPPLEMENT04.md`。"),
    ("补充 03 为 2 / 2，本机计算约 1.6 小时 / 2 小时，磁盘约 9.5 GB / 20 GB。", "补充 03 为 2 / 2，本机计算约 1.6 小时 / 2 小时，磁盘约 9.5 GB / 20 GB。补充 04 为 0 / 2，上限本机计算 2 小时、磁盘 20 GB。"),
])
print("ok")
