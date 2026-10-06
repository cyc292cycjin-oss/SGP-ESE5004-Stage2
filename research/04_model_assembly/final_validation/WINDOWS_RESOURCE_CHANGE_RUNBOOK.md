# Windows侧后续步骤 — 本轮不执行设置变更

1. 当前先不改WSL。用户自行保存其他任务并关闭不需要同时运行的高内存应用；助手不会杀这些进程。重新运行交付目录scripts/Invoke-Gate5MemoryReadiness.ps1（不加Execute），查看主机/Guest/提交量是否同时达到GATE5_MEMORY_PLAN.md预算。
2. 只有在用户接受资源方案后才编辑实际用户目录.wslconfig。本次检查该文件不存在。先备份：若存在，以时间戳复制到同目录备份文件并记录SHA256；若不存在，记录ABSENT，不伪造备份。不要覆盖其他用户的设置。
3. 评审候选约memory=11GB、swap=4GB时，先核对主机能保留实际Windows工作集和2GiB运行保护；当前机器负载不满足，不能现在照抄。使用编辑器只变更[wsl2] memory/swap键并保留其他设置。不改变线程预算，求解仍为2线程。
4. 由用户确认所有WSL发行版、容器及本地任务均已结束后，才可在Windows手动执行wsl --shutdown并重新打开Ubuntu。该命令会终止所有WSL发行版；脚本不会自动执行。不能在活动任务中照做。
5. 重启后用同一只读入口重新记录Windows和Linux实际内存/swap、环境版本与输入hash。配置文字不等于实际生效。准入仍不通过则停止，不能调低保护线。
6. 回滚：同样先确认任务已结束；存在旧文件时从已核对备份恢复；原状态ABSENT时，仅移除本次新建且路径/hash已核对的.wslconfig。保留备份与变更记录，用户手动重启WSL后复检。

官方设置说明：[Microsoft WSL advanced configuration](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)。.wslconfig作用于WSL2，应用变更通常需要停止后重启；swap是磁盘交换空间，不能作为物理RAM承诺。

单一启动入口默认仅preflight。未来加Execute仍要求单独的真实授权回执：接受预算、指定gate5_20261006_05、max_attempts=1、当时提交SHA及冻结输入hash；未批准模板会拒绝。参数固定10800秒solver、14400秒wall、2线程。授权不会跳过内存、结果资格或动态验收。当前第五次运行没有授权，也没有运行。
