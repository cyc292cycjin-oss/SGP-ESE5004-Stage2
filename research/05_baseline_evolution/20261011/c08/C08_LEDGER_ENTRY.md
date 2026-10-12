## C08 日模型根因核实：零成本解耦资源块（2026-10-13）

**C08_ROOT_CAUSE_IDENTIFIED_READ_ONLY。** 由 Claude 在用户授权的只读范围内完成；新增优化、构模、AutoDL 操作均为 0；V4/Scheme A/C01R/D/R/成本及历史结果均未改动。G6-05 PAUSED_BY_USER。

- EXACT：807 个 fixed resource Store 与 807 个 final-energy meter Link 组成块：884,472 列、2,203,217 行。该块与其余 LP 完全解耦，块内成本全为 0；系数仅 ±1/−24，无列级界。块内 V4 失败与求解器无关。
- EXACT：块可行性证书。用 LP 的 binary64 数据逐行有理数核验全部 2,203,217 行，违约为 0。385 组 D≤Q；LP 坐标下的余量为 1.08e−19 至 4.13e−16，物理值 = 2^k × LP 值（k∈[0,28]），与 SCHEME_A_DAILY_EXACT_GROUPS 精确一致。
- VERIFIED：以下失败全部在块内——C06 的 243 条与 C07A 的 1 条矩阵失败行；C07A 的 12,045 项对偶符号/自由 RC；|y|>1e9 的 316,102 行（块内最大 4.3e14，块外最大 8.2e5）。C03/C06/C07A 的 stationarity 失败（4304/3336/3353 列）全部在块外。C07 实际改变的 884,472 个 D 和 2,203,217 个 R（新指数减原指数）全部位于块内，块外为 0。
- VERIFIED（非证书）：主 LP 对偶修复后，残差列为 5,326 列（Line-s 3376、Link-p 1931、p_nom 19），有限部分相对差距约 4.8e−7；严格下界未取得。
- INFERENCE：块余量远低于 FeasibilityTol 1e−6，是巨大对偶、多账户组敏感性的成因，也可能是 C07B Status 3 的成因（未证明）。
- PROPOSED（待授权）：方案 (a) 精确分解。块用精确有理数解，只对主 LP 做一次 Barrier+Crossover 求解，合并后按原 V4 全量验收，并预先写定判定规则。方案 (b)（修改 Scheme A 的余量）严格劣于 (a)。建议暂缓 C07 分层准入指令。
- 交付：`work/c08_block_decomposition_20261013/`，以及 `outputs/C08_BLOCK_DECOMPOSITION_REVIEW.zip`（含成员 SHA/CRC 清单）。GitHub 尚未推送：本会话 GitHub 账户待关联。
