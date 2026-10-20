# GATES_V6 说明（补充 01 §4；不修改 `GATES_V6.md`，其 SHA256 保持 `5c0aa8b8ed322b75a63879fccfc19559606a0ad743ecafee3addfcbfe04fd7f9`）

## 1. 说明对象

`GATES_V6.md` §3 的诊断 D2（对偶符号 / 平稳性残差）用预算 `k × max(OptimalityTol, BarConvTol)`，k = 10。重评（`GATES_RETRO_COMPARISON.csv`，只读导出指标）显示：在 barrier 不做 crossover（`Crossover = 0`）的运行上，D2 几乎总是"超预算"，而验收判据 G1（= C1 (a)(b)(c)）全部通过。本说明记录这一现象的实测量级与解释，并说明为何保持 k = 10。

## 2. 实测（`v5_dual_sign_normalized_max` = 归一化对偶符号误差最大值；VERIFIED，来自各运行的 `kkt_summary.json`）

| 运行组 | 分辨率 / 状态 | BarConvTol | 对偶符号误差最大值 | 误差 / BarConvTol | D2 比值（V6 预算） |
|---|---|---|---|---|---|
| S4M-2 档案 A ×3 + 复跑 | 56×3h，OPTIMAL | 1e-8 | 4.3e-7 – 2.4e-6 | 43 – 240 | 0.04 – 0.24（在预算内） |
| S4Q T8 / T16 ×6 | 56×3h，OPTIMAL | 1e-6 | 1.06e-4 – 1.93e-4 | 106 – 193 | 10.6 – 19.3 |
| S4N C2 标定 ×3 | 56×3h，1e-5 t32 | 1e-5 | 5.8e-2 – 7.7e-2 | 5,800 – 7,700 | 582 – 769 |
| S4N 试点 | 365×24h，OPTIMAL | 1e-8 | 8.6e-3 | 8.6e5 | 865 |
| S4O-6 ×3 | 365×24h，SUBOPTIMAL | 1e-8 | 3.9e-2 – 6.6e-2 | 3.9e6 – 6.6e6 | 3,863 – 6,571 |
| L23 ×3 | 365×24h，SUBOPTIMAL / TIME_LIMIT | 1e-8 | 6.0e-2 – 3.3e-1 | 6.0e6 – 3.3e7 | 6,047 – 33,378 |

读法：对偶预算 = 10 × max(OptimalityTol 1e-6, BarConvTol)，即 1e-5（档案 A、1e-6 候选）或 1e-4（1e-5 档案）；D2 比值 = 误差 / 预算。

## 3. 解释（INFERENCE）

1. **barrier 无 crossover 的解是内点，不是顶点。** Gurobi 的 BarConvTol 只约束原始目标与对偶目标的相对间隙（Gurobi Optimizer Reference, Parameters: BarConvTol），不直接约束返回解的逐行对偶可行性；OptimalityTol 只在 simplex / crossover 后对约化成本生效。因此内点解的"对偶符号误差"与 BarConvTol 之间没有文档给出的固定倍数。
2. **56×3h 优化成功的运行上，误差约为 BarConvTol 的 40–240 倍**（S4M-2 在 1e-8、S4Q 在 1e-6 两档一致），即 k ≈ 100 量级。
3. **365×24h 的解无论状态如何，误差都在 1e-2 量级**（试点 OPTIMAL 8.6e-3；S4O-6 / L23 SUBOPTIMAL 4e-2–3e-1），与 BarConvTol 的倍数达 1e5–1e7：误差随问题规模与条件数增长，不再由 BarConvTol 决定；1e-5 档案的 56×3h 标定也在 6–8e-2。
4. 这些运行的 G1（C1 (a) 目标值、(b)(c) 分国差额与结构）全部通过（有 PRECISION 文件的 10 次），说明目标函数层面的精度已足够回答研究问题（第 119 项），逐行对偶误差对分摊结果的影响在 C1 的阈值之内。

## 4. 决定（第 129 项，补充 01 §4）

- **保持 k = 10，不修改 `GATES_V6.md`。** D2 是诊断，不参与验收；验收只看 G1（= C1）与 G2 结构检查。
- 报告中的写法：对 365×24h 内点解，D2"超预算"属已知现象，报告 D2 比值与本说明的量级表即可，不作"失败"解读；若某次运行的 D2 比值超出同组历史范围一个数量级以上（例如 365×24h 档案 A 运行 > 1e5），作为异常提示登记并复核日志，但仍不改变标签。
- 若日后要让 D2 在"优化成功的 56×3h 运行"上通常落在预算内，k 应取 100（第 3 节第 2 点）；这需要新的 V6.1 定义与独立提交，不在本步范围。

## 5. 文件

- 定义：`GATES_V6.md`（提交 d45955ea，SHA256 同上）。
- 重评：`GATES_RETRO_COMPARISON.csv/.md`（`scripts/s4r_r8_retro.py`）。
- 本说明：`GATES_V6_NOTES.md`（补充 01，2026-10-20）。
