"""Step 6. Static figures for the paper (release/paper/f_*.png) and the blog (release/blog/b_*.png, 1520 px wide).
Maps are drawn from coordinates over the Natural Earth 1:10m land outline (no web tiles).
Every number comes from ../data/results.json or ../data/page_data.json.
Run: python3 06_release_figs.py
"""
import json, math, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    if os.path.exists(os.path.join(FD, f)): fm.fontManager.addfont(os.path.join(FD, f))
BG = "#F4EEE1"; FG = "#2B2219"; MUT = "#6F6354"; RULE = "#DDD2BD"; LAND = "#E4D9C2"
WAX = "#9C2A22"; WAXL = "#D98F86"; ABS = "#C8682E"; VIL = "#C49A3E"; HAM = "#8A8774"; GONE = "#A69C8C"; INK = "#2F4A6B"
COL = [WAX, ABS, VIL, HAM, GONE]; OLAB = ["Town or city", "Swallowed by a town", "Village", "Hamlet", "Gone from the map"]
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": "Source Serif 4", "font.size": 13, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG, "axes.facecolor": BG, "figure.facecolor": BG})
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
ROWS = [dict(zip(P["cols"], r)) for r in P["rows"]]
PO = os.path.join(ROOT, "release", "paper"); BO = os.path.join(ROOT, "release", "blog")
os.makedirs(PO, exist_ok=True); os.makedirs(BO, exist_ok=True)
K = math.cos(math.radians(52.5))
LAND_POLYS = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LAND_POLYS.append(np.c_[a[:, 0] * K, a[:, 1]])
pct = lambda v: f"{v * 100:.0f}%"


def basemap(ax, ext=(-5.9, 1.9, 49.9, 55.85)):
    for a in LAND_POLYS:
        ax.add_patch(Polygon(a, closed=True, fc=LAND, ec="#CDBFA3", lw=.5, zorder=0))
    ax.set_xlim(ext[0] * K, ext[1] * K); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def save(fig, name, blog):
    if blog:
        fig.savefig(os.path.join(BO, name), dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=.2)
    else:
        fig.savefig(os.path.join(PO, name), dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=.15)
    plt.close(fig)


def fix_width(name):
    """Resize blog PNGs to exactly 1520 px wide."""
    from PIL import Image
    p = os.path.join(BO, name); im = Image.open(p)
    if im.size[0] != 1520:
        im = im.resize((1520, round(im.size[1] * 1520 / im.size[0])), Image.LANCZOS); im.save(p, optimize=True)


def fig_map(blog):
    fig, ax = plt.subplots(figsize=(7.6, 7.6) if blog else (6.4, 6.4))
    basemap(ax, (-5.9, 4.6, 49.9, 55.85))
    for o in (2, 3, 1, 0, 4):
        pts = [r for r in ROWS if r["kind"] != 2 and r["out"] == o]
        x = [r["lon"] * K for r in pts]; y = [r["lat"] for r in pts]
        if o == 4:
            ax.scatter(x, y, s=30, facecolor="none", edgecolor=FG, lw=1, zorder=5)
        else:
            ax.scatter(x, y, s={0: 16, 1: 11, 2: 7, 3: 9}[o], c=COL[o], alpha={0: .95, 1: .9, 2: .75, 3: .9}[o], lw=0, zorder=2 + (o == 0))
    hs = [Line2D([], [], marker="o", ls="", ms=7, mfc=COL[i] if i < 4 else "none", mec=COL[i] if i < 4 else FG, label=f"{OLAB[i]} ({R['outcomes'][k]['n']:,})")
          for i, k in enumerate(["town", "absorbed", "village", "hamlet", "gone"])]
    ax.legend(handles=hs, loc="upper right", bbox_to_anchor=(1.0, 1.0), frameon=True, facecolor=BG, edgecolor=RULE, framealpha=.95, prop=dict(family=MONO, size=10.5 if blog else 9))
    save(fig, ("b_" if blog else "f_") + "map.png", blog)


def fig_decades(blog):
    D = R["decades"]; x = np.array([d["decade"] for d in D])
    fig, ax = plt.subplots(figsize=(7.6, 4.2) if blog else (6.4, 3.4))
    ax.bar(x + 5, [d["fair_grants"] for d in D], width=8.4, color=WAXL, alpha=.55, label="Fair grants")
    ax.bar(x + 5, [d["market_grants"] for d in D], width=5.2, color=WAX, label="Market grants")
    ax.axvline(1348, color=FG, ls="--", lw=1)
    ax.text(1352, 300, "Black Death, 1348", family=MONO, fontsize=10, va="top")
    pk = R["grants"]["peak_decade"]
    ax.text(pk - 4, R["grants"]["peak_n"] - 4, f"{pk}s: {R['grants']['peak_n']} market grants", family=MONO, fontsize=10, va="center", ha="right")
    ax.set_xlim(1060, 1520); ax.set_ylabel("Grants per decade"); ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True)
    ax.legend(frameon=False, prop=dict(family=MONO, size=10), loc="upper right", bbox_to_anchor=(1.0, 0.86))
    save(fig, ("b_" if blog else "f_") + "decades.png", blog)


