# V4 W07 G1（马来西亚）进度

- 指令：`work/p1_v4_w07_20261106/V4_W07_INSTRUCTION.md` v1，SHA256 `20d03b692f1d32733f34b04d85c01fb3df1345f95f366a6bf25de36ac7ec7baf`（与 `V4_W07_SHA256.txt` 一致，2026-11-06 核对）；本会话只执行 B-G1 节。
- 分支 `codex/v4-w07-g1-20261106`（起点 `codex/v4-data-20261105` 头 `07e08f38`），worktree `/home/jin/wt_v4_g1`；临时副本 `/home/jin/v4w07_g1/`。
- 交付目录：`work/p1_v4_w07_20261106/G1/` = 仓库 `research/06_scope_redesign/p1_v4_w07_20261106/G1/`。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| G1-A | 复现（偏差 0 MWh）、国家统计基数（UNSD 导出 + SDMX + NEB 2019）、热值（SDMX 26.394）、自备电厂（不触发） | 完成 | `573337eb` |
| G1-B | 实物产量与基年（钢、水泥、原铝、氨复核；化工逐装置；纸浆造纸；石灰与玻璃）、熟料比 | 完成 | `7fdf568c` |
| G1-C | 生物质口径（棕榈压榨闭环） | 完成 | `ff0bff93` |
| G1-D | 合并量化（两套热值）、空间分配 | 完成 | `170a8d53` |
| G1-E | A6 表、报告、证据（审阅包在收尾提交） | 完成 | `7f0254db` |
| 收尾 | 审阅包 `REVIEW_7f0254db.zip`（60 个成员，191,430 B，SHA256 `01380000e13e5fabadd03a0fd9d8ba8bc0b3949798f3787e103e09d19665c3d5`）与成员清单 `REVIEW_ZIP_MANIFEST_7f0254db.txt`、`scripts/v4g1_review_zip.py` | 完成 | 本文件所在提交 |

续做起点：无。全部完成，已推送，等待审阅端审阅。

最后一行（收尾状态）：G1-A `573337eb` → G1-B `7fdf568c` → G1-C `ff0bff93` → G1-D `170a8d53` → G1-E（报告）`7f0254db` → 收尾提交（本文件所在提交，见 `git log -1 codex/v4-w07-g1-20261106`）；推送到 `origin/codex/v4-w07-g1-20261106`，不建 PR、不合并 main、不 force-push。
