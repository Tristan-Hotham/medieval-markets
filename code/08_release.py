"""Step 8. Blog post (release/blog/post.html from blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader.
Run: python3 08_release.py
"""
import json, os, re, shutil, zipfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
t = open(os.path.join(HERE, "blog_template.html")).read().replace("{{GAZ_CREDIT}}", b.gaz_credit())
t = re.sub(r"\{\{(?!IMG\|)([^{}]+?)\}\}", b.sub, t)
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m

title = "Market Towns That Failed: What Became of the Medieval Market Places of England and Wales"
o = R["outcomes"]
meta = dict(
    title="Market towns that failed: what became of the medieval markets of England and Wales?",
    slug="medieval-markets",
    excerpt=(f"Medieval kings licensed markets in their thousands, each a bet that a village would become a town. I followed all {R['counts']['market_places']:,} "
             f"market places in England and Wales to today: {o['town']['n']:,} are towns, {o['village']['n']:,} are villages, and a few are fields or sea."),
    seo_description=f"Of {R['counts']['market_places']:,} medieval market places in England and Wales, {R['town_share'] * 100:.0f}% are towns today. Which succeeded, and why most did not.",
    tags=["medieval", "markets", "market towns", "charters", "Black Death", "towns", "maps", "data"],
    header_alt=(f"Title card reading 'Market towns that failed' on a parchment background, beside a map of England and Wales covered in dots for "
                f"medieval market places, dark red for those that are towns today and ochre for villages. Text: of {R['counts']['market_places']:,} medieval market "
                f"places in England and Wales, only {o['town']['n']:,} are towns today; {o['village']['n']:,} are villages."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

pt = open(os.path.join(ROOT, "release", "paper", "Hotham_Market_Towns.tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("$<$", "<")
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title=title,
    description_html=f"<p>{ab}</p><p>Markets and fairs data derived from Samantha Letters, Online Gazetteer of Markets and Fairs in England and Wales to 1516 (Centre for Metropolitan History, Institute of Historical Research), which is copyright; only derived variables are included.</p>"
                     f"<p>Interactive version: https://tristan-hotham.github.io/medieval-markets/. Data and code: https://github.com/Tristan-Hotham/medieval-markets. Blog post: to follow.</p>",
    keywords=["medieval markets", "market charters", "market towns", "boroughs", "urban history", "Black Death", "Bracton", "persistence", "England", "Wales"],
    licence="cc-by-nc-sa-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/medieval-markets", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/medieval-markets/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://archives.history.ac.uk/gazetteer/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-rivers", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ons.gov.uk/census", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://digitalcollections.hull.ac.uk/collections/3t945r28b", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://zenodo.org/records/17122148", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://doi.org/10.5281/zenodo.23689962", relation="isderivedfrom", resource_type="other"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", "Hotham_Market_Towns.pdf"), Z)
for f in ["markets.csv", "decades.csv", "counties.csv", "model.csv", "grid_checks.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "medieval-markets_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): zf.write(p, f"medieval-markets/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"medieval-markets/{f}")
print("release files written; post words:", len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t, flags=re.S)).split()))
