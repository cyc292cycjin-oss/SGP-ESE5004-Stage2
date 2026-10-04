# Research 构网入口与实际执行状态

新增可执行入口`scripts_project/build_research_network.py`，独立DAG`workflow/research_assembly.smk`。当前已执行入口并回传真实输入阻断；**完整生产资产物化和导出分支尚未实网验证**。

调用链：原始源胶囊→`reconstruct_base_accounts.py`→已批准方法的2050 registry→`allocate_assembly_inputs.py`→`check_assembly_inputs.py`数值/真实数组门→已合格2050电力基础网+Gate3数值片段/碳map→PyPSA拼装/Load→导出前与回读静态检查。入口不调用优化、旧final_adjustment或only_elec_network。Snakemake dry-run只有一个research_fullsc_unsolved job。

可复用资产实际核验：作者2025结果包SHA06152be5…含96AC+4DC地理母线、2013年2920×3h=8760h、98基负荷输入位置及可再生p_max_pu。分配只读取地理数据、权重和基负荷p_set（识别其低压附件），未读取p_nom_opt、dispatch、duals、objective。电力按国家内输入曲线归一化；固定燃料采用同国节点年负荷份额/平时序；海运/航空按同国港口/机场size权重映射最近地理节点。非观测小时燃料、size非交通量等局限写入allocation manifest。

131个最终合格账户均有实际数组、节点国别、数组hash和国家→节点→时间守恒。大文件`allocations.npz`随本轮交付包提供，不加入Git源代码。不能用这些数组将全局ALLOCATION_READY提前改为true。

尚缺的工程产物：2050合格电力基础网（2025作者求解文件不能直接改名；需逐项核对成本、存续容量与潜力）、100节点的实际Gate3参数/碳归属/生物质隔离bundle。当前asset_bundle明确UNQUALIFIED，未伪造替代文件。此项是后续工程工作，不能全部转嫁为用户补数据。

在输入完整后，命令为：
```sh
python scripts_project/build_research_network.py --repo . --allocation <actual_allocation_dir> --assets research_inputs/assembly_v1/asset_bundle.json --output results_project/assembly_v1/research_fullsc_2050_unsolved.nc --report results_project/assembly_v1/build_receipt.json
snakemake -s workflow/research_assembly.smk --cores 1 --config research_allocation_dir=<actual_allocation_dir> research_asset_manifest=research_inputs/assembly_v1/asset_bundle.json
```

当前运行会在输入门返回2，不会输出.nc。Gate3的生物质/CO2专用Store仍保留显式运行约束hook，未来求解阶段必须安装；本轮不创建优化变量或求解。

独立复算入口：`python scripts_project/rebuild_assembly_targets.py --repo . --output <review.json>`；不读取存储的Value/CandidateValue作为计算输入，131项已接受目标值从原始源及批准方法复算一致。
