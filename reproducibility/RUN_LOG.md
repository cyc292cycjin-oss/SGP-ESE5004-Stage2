# 教程运行记录

日期：2026-09-29。本文根据本地日志与检查整理；更详细的原始日志仍保存在本机。

| 阶段 | 操作与证据 | 状态 |
|---|---|---|
| 数据获取 | 修正 tutorial HydroBASINS 分支；数据包规则退出码 0 | 流程通过 |
| 港口输入 | 使用本人下载的 WPI 导出数据；保留转换脚本 | 教程通过，未宣称与论文原始数据一致 |
| 地理形状 | 将 nprocesses 设为 1，降低内存压力 | 规则通过 |
| 网络简化 | 补充新增线路国家属性；处理反向线路聚合时的国家属性 | 规则通过；数据验收仍有问题 |
| 2030 | HiGHS IPM 求解，日志 optimal | 完成 |
| 2040 初次 | HiGHS internal_solver_error；随后读取 objective 出错 | 失败，未证明模型不可行 |
| 2040 重试 | HiGHS simplex，单线程，保留原数值容差；optimal、退出码 0、输入校验通过 | 完成 |
| 2050 | 承接 2040 资产，HiGHS simplex；optimal、退出码 0，2030/2040 校验通过 | 完成 |
| 完成检查 | 三个 NetCDF 可读取、目标值有限、日志 optimal、记录 SHA256 | 基础文件检查通过 |

## 定位原始运行记录

- 2040：logs/reproduction/retry-2040-simplex-20260929-231037/
- 2050：logs/reproduction/resume-2050-simplex-20260929-231717/
- 全部求解日志：logs/baseline-aims-3H-tutorial/solve_network/

## 本轮代码修改

- scripts/retrieve_databundle_light.py：HydroBASINS 数据源分支。
- scripts/prepare_ports.py：教程使用已保存的本地港口数据。
- scripts/add_transmission_projects.py：新增线路缺失国家属性的填充。
- scripts/line_country_clustering.py、scripts/simplify_network.py、scripts/cluster_network.py：方向一致的线路国家属性聚合。
- configs/tutorials/config.sgp-lowmem.yaml：形状处理单进程。
- configs/tutorials/config.sgp-simplex.yaml：求解器算法与线程配置。

修复工具、检查脚本和运行脚本保存在本目录。正式论文版本中是否需要这些修改，必须重新核对，不能直接照搬。

## 未解决事项

网络简化导致母线 765 相关负荷与 1 MW 光伏丢失；版本及数据尚未与论文冻结版本对齐；未开展完整物理一致性与论文指标对照。教程目标值不能直接作为论文成本复现结果。