def fig_period(blog):
    V = R["by_period"]
    lab = ["Market by custom" if v["key"] == "prescriptive" else "Granted " + v["key"] for v in V]
    fig, ax = plt.subplots(figsize=(7.6, 4.2) if blog else (6.4, 3.4))
    y = np.arange(len(V))[::-1]
    ax.barh(y, [v["town_share"] for v in V], color=[INK if v["key"] == "prescriptive" else WAX for v in V], height=.62)
    for yi, v in zip(y, V):
        ax.text(v["town_share"] + .008, yi, f"{pct(v['town_share'])} of {v['n']:,}", va="center", family=MONO, fontsize=10.5)
    ax.set_yticks(y); ax.set_yticklabels(lab); ax.set_xlim(0, .7)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0)); ax.set_xlabel("Share that are a town or city today")
    ax.grid(axis="x", color=RULE, lw=.8); ax.set_axisbelow(True)
    save(fig, ("b_" if blog else "f_") + "period.png", blog)


def fig_bracton(blog):
    V = R["spacing"]["bands"]
    fig, ax = plt.subplots(figsize=(7.6, 4.2) if blog else (6.4, 3.4))
    x = np.arange(len(V))
    ax.bar(x, [v["town_share"] for v in V], color=[WAXL if i < 4 else WAX for i in range(len(V))], width=.78)
    for xi, v in zip(x, V):
        ax.text(xi, v["town_share"] + .01, f"n = {v['n']}", ha="center", family=MONO, fontsize=9.5, color=MUT)
    ax.axvline(3.5, color=FG, ls="--", lw=1); ax.text(3.42, .53, "Bracton's 6 2/3 miles", family=MONO, fontsize=10, va="top", ha="right")
    ax.set_xticks(x); ax.set_xticklabels([v["band"] for v in V], fontsize=10.5)
    ax.set_xlabel("km from the nearest older market"); ax.set_ylabel("Share that are towns today")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0)); ax.set_ylim(0, .56)
    ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True)
    save(fig, ("b_" if blog else "f_") + "bracton.png", blog)


def fig_forest(blog):
    V = R["model_all"]["rows"]
    fig, ax = plt.subplots(figsize=(7.6, 4.8) if blog else (6.4, 4.0))
    y = np.arange(len(V))[::-1]
    for yi, v in zip(y, V):
        sig = v["lo"] > 1 or v["hi"] < 1
        ax.plot([v["lo"], v["hi"]], [yi, yi], color=WAX if sig else MUT, lw=2)
        ax.plot(v["odds_ratio"], yi, "o", ms=8, mfc=WAX if sig else BG, mec=WAX if sig else MUT, mew=1.6)
    ax.axvline(1, color=FG, lw=1); ax.set_xscale("log"); ax.set_xlim(.25, 8)
    ax.set_xticks([.25, .5, 1, 2, 4, 8]); ax.set_xticklabels(["0.25", "0.5", "1", "2", "4", "8"]); ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter()); ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_yticks(y); ax.set_yticklabels([v["label"] for v in V]); ax.set_xlabel("Odds ratio for being a town today (log scale)")
    ax.grid(axis="x", color=RULE, lw=.8); ax.set_axisbelow(True)
    save(fig, ("b_" if blog else "f_") + "forest.png", blog)


def fig_everitt(blog):
    """Two bars: c.1600 market towns versus the rest, split by outcome today."""
    import pandas as pd
    D = pd.DataFrame(ROWS); D = D[D.kind != 2]
    ev = (D["flags"] & 4) > 0
    fig, ax = plt.subplots(figsize=(7.6, 3.0) if blog else (6.4, 2.6))
    for yi, (mask, lab) in enumerate([(~ev, f"Not a market town c.1600 ({int((~ev).sum()):,})"), (ev, f"Market town c.1600 ({int(ev.sum()):,})")]):
        s = D[mask]; left = 0
        for o in range(5):
            w = float((s.out == o).mean())
            ax.barh(yi, w, left=left, color=COL[o], alpha=.6 if o == 4 else 1, height=.6, label=OLAB[o] if yi == 0 else None)
            if w > .07: ax.text(left + w / 2, yi, pct(w), ha="center", va="center", color="white", family=MONO, fontsize=10)
            left += w
    ax.set_yticks([0, 1]); ax.set_yticklabels([f"Not a market town c.1600\n({int((~ev).sum()):,} places)", f"Market town c.1600\n({int(ev.sum()):,} places)"])
    ax.set_xlim(0, 1); ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.legend(ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(.42, -.25), prop=dict(family=MONO, size=9.5))
    save(fig, ("b_" if blog else "f_") + "everitt.png", blog)


if __name__ == "__main__":
    for blog in (False, True):
        for f in (fig_map, fig_decades, fig_period, fig_bracton, fig_forest, fig_everitt):
            f(blog)
    for n in os.listdir(BO):
        if n.startswith("b_") and n.endswith(".png"): fix_width(n)
    print("figures written")
