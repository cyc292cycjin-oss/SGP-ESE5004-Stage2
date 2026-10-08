# 云端待执行步骤（本轮 NOT_RUN）

用户已选择保持关机。当前 SSH 拒绝连接，不再重试；未开机、上传或运行云端程序。最后已知执行仓库 HEAD 为 2970979645380a8505076910bf1af227d2a5632c；不是本轮核实值。

用户下一次决定继续时：

1. 手动开机后重新确认 SSH 端点与身份。沿用既有密钥，不把密码、token 或私钥写入脚本/报告。
2. 核对 /root/autodl-tmp/SGP/repo 的分支、HEAD、clean。仅 fast-forward 到 GATE6_GIT_STATE.json 记录的已提交 HEAD；存在合法后续提交先审查，不 reset，不 force-push。数据路径仍为 /root/autodl-tmp/SGP/inputs/repo 下对应相对路径，仓库使用既有链接方案。
3. 逐项检查 GATE6_INPUT_LOCK.json。科学运行数据只有五项；代码从 Git 恢复，三个历史小文件是无求解资源回归 fixture。只传缺失或未验证文件到新的暂存路径，校验 SHA 后再形成最终路径；已存在不同哈希文件不覆盖。原 3h NetCDF=72,082,285 字节，SHA 238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d。完整输入 manifest（来源说明，不是新增运行读依赖）=429,810 字节，SHA f36b17072be20cafb7161bb60721fb55dff6f27699f113063e8e82bafea0b111。其余小输入通常已随 Gate5 部署，仍应实际逐文件核对。
4. 使用现有 /root/autodl-tmp/SGP/env/gate5/bin/python；不升级或重新复制环境。按冻结 Linux spec 与版本回执核验。分配唯一 evidence 子目录并运行下面的无求解测试入口。

```bash
cd /root/autodl-tmp/SGP/repo
/root/autodl-tmp/SGP/env/gate5/bin/python scripts_project/run_gate6_baseline.py \
  --mode test --output /root/autodl-tmp/SGP/evidence/gate6_no_solver_<NEW_UNIQUE_ID>
```

输出目录不得已存在；该命令经过测试，只做文件审计和小型/mock 测试，生产完整 create_model 与原生 run/presolve 被拦截。测试前应把 stdout/stderr 重定向到独立 supervisor 日志，保留返回码。这里不提供或创建 build/solve 授权文件。

5. 再记录当前 cgroup 及可见祖先限制/用量、有效 CPU、数据盘、活动任务；不读任务命令行中的凭证，不以宿主机 RAM 或本地 Windows 门槛判断。输出资源快照到 evidence。
6. 回传轻量回执与 SHA 至 D:\ResearchWorkspaces\ASEAN\outputs\gate6_baseline_prepare_20261008 的新追加目录，保留本轮 NOT_RUN 历史。输入/代码/环境/云端无求解测试/资源均合格，且人类接受预算后，才讨论另一次明确的 Gate6 构模/求解授权。

严禁上传整个 ASEAN、WSL VHDX、环境目录、历史大 ZIP 或再上传 Gate5 已交付网络。本清单不是开机或计费授权，也没有触发 GitHub Actions。
