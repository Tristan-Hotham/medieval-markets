"""r/dataisbeautiful collage for Market Towns That Failed (medieval-markets). Run from this folder: python3 collage.py
Every number is read from ../data/results.json or ../data/page_data.json."""
import json, math, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon

F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(os.path.join(F, f))
DISP = fm.FontProperties(fname=os.path.join(F, "FrauncesVar.ttf"), weight=900)
SER = "Source Serif 4"; MONO = "IBM Plex Mono"
BG = "#F3ECDC"; FG = "#2B2219"; MUT = "#6F6354"; LAND = "#E6DAC1"; WAX = "#9C2A22"; WAXL = "#D98F86"; VIL = "#C49A3E"; HAM = "#8A8774"; ABS = "#C8682E"; INK = "#2F4A6B"
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
ROWS = [dict(zip(P["cols"], r)) for r in P["rows"] if r[P["cols"].index("kind")] != 2]
K = math.cos(math.radians(52.5))
LANDP = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LANDP.append(np.c_[a[:, 0] * K, a[:, 1]])
pct = lambda v: f"{v * 100:.0f}%"
o = R["outcomes"]; g = R["grants"]; s = R["spacing"]

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.04, 0.968, "Which medieval market towns failed?", fontproperties=DISP, fontsize=40, color=FG, va="top")
fig.text(0.04, 0.917, f"Between 1066 and 1516 English kings licensed markets in their thousands, each a bet that a village would become a\n"
         f"town. I followed all {R['counts']['market_places']:,} market places in England and Wales from the Gazetteer of Markets and Fairs to today.",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.4)

# hero map
ax = fig.add_axes([0.0, 0.335, 0.6, 0.505])
for a in LANDP:
    ax.add_patch(Polygon(a, closed=True, fc=LAND, ec="#CDBFA3", lw=.6, zorder=0))
