"""Step 4. Build ../index.html and ../README.md from page_template.html and README_template.md.

Every number in the text is a placeholder like {{outcomes.town.n|int}} filled from
../data/results.json. The page data (every Gazetteer place with its derived variables and outcome)
are embedded as `const D = ...`.
Formats: int, pct0, pct1, f1, f2, f3, words, raw.
Run: python3 04_build_site.py
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
D = dict(R=R, P=P)
WORDS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "km1": return f"{v:.1f}"
    if f == "x1": return f"{v:.1f}"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "f3": return f"{v:.3f}"
    if f == "words": return WORDS[int(v)] if int(v) < len(WORDS) else f"{int(v):,}"
    if f == "p": return "p < 0.001" if v < 0.001 else f"p = {v:.3f}"
    if f == "Words": w = fmt(v, "words"); return w[0].upper() + w[1:]
    return str(v)


def gaz_credit(html=True):
    """The acknowledgement in the form the Gazetteer asks for, one clause per county page used."""
    url = "http://www.history.ac.uk/cmh/gaz/gazweb2.html"
    parts = "; ".join(f"{c} (last updated {d})" for c, d in R["county_dates"].items())
    lt, gt = ("&lt;", "&gt;") if html else ("<", ">")
    return f"Samantha Letters, Online Gazetteer of Markets and Fairs in England and Wales to 1516 {lt}{url}{gt}: {parts}."


def sub(m_):
    path, _, f = m_.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


if __name__ == "__main__":
    t = open(os.path.join(HERE, "page_template.html")).read()
    t = t.replace("{{GAZ_CREDIT}}", gaz_credit())
    t = re.sub(r"\{\{(.+?)\}\}", sub, t)
    t = t.replace("/*DATA*/", "const D = " + json.dumps(D, separators=(",", ":"), ensure_ascii=False) + ";")
    open(os.path.join(ROOT, "index.html"), "w").write(t)
    print("index.html", len(t.encode()) // 1024, "KB")
    md = re.sub(r"\{\{(.+?)\}\}", sub, open(os.path.join(HERE, "README_template.md")).read().replace("{{GAZ_CREDIT}}", gaz_credit(False)))
    open(os.path.join(ROOT, "README.md"), "w").write(md)
    print("README.md written")
