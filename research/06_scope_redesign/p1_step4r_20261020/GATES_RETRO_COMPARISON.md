# R8 历史运行重评：V5 标签 vs GATES_V6（只用已导出指标；G2.2 配置子集哈希未导出 → 全部标 pending；G1 缺 PRECISION 的运行标不可计算）

| run | profile | barconvtol | termination | v5_all_passed_solver_tolerances | v5_failed_gates | g1a | g1b | g1c | v6_label | d2_dual_sign_ratio_v5_budget | d2_dual_sign_ratio_v6_budget | d2_within_v6 | d3_gap_ratio | d1_within | d9_terminal_within_v6 | d7_storage_within_v6 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L23 integrated | formal_barrier | 1e-08 | suboptimal | False | A1_A2;A3;B1;B2;B3;B14;B15;A1_A2_S4B;A3_S4B;B3_S4B | — | — | — | not computable (C1 missing) | 3.34e+04 | 3.34e+04 | False | 7.95 | False | True | True |
| L23 disconnected | formal_barrier | 1e-08 | suboptimal | False | A1_A2;A3;B1;B3;B15;A1_A2_S4B;A3_S4B;B3_S4B | — | — | — | not computable (C1 missing) | 6.9e+03 | 6.9e+03 | False | 13.6 | False | True | True |
| L23 disconnected_gap | formal_barrier | 1e-08 | suboptimal | False | A1_A2;A3;B3;B14;B15;A1_A2_S4B;A3_S4B;B3_S4B | — | — | — | not computable (C1 missing) | 6.05e+03 | 6.05e+03 | False | 32.6 | False | True | True |
| S4M-2 A integrated (56x3h) | formal_barrier | 1e-08 | optimal | True | A1_A2;A3;B1;B3 | — | — | — | not computable (C1 missing) | 0.0524 | 0.0524 | True | 0.000188 | True | True | True |
| S4M-2 A disconnected (56x3h) | formal_barrier | 1e-08 | optimal | True | A1_A2;A3;B1 | — | — | — | not computable (C1 missing) | 0.0427 | 0.0427 | True | 8.17e-05 | True | True | True |
| S4M-2 A integrated_nze (56x3h) | formal_barrier | 1e-08 | optimal | True | A1_A2;A3;B1;B3 | — | — | — | not computable (C1 missing) | 0.24 | 0.24 | True | 0.000546 | True | True | True |
| S4M-S2 A integrated rerun (56x3h) | formal_barrier | 1e-08 | optimal | True | A1_A2;A3;B1;B3 | — | — | — | not computable (C1 missing) | 0.0524 | 0.0524 | True | 0.000188 | True | True | True |
| S4N pilot integrated (365x24h) | formal_barrier | 1e-08 | optimal | False | A1_A2;A3;B1;B3;B15;A1_A2_S4B;A3_S4B;B3_S4B | True | True | True | ACCEPTED_LAYER2 (G2.2 pending) | 865 | 865 | False | 1.24 | False | True | True |
| S4N C2 cal integrated (56x3h, 1e-5 t32) | pypsa_eur_default | 1e-05 | optimal | False | A1_A2;A3;B12;A1_A2_S4B;A3_S4B | — | — | — | not computable (C1 missing) | 7.65e+03 | 765 | False | 0.0784 | False | True | True |
| S4N C2 cal disconnected (56x3h) | pypsa_eur_default | 1e-05 | optimal | False | A1_A2;A3;B12;A1_A2_S4B;A3_S4B | — | — | — | not computable (C1 missing) | 7.69e+03 | 769 | False | 0.06 | False | True | True |
| S4N C2 cal integrated_nze (56x3h) | pypsa_eur_default | 1e-05 | optimal | False | A1_A2;A3;B1;B12;A1_A2_S4B;A3_S4B | — | — | — | not computable (C1 missing) | 5.82e+03 | 582 | False | 0.0551 | False | True | True |
| S4O-6 disconnected (365x24h) | formal_barrier | 1e-08 | suboptimal | False | A1_A2;A3;B1;B3;B12;B14;B15;A1_A2_S4B;A3_S4B;B3_S4B | True | True | True | ACCEPTED_LAYER2 (G2.2 pending) | 6.26e+03 | 6.26e+03 | False | 13 | False | True | True |
| S4O-6 disconnected_gap (365x24h) | formal_barrier | 1e-08 | suboptimal | False | A1_A2;A3;B3;B12;B14;B15;A1_A2_S4B;A3_S4B;B3_S4B | True | True | True | ACCEPTED_LAYER2 (G2.2 pending) | 6.57e+03 | 6.57e+03 | False | 66.9 | False | True | True |
| S4O-6 integrated_nze (365x24h) | formal_barrier | 1e-08 | suboptimal | False | A1_A2;A3;B1;B2;B3;B12;B14;B15;A1_A2_S4B;A3_S4B;B3_S4B | True | True | True | ACCEPTED_LAYER2 (G2.2 pending) | 3.86e+03 | 3.86e+03 | False | 3.18 | False | True | True |
| S4Q T8 integrated (56x3h, 1e-6) | formal_barrier_1e6 | 1e-06 | optimal | False | A1_A2;A3;B1;B3;B12;A1_A2_S4B | True | True | True | ACCEPTED_LAYER2 (G2.2 pending) | 10.6 | 10.6 | False | 0.000464 | True | True | True |
| S4Q T8 disconnected (56x3h, 1e-6) | formal_barrier_1e6 | 1e-06 | optimal | False | A1_A2;A3;B1;B3;B12;A1_A2_S4B;A3_S4B | True | True | True | ACCEPTED_LAYER2 (G2.2 pending) | 11.3 | 11.3 | False | 0.000241 | False | True | True |
| S4Q T8 integrated_nze (56x3h, 1e-6) | formal_barrier_1e6 | 1e-06 | optimal | False | A1_A2;A3;B1;B3;B12;A1_A2_S4B;A3_S4B | True | True | True | ACCEPTED_LAYER2 (G2.2 pending) | 13.3 | 13.3 | False | 0.000531 | False | True | True |
| S4Q T16 integrated (56x3h, 1e-6) | formal_barrier_1e6_t16 | 1e-06 | optimal | False | A1_A2;A3;B1;B3;B12;A1_A2_S4B;A3_S4B | True | True | True | ACCEPTED_LAYER2 (G2.2 pending) | 10.9 | 10.9 | False | 0.000371 | False | True | True |
| S4Q T16 disconnected (56x3h, 1e-6) | formal_barrier_1e6_t16 | 1e-06 | optimal | False | A1_A2;A3;B1;B2;B3;B12;B14;A1_A2_S4B;A3_S4B | True | True | True | ACCEPTED_LAYER2 (G2.2 pending) | 19.3 | 19.3 | False | 0.000305 | False | True | True |
| S4Q T16 integrated_nze (56x3h, 1e-6) | formal_barrier_1e6_t16 | 1e-06 | optimal | False | A1_A2;A3;B1;B3;B12;A1_A2_S4B;A3_S4B | True | True | True | ACCEPTED_LAYER2 (G2.2 pending) | 14.1 | 14.1 | False | 0.000434 | False | True | True |

- D2 比值 = 对偶符号误差归一化最大值 / 预算；V5 预算 = 10 × OptimalityTol = 1e-5；V6 预算 = 10 × max(OptimalityTol, BarConvTol)。比值 ≤ 1 为在预算内。
- 未重新加载任何求解后网络、未重建 LP（原则 7）。