ax.set_xlim(-5.9 * K, 1.9 * K); ax.set_ylim(49.9, 55.85); ax.set_aspect("equal"); ax.axis("off")
def pts(k): return [r for r in ROWS if r["out"] == k]
v = pts(2) + pts(3)
ax.scatter([r["lon"] * K for r in v], [r["lat"] for r in v], s=9, c=[VIL if r["out"] == 2 else HAM for r in v], alpha=.55, lw=0, zorder=1, rasterized=True)
v = pts(1); ax.scatter([r["lon"] * K for r in v], [r["lat"] for r in v], s=14, c=ABS, alpha=.8, lw=0, zorder=2)
v = pts(0); ax.scatter([r["lon"] * K for r in v], [r["lat"] for r in v], s=34, c=WAX, edgecolors="#5E1510", lw=.5, zorder=3)
v = pts(4); ax.scatter([r["lon"] * K for r in v], [r["lat"] for r in v], s=60, facecolors="none", edgecolors=FG, lw=1.1, zorder=4)
for nm, (dx, dy, ha) in {"Ravenserodd": (-10, 6, "right"), "Old Winchelsea": (8, -12, "left"), "Old Sarum": (-10, -10, "right")}.items():
    r = [q for q in ROWS if q["place"] == nm][0]
    ax.annotate(nm, (r["lon"] * K, r["lat"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", family=MONO, fontsize=10.5, color=FG, zorder=6, bbox=dict(fc=BG, ec="none", alpha=.85, pad=1.5))
key = [(WAX, "o", "towns or cities", o["town"]["n"]), (ABS, "o", "swallowed by towns", o["absorbed"]["n"]), (VIL, "o", "villages", o["village"]["n"]),
       (HAM, "o", "hamlets", o["hamlet"]["n"]), ("none", "o", "gone from the map", o["gone"]["n"])]
xs = [0.04, 0.235, 0.445, 0.6, 0.735]
for (c, m, t, n), x0 in zip(key, xs):
    fig.patches.append(matplotlib.patches.Ellipse((x0 + .006, 0.856), .009, .009 * 12 / 15, transform=fig.transFigure, fc=c if c != "none" else BG, ec=FG if c == "none" else c, lw=1.1))
    fig.text(x0 + .016, 0.856, f"{n:,} {t}", va="center", family=MONO, fontsize=11, color=FG)

# headline numbers
tx = fig.add_axes([0.62, 0.35, 0.36, 0.48]); tx.axis("off")
notes = [(pct(R["town_share"]), WAX, f"of medieval market places are a town\nor city today: {o['town']['n']:,} of {R['counts']['market_places']:,}. More than half\n({pct(o['village']['share'])}) are villages."),
         (f"{g['peak_n']} to {g['d1350s']}", INK, f"royal market grants in the 1250s, the\npeak decade, against the 1350s, the\ndecade after the Black Death."),
         (f"{pct(s['close_town'])} vs {pct(s['far_town'])}", WAX, f"towns today among granted markets within\nBracton's 6 2/3 miles ({s['bracton_km']:.1f} km) of an\nolder market, and those with room."),
         (pct(R["everitt"]["town_share"]), INK, f"of the market towns of c.1600 are still\ntowns. Most of the sorting was done by\nthe time of Elizabeth I.")]
for (big, col, small), y in zip(notes, [1.0, 0.745, 0.49, 0.235]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=36, color=col, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.085, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# small multiple 1: grants per decade
fig.text(0.04, 0.312, "ROYAL MARKET GRANTS PER DECADE", family=MONO, fontsize=10.5, color=MUT)
bx = fig.add_axes([0.06, 0.12, 0.5, 0.175], facecolor=BG)
D = R["decades"]; x = np.array([d["decade"] for d in D])
bx.bar(x + 5, [d["market_grants"] for d in D], width=8, color=WAX)
bx.axvline(1348, color=FG, ls="--", lw=1); bx.text(1356, 245, "Black Death\n1348", family=MONO, fontsize=10, va="top", color=FG)
bx.text(g["peak_decade"] - 4, g["peak_n"], f"{g['peak_decade']}s: {g['peak_n']}", family=MONO, fontsize=10, ha="right", va="top", color=FG)
bx.set_xlim(1060, 1520); bx.set_ylim(0, 270)
for sp in ("top", "right"): bx.spines[sp].set_visible(False)
bx.spines["left"].set_color(MUT); bx.spines["bottom"].set_color(MUT)
bx.tick_params(labelsize=10, colors=FG); [t.set_family(MONO) for t in bx.get_xticklabels() + bx.get_yticklabels()]
bx.grid(axis="y", color="#DDD2BD", lw=.8); bx.set_axisbelow(True)

# small multiple 2: share town by start
fig.text(0.64, 0.312, "TOWN TODAY, BY WHEN THE MARKET BEGAN", family=MONO, fontsize=10.5, color=MUT)
cx = fig.add_axes([0.64, 0.12, 0.34, 0.175]); cx.axis("off")
V = [p for p in R["by_period"] if p["key"] not in ("1349 to 1399", "1400 to 1516")]
for i, p in enumerate(V):
    y = 1 - i * .2
    lab = "by custom" if p["key"] == "prescriptive" else "granted " + p["key"]
    cx.text(0, y, lab, family=MONO, fontsize=10.5, color=FG, va="center", transform=cx.transAxes)
    cx.barh([y], [p["town_share"] * .62], left=.58, height=.11, color=INK if p["key"] == "prescriptive" else WAX, transform=cx.transAxes)
    cx.text(.59 + p["town_share"] * .62, y, pct(p["town_share"]), family=MONO, fontsize=10.5, color=FG, va="center", transform=cx.transAxes)

fig.text(0.04, 0.085, "Town = Ordnance Survey City or Town today. A grant is a licence, not proof a market was held. Associations, not causes.",
         family=MONO, fontsize=9.5, color=MUT)
fig.text(0.04, 0.012,
         "Data: derived from Samantha Letters, Online Gazetteer of Markets and Fairs in England and Wales to 1516 (Centre for Metropolitan History, IHR;\n"
         "copyright, derived counts and years only). OS Open Names (Contains OS data © Crown copyright and database right 2026, OGL v3). ONS Census 2021 (OGL v3).\n"
         "Bracton, trans. S.E. Thorne, vol. 3, p. 198. Natural Earth coastline.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib.  tristan-hotham.github.io/medieval-markets",
         family=MONO, fontsize=8.6, color=MUT, linespacing=1.45)
fig.savefig(os.path.join(HERE, "which_medieval_market_towns_failed.png"), facecolor=BG, dpi=200)
print("ok")
