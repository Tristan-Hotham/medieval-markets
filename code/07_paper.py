"""Step 7. Build the paper PDF: fill paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Market_Towns.tex and compile it with xelatex (figures from 06_release_figs.py).
Placeholders: {{path|fmt}} as in 04_build_site.py, with % escaped for LaTeX.
Run: python3 07_paper.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Market_Towns"
WORDS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty twenty-one twenty-two twenty-three twenty-four twenty-five twenty-six twenty-seven twenty-eight twenty-nine thirty".split()


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f in ("f1", "km1"): return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "p": return "p $<$ 0.001" if v < 0.001 else f"p = {v:.3f}"
    if f == "words": return WORDS[int(v)] if int(v) < len(WORDS) else f"{int(v):,}"
    if f == "Words": w = fmt(v, "words"); return w[0].upper() + w[1:]
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")
pc = lambda v: f"{v * 100:.0f}"
rows = ""
for p in R["by_period"]:
    lab = "Market by custom (prescriptive)" if p["key"] == "prescriptive" else "First granted " + p["key"]
    rows += f"{lab} & {p['n']:,} & {p['town']:,} & {pc(p['town_share'])} & {pc(p['urban_share'])} & {pc(p['gone_share'])} & {pc(p['everitt_share'])}\\\\\n"
TP = ("\\begin{table}[tbp]\\centering\\small\\caption{Market places by how their market began, and their outcome. Town: OS City or Town today. "
      "Urban: town, or swallowed by a town. Hamlet or gone: OS Hamlet or Other Settlement, or no longer on the map. c.1600: in Everitt's list of market towns.}\\label{tab:period}"
      "\\begin{tabular}{lrrrrrr}\\toprule Group & Places & Towns & \\% town & \\% urban & \\% hamlet or gone & \\% c.1600\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
dd = R["or_dd"]; rows = ""
for r in R["model_all"]["rows"]:
    d = dd.get(r["var"])
    rows += f"{tex(r['label'])} & {r['odds_ratio']:.2f} & {r['lo']:.2f} to {r['hi']:.2f} & " + (f"{d['odds_ratio']:.2f} & {d['lo']:.2f} to {d['hi']:.2f}" if d else "& ") + "\\\\\n"
d = dd["log_hh"]; rows += f"Domesday households (log) & & & {d['odds_ratio']:.2f} & {d['lo']:.2f} to {d['hi']:.2f}\\\\\n"
rows += f"\\midrule Places & {R['model_all']['n']:,} & & {R['model_domesday']['n']:,} & \\\\\nPseudo $R^2$ & {R['model_all']['pseudo_r2']:.3f} & & {R['model_domesday']['pseudo_r2']:.3f} & \\\\\n"
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Logistic regressions of being a town or city today. Odds ratios with 95\\% intervals. "
      "Model 2 is restricted to market places matched to a Domesday place with a household count.}\\label{tab:model}"
      "\\begin{tabular}{lrlrl}\\toprule & \\multicolumn{2}{c}{Model 1: all} & \\multicolumn{2}{c}{Model 2: Domesday}\\\\ Predictor & OR & 95\\% CI & OR & 95\\% CI\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for f in R["failed_boroughs"]:
    rows += f"{tex(f['place'])} & {tex(f['county'])} & {f['first'] or ''} & {f['markets']} & {f['fairs']} & {'hamlet' if f['outcome'] == 'hamlet' else 'gone'}\\\\\n"
TF = ("\\begin{table}[tbp]\\centering\\small\\caption{Market places that were boroughs by 1516 and are hamlets or gone from the map today. First: first year with evidence of a market (blank: none given).}\\label{tab:failed}"
      "\\begin{tabular}{llrrrl}\\toprule Place & County & First & Markets & Fairs & Today\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
url = "http://www.history.ac.uk/cmh/gaz/gazweb2.html"
GC = "Samantha Letters, Online Gazetteer of Markets and Fairs in England and Wales to 1516 $<$\\url{" + url + "}$>$: " + "; ".join(f"{c} (last updated {d})" for c, d in R["county_dates"].items()) + "."
s = open(os.path.join(HERE, "paper_template.tex")).read()
s = s.replace("{{TABLE_PERIOD}}", TP).replace("{{TABLE_MODEL}}", TM).replace("{{TABLE_FAILED}}", TF).replace("{{GAZ_CREDIT}}", GC)
s = re.sub(r"\{\{(.+?)\}\}", sub, s)
assert "{{" not in s
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(s)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
print(r.stdout[-600:])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.move(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
