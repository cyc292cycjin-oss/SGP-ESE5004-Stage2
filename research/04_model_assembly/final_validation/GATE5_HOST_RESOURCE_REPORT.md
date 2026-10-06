# Gate5 主机资源核验（只读）

观测时间：2026-10-06T22:33:00.343769+08:00（Asia/Shanghai）。真实Windows模块合计 **16.00 GiB**；OS可见物理内存 **15.731 GiB**。这些来自实际主机查询，未从WSL反推。

| 资源 | 本次最终观测 |
|---|---:|
| Windows可用物理内存 | 1.637 GiB |
| Windows提交量 / 提交上限 | 27.216 / 27.727 GiB |
| Windows提交余量 | 0.511 GiB |
| Windows分页文件已分配 / 当前使用 | 11.996 / 2.516 GiB |
| WSL MemTotal / MemAvailable | 7.621 / 7.014 GiB |
| WSL SwapTotal / SwapFree | 2.000 / 2.000 GiB |
| Linux文件系统空闲 | 939.9 GiB |

Windows分页文件为系统管理。用户目录C:/Users/20122下实际.wslconfig不存在；未创建或修改。WSL2.7.14.0，内核6.18.33.2-2；最终发行版清单只有Ubuntu Running (WSL2)。初始/中途的发行版状态按各自采样时刻保留，未执行shutdown或人工重启。预检调用会启动尚未运行的Ubuntu进行只读检查。

当前cgroup init.scope memory.max= max；没有在该路径与可读祖先观察到更低的有限内存上限。这不取消WSL全局MemTotal限制。实际swap为/proc/swaps中的/dev/sdc，2GiB、未使用。没有发现Linux docker/containerd/podman进程；Windows相关进程只有vmmemWSL。此为当时可见进程/发行版清单，不声称全主机容器活动永远不存在。

| 主要进程（不采集命令行） | Working set MiB | Private bytes MiB |
|---|---:|---:|
| vmmemWSL | 2761.9 | 2932.7 |
| cs2 | 2290.3 | 7210.6 |
| ChatGPT | 533.6 | 960.3 |
| MsMpEng | 254.7 | 415.3 |
| steamwebhelper | 240.4 | 477.1 |
| ChatGPT | 212.0 | 389.1 |
| ChatGPT | 181.3 | 263.2 |
| pwsh | 151.2 | 68.2 |

进程working set可能共享页面，不能直接求和当作总物理占用。Private bytes也不是物理RSS。预检自己的进程RSS/PSS与各可见子进程单独记录，当前未运行研究求解。主机与Guest可用内存不能相加：Guest可回收页不等于Windows当前立即可供分配的物理页。

初始采样与最终采样之间主机占用明显变化，最终Windows可用量低于2GiB候选主机保护线。仅凭一次空闲快照不足以证明四小时运行安全。没有关闭任何应用或改变分页设置。

原始证据：memory_readiness_20261006/HOST_RESOURCE_SNAPSHOT.json、DEFAULT_ENTRYPOINT_PREFLIGHT.json、INITIAL_HOST_RESOURCE_SNAPSHOT.json。安全重采入口：Get-Gate5HostResources.ps1，或默认只预检的Invoke-Gate5MemoryReadiness.ps1；不需要用户手抄参数，也不读取密钥/许可证。
