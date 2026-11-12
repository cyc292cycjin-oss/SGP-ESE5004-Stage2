"""只读：逐条打印 WINDOWS_PYTHON_COMMANDS.csv 的命令（去重：同一时间戳与命令文本只列一次），供人工核对是否写文件（含重定向 >）。"""
import pandas as pd
t = pd.read_csv("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/evidence/WINDOWS_PYTHON_COMMANDS.csv", keep_default_na=False)
t["key"] = t.command.str[:300]
u = t.drop_duplicates("key")
print("unique commands", len(u))
for i, r in u.iterrows():
    c = r.command
    redir = ">" in c.replace("->", "").replace(">=", "").replace("> /dev/null", "")
    print(f"[{i}] {r.session} {r.timestamp} redirect_or_gt={redir} :: {c[:330]}")
