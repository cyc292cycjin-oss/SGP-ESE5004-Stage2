s = open("/home/jin/v3/x1_load.py").read()
a = "    bind = np.mean([(x.abs() >= 0.999 * y) for x, y in zip(g.f, g.cap)], axis=0)\n"
b = "    bind = np.mean([(x > 1e-3) for x in g.mu], axis=0)   # binding = non-zero bound dual; a static s_nom x s_max_pu is not the limit when s_max_pu varies in time\n"
assert s.count(a) == 1; s = s.replace(a, b).replace("share_lines_at_limit", "share_line_hours_binding")
a2 = "t = pd.DataFrame(out).sort_values"
b2 = 'print("s_max_pu static", n.lines.s_max_pu[L.index].round(3).unique()[:6], "time-varying lines", len(n.lines_t.s_max_pu.columns.intersection(L.index)), "range", (float(n.lines_t.s_max_pu[n.lines_t.s_max_pu.columns.intersection(L.index)].min().min()), float(n.lines_t.s_max_pu[n.lines_t.s_max_pu.columns.intersection(L.index)].max().max())) if len(n.lines_t.s_max_pu.columns.intersection(L.index)) else None)\nt = pd.DataFrame(out).sort_values'
assert s.count(a2) == 1; s = s.replace(a2, b2)
open("/home/jin/v3/x1_load.py", "w").write(s)
