"""Step 3. All statistics: what became of the medieval market places, and what predicts success.

Inputs: work/places_today.json (steps 1 and 2); OS Open Rivers; Itiner-e Roman roads;
Natural Earth land (coastline).
Outputs: data/markets.csv, data/markets.geojson, data/decades.csv, data/counties.csv,
data/model.csv, data/results.json (every number used anywhere), data/page_data.json.

Definitions
- Market place: a Gazetteer place with at least one market (M) line. Places with fairs only are
  kept in the data but left out of the market statistics.
- Outcome today (OS Open Names): "town" = the place's own name is an OS City or Town;
  "absorbed" = its own name is an OS Suburban Area, or an OS Village, Hamlet or Other Settlement
  lying inside a built-up area of 20,000 or more people (the nearest MSOA population-weighted
  centroid is within 1 km and belongs to such a 2022 built-up area: London districts such as
  Croydon, Bromley or Southwark, which OS lists as "Other Settlement"), or its name is not on the
  OS list and the nearest OS populated place within 1.5 km is a City, Town or Suburban Area; "village" = own
  name is an OS Village, or an OS Hamlet or Other Settlement with a same-name built-up area of 1,000 or
  more people (OS uses "Other Settlement" for some sizeable places such as Kings Langley); "hamlet" = own
  name is an OS Hamlet or Other Settlement otherwise; "gone" = name
  not on the OS list and no town within 1.5 km (nearest place a village or hamlet, or nothing).
- Grant: a market created by royal charter, letter close, letter patent or other grant.
  Prescriptive: held by custom (often boroughs and mints), year = first record, not foundation.
- Bracton distance: 20 miles / 3 = 6 2/3 miles = 10.73 km (Bracton, De Legibus, Thorne
  translation, vol. 3, p. 198: a reasonable day's journey of twenty miles divided in three).
- Major river: an OS Open Rivers watercourse whose named course totals at least 40 km.
- Roman road: Itiner-e main or secondary road, conjectured (hypothetical lines excluded).
- Coast: Natural Earth 1:10m land outline of Great Britain.
Run: python3 03_analysis.py
"""
import json, math, os, re, sqlite3, struct
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from scipy import stats
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); HIST = os.path.join(ROOT, "..")
DATA = os.path.join(ROOT, "data")
P = pd.DataFrame(json.load(open(os.path.join(ROOT, "work", "places_today.json"))))
P = P[P.easting_used.notna()].reset_index(drop=True)
to_bng = Transformer.from_crs(4326, 27700, always_xy=True)
BRACTON_KM = 20 / 3 * 1.609344
X = P.easting_used.values; Y = P.northing_used.values

# ---------- outcome
def outcome(r):
    t, m = r.os_type, r.os_match
    if m in ("name", "similar name"):
        if t in ("City", "Town"): return "town"
        if t == "Suburban Area" or (r.area_bua_pop2021 >= 20000): return "absorbed"
        if t == "Village" or (r.bua_pop2021 >= 1000): return "village"
        return "hamlet"
    if (m == "nearest" and t in ("City", "Town", "Suburban Area")) or r.area_bua_pop2021 >= 20000:
        return "absorbed"
    return "gone"


P["outcome"] = [outcome(r) for r in P.itertuples()]
# Manual correction: OS Open Names "Old Sarum" is a modern housing area beside the abandoned medieval city,
# whose cathedral and townspeople moved to New Salisbury in the thirteenth century.
P["outcome_note"] = None
P.loc[(P.place == "Old Sarum") & (P.county == "Wiltshire"), ["outcome", "outcome_note"]] = ["gone", "manual: the OS name now marks a modern housing area beside the abandoned medieval city"]
P["town"] = P.outcome == "town"
P["urban"] = P.outcome.isin(["town", "absorbed"])
P["has_market"] = P.n_markets > 0
P["pop2021"] = P.bua_pop2021
P["pop2021_src"] = np.where(P.bua_pop2021.notna(), "built-up area", np.where(P.parish_pop2021.notna(), "parish", ""))
P.loc[P.bua_pop2021.isna(), "pop2021"] = P.loc[P.bua_pop2021.isna(), "parish_pop2021"]
P["bua_any_pop"] = P.bua_pop2021.fillna(P.area_bua_pop2021)

# ---------- environment
ENV = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


def decode(blob):
    flags = blob[3]; wkb = blob[8 + ENV[(flags >> 1) & 7]:]

    def read(p):
        bo = "<" if wkb[p] == 1 else ">"
        typ = struct.unpack(bo + "I", wkb[p + 1:p + 5])[0]
        dim = 3 if (typ // 1000 in (1, 2) or typ & 0x80000000) else 2
        base = (typ % 1000) & 0xFF; p += 5
        n = struct.unpack(bo + "I", wkb[p:p + 4])[0]; p += 4
        if base == 2:
            a = np.frombuffer(wkb[p:p + 8 * dim * n], dtype=bo + "f8").reshape(n, dim)[:, :2]
            return [a], p + 8 * dim * n
        out = []
        for _ in range(n):
            a, p = read(p); out += a
        return out, p
    return read(0)[0]


def densify(lines, step=50.0):
    pts = []
    for a in lines:
        a = np.asarray(a, float)
        if len(a) < 2: pts.append(a); continue
        seg = np.diff(a, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); k = np.maximum(1, np.ceil(L / step).astype(int))
        for i in range(len(seg)):
            t = np.arange(k[i]) / k[i]; pts.append(a[i] + seg[i] * t[:, None])
        pts.append(a[-1:])
    return np.vstack(pts)


con = sqlite3.connect(os.path.join(HIST, "osrivers", "Data", "oprvrs_gb.gpkg"))
rv = pd.read_sql("select watercourse_name n, length l from watercourse_link where form != 'canal' and watercourse_name is not null", con)
big = set(rv.groupby("n").l.sum().loc[lambda s: s >= 40000].index)
lines = []
for g, n in con.execute("select geometry, watercourse_name from watercourse_link where form != 'canal' and watercourse_name is not null"):
    if n in big: lines += decode(g)
river_d = cKDTree(densify(lines)).query(np.c_[X, Y])[0]
roads = json.load(open(os.path.join(HIST, "how-roman-is-your-road", "data", "itinere_gb.geojson")))
rl = []
for f in roads["features"]:
    if f["properties"]["cert"] == "Hypothetical": continue
    g = f["geometry"]; parts = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    for part in parts:
        a = np.array(part); x, y = to_bng.transform(a[:, 0], a[:, 1]); rl.append(np.c_[x, y])
road_d = cKDTree(densify(rl)).query(np.c_[X, Y])[0]
cl = []
for g in json.load(open(os.path.join(HIST, "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0])
        if a[:, 0].min() < -5.5 and a[:, 1].max() < 55.5 and a[:, 0].max() < -5.3: continue  # Ireland
        x, y = to_bng.transform(a[:, 0], a[:, 1]); cl.append(np.c_[x, y])
coast_d = cKDTree(densify(cl, 200)).query(np.c_[X, Y])[0]
P["river_km"] = np.round(river_d / 1000, 2); P["roman_km"] = np.round(road_d / 1000, 2); P["coast_km"] = np.round(coast_d / 1000, 2)
P["on_river"] = P.river_km <= 1; P["on_roman"] = P.roman_km <= 1; P["coastal"] = P.coast_km <= 3

# ---------- spacing (market places only)
M = P[P.has_market].copy()
MT = cKDTree(np.c_[M.easting_used, M.northing_used])
d, i = MT.query(np.c_[M.easting_used, M.northing_used], k=2)
M["nn_market_km"] = np.round(d[:, 1] / 1000, 2)
fy = M.first_market_any.values; mx, my = M.easting_used.values, M.northing_used.values
ne = []
for k in range(len(M)):
    if np.isnan(fy[k]): ne.append(np.nan); continue
    earlier = np.where(fy < fy[k])[0]
    ne.append(np.hypot(mx[earlier] - mx[k], my[earlier] - my[k]).min() / 1000 if len(earlier) else np.nan)
M["nn_earlier_km"] = np.round(ne, 2)
P = P.merge(M[["name_gaz", "county", "nn_market_km", "nn_earlier_km"]], on=["name_gaz", "county"], how="left")
M = P[P.has_market].copy()
M["granted_first"] = M.first_market_grant.notna() & (M.m_prescriptive == 0)
M["bracton_close"] = M.nn_earlier_km < BRACTON_KM

R = {}
share = lambda s: float(s.mean()) if len(s) else None
R["counts"] = dict(places=int(len(P) + 1), places_placed=int(len(P)), market_places=int(P.has_market.sum()), fair_only=int((~P.has_market).sum()),
                   markets=int(P.n_markets.sum()), fairs=int(P.n_fairs.sum()), counties=int(P.county.nunique()),
                   england_market_places=int((M.country == "England").sum()), wales_market_places=int((M.country == "Wales").sum()),
                   market_lines_granted=int((M.m_charter + M.m_letter_close + M.m_letter_patent + M.m_grant_other).sum()),
                   market_lines_charter=int(M.m_charter.sum()), market_lines_prescriptive=int(M.m_prescriptive.sum()),
                   places_prescriptive=int((M.m_prescriptive > 0).sum()), places_granted_only=int(((M.m_prescriptive == 0) & (M.n_market_grants > 0)).sum()),
                   places_charter=int((M.m_charter > 0).sum()),
                   multi_market_places=int((M.n_markets >= 2).sum()), boroughs=int(M.borough.sum()), mints=int(M.mint.sum()),
                   everitt=int(M.everitt_c1600.sum()), everitt_all=int(P.everitt_c1600.sum()),
                   name_matched=int(M.os_match.isin(["name", "similar name"]).sum()), exact_name=int((M.os_match == "name").sum()),
                   similar_name=int((M.os_match == "similar name").sum()), nearest_only=int((M.os_match == "nearest").sum()), no_place=int((M.os_match == "none").sum()),
                   grid_fixed=int(P.grid_note.notna().sum()), no_grid=1,
                   median_offset_m=float(P[P.os_match == "name"].os_dist_m.median()), p90_offset_m=float(P[P.os_match == "name"].os_dist_m.quantile(.9)),
                   domesday_matched=int(M.dd_place.notna().sum()), domesday_households=int(M.dd_households.notna().sum()),
                   bua_matched=int(M.bua.notna().sum()))
R["counts"]["market_places_all"] = R["counts"]["market_places"] + 1  # Lothingland: a market but no grid reference
R["counts"]["name_matched_share"] = R["counts"]["name_matched"] / R["counts"]["market_places"]

# ---------- outcomes
OUT = ["town", "absorbed", "village", "hamlet", "gone"]
LAB = {"town": "Town or city", "absorbed": "Swallowed by a town", "village": "Village", "hamlet": "Hamlet", "gone": "Gone from the map"}
R["outcomes"] = {o: dict(n=int((M.outcome == o).sum()), share=float((M.outcome == o).mean()), label=LAB[o]) for o in OUT}
R["outcomes_england"] = {o: dict(n=int(((M.outcome == o) & (M.country == "England")).sum()), share=float((M[M.country == "England"].outcome == o).mean())) for o in OUT}
R["outcomes_wales"] = {o: dict(n=int(((M.outcome == o) & (M.country == "Wales")).sum()), share=float((M[M.country == "Wales"].outcome == o).mean())) for o in OUT}
R["town_share"] = float(M.town.mean()); R["urban_share"] = float(M.urban.mean()); R["not_town_share"] = 1 - R["town_share"]
R["village_or_less_share"] = float(M.outcome.isin(["village", "hamlet", "gone"]).mean())
R["hamlet_or_gone"] = int(M.outcome.isin(["hamlet", "gone"]).sum()); R["hamlet_or_gone_share"] = float(M.outcome.isin(["hamlet", "gone"]).mean())
R["all_os_towns_ew"] = None
pp = M[M.pop2021_src == "built-up area"].pop2021
R["pop"] = dict(townsize5k=int((M.bua_any_pop >= 5000).sum()), townsize5k_share=float((M.bua_any_pop >= 5000).mean()),
                village_bua10k=int(((M.outcome == "village") & (M.bua_pop2021 >= 10000)).sum()), n_bua=int(len(pp)), median_bua=float(pp.median()), over5k=int((M.bua_pop2021 >= 5000).sum()), over5k_share=float((M.bua_pop2021 >= 5000).mean()),
                town_median=float(M[M.town & M.bua_pop2021.notna()].bua_pop2021.median()),
                village_parish_median=float(M[(M.outcome == "village") & (M.pop2021_src == "parish")].pop2021.median()) if ((M.outcome == "village") & (M.pop2021_src == "parish")).any() else None)

# ---------- time
def per(y):
    if pd.isna(y): return None
    for lo, hi, k in ((0, 1199, "before 1200"), (1200, 1249, "1200 to 1249"), (1250, 1299, "1250 to 1299"), (1300, 1348, "1300 to 1348"), (1349, 1399, "1349 to 1399"), (1400, 1516, "1400 to 1516")):
        if lo <= y <= hi: return k
    return None


PERIODS = ["before 1200", "1200 to 1249", "1250 to 1299", "1300 to 1348", "1349 to 1399", "1400 to 1516"]
M["period"] = [("prescriptive" if r.m_prescriptive > 0 else per(r.first_market_grant)) for r in M.itertuples()]
R["by_period"] = []
for k in ["prescriptive"] + PERIODS:
    s = M[M.period == k]
    R["by_period"].append(dict(key=k, n=int(len(s)), town=int(s.town.sum()), town_share=share(s.town), urban_share=share(s.urban),
                               gone_share=share(s.outcome.isin(["hamlet", "gone"])), everitt_share=share(s.everitt_c1600)))
R["period"] = {p["key"]: p for p in R["by_period"]}
# grants per decade (every granted market line with a year; and every granted fair line)
gy, fyrs = [], []
for r in P.itertuples():
    gy += [y for k, y in r.market_years if k in ("charter", "letter_close", "letter_patent", "grant_other") and y]
    fyrs += [y for k, y in r.fair_years if k in ("charter", "letter_close", "letter_patent", "grant_other") and y]
gy = pd.Series(gy); fyrs = pd.Series(fyrs)
dec = pd.DataFrame(dict(decade=range(1060, 1520, 10)))
dec["market_grants"] = [int(((gy >= d) & (gy < d + 10)).sum()) for d in dec.decade]
dec["fair_grants"] = [int(((fyrs >= d) & (fyrs < d + 10)).sum()) for d in dec.decade]
fg = M[M.granted_first]
dec["new_places"] = [int(((fg.first_market_grant >= d) & (fg.first_market_grant < d + 10)).sum()) for d in dec.decade]
dec["new_places_town"] = [int(((fg.first_market_grant >= d) & (fg.first_market_grant < d + 10) & fg.town).sum()) for d in dec.decade]
dec.to_csv(os.path.join(DATA, "decades.csv"), index=False)
R["decades"] = dec.to_dict(orient="records")
R["grants"] = dict(total=int(len(gy)), before1200=int((gy < 1200).sum()), y1200_1349=int(((gy >= 1200) & (gy < 1349)).sum()),
                   share_1200_1349=float(((gy >= 1200) & (gy < 1349)).mean()), after1349=int((gy >= 1349).sum()),
                   peak_decade=int(dec.loc[dec.market_grants.idxmax(), "decade"]), peak_n=int(dec.market_grants.max()),
                   d1340s=int(dec.loc[dec.decade == 1340, "market_grants"].iloc[0]), d1350s=int(dec.loc[dec.decade == 1350, "market_grants"].iloc[0]),
                   d1250s=int(dec.loc[dec.decade == 1250, "market_grants"].iloc[0]), d1200s=int(dec.loc[dec.decade == 1200, "market_grants"].iloc[0]),
                   d1300_09=int(dec.loc[dec.decade == 1300, "market_grants"].iloc[0]),
                   mean_per_decade_1200_1349=float(dec[(dec.decade >= 1200) & (dec.decade < 1350)].market_grants.mean()),
                   mean_per_decade_1350_1509=float(dec[(dec.decade >= 1350) & (dec.decade < 1510)].market_grants.mean()),
                   fairs_total=int(len(fyrs)))
R["grant_share_by_years"] = dict(pre1349_town=share(M[M.granted_first & (M.first_market_grant < 1349)].town),
                                 post1349_town=share(M[M.granted_first & (M.first_market_grant >= 1349)].town),
                                 pre1349_n=int((M.granted_first & (M.first_market_grant < 1349)).sum()),
                                 post1349_n=int((M.granted_first & (M.first_market_grant >= 1349)).sum()))
R["prescriptive_town"] = share(M[M.m_prescriptive > 0].town); R["granted_town"] = share(M[M.granted_first].town)
R["prescriptive_n"] = int((M.m_prescriptive > 0).sum()); R["granted_n"] = int(M.granted_first.sum())

# ---------- predictors, one at a time
def grp(mask, name):
    a, b = M[mask], M[~mask]
    t = stats.fisher_exact([[int(a.town.sum()), int(len(a) - a.town.sum())], [int(b.town.sum()), int(len(b) - b.town.sum())]])
    return dict(name=name, n_yes=int(len(a)), town_yes=share(a.town), n_no=int(len(b)), town_no=share(b.town), odds_ratio=float(t[0]) if np.isfinite(t[0]) else None, p=float(t[1]))


hh = M.dd_households
R["single"] = {
    "borough": grp(M.borough, "Borough by 1516"),
    "mint": grp(M.mint, "Had a mint"),
    "prescriptive": grp(M.m_prescriptive > 0, "Market by custom (prescriptive)"),
    "multi": grp(M.n_markets >= 2, "Two or more markets recorded"),
    "fair": grp(M.n_fairs >= 1, "Also had a fair"),
    "river": grp(M.on_river, "Within 1 km of a major river"),
    "roman": grp(M.on_roman, "Within 1 km of a Roman road"),
    "coast": grp(M.coastal, "Within 3 km of the sea"),
    "bracton": grp(M.bracton_close.fillna(False).astype(bool), "Within 10.7 km of an older market"),
    "everitt": grp(M.everitt_c1600, "Market town c.1600 (Everitt)"),
}
# Domesday size bands (places with a Domesday match and a household count)
DB = []
for lo, hi, lab in ((0, 19.99, "under 20"), (20, 39.99, "20 to 39"), (40, 59.99, "40 to 59"), (60, 99.99, "60 to 99"), (100, 1e9, "100 or more")):
    s = M[(hh >= lo) & (hh <= hi)]
    DB.append(dict(band=lab, n=int(len(s)), town_share=share(s.town), urban_share=share(s.urban)))
s = M[M.dd_place.isna() & M.country.eq("England")]
DB.append(dict(band="no Domesday match (England)", n=int(len(s)), town_share=share(s.town), urban_share=share(s.urban)))
R["domesday_bands"] = DB
R["domesday"] = dict(n=int(hh.notna().sum()), median_hh_town=float(M[M.town].dd_households.median()), median_hh_village=float(M[M.outcome == "village"].dd_households.median()),
                     median_hh_hamlet=float(M[M.outcome.isin(["hamlet", "gone"])].dd_households.median()))
R["domesday"]["spearman"] = float(stats.spearmanr(M[hh.notna()].dd_households, M[hh.notna()].town)[0])

# ---------- logistic regression
F = M.copy()
F["log_hh"] = np.log1p(F.dd_households)
F["n_markets2"] = (F.n_markets >= 2).astype(int)
F["fair"] = (F.n_fairs >= 1).astype(int)
F["first_c"] = (F.first_market_any.fillna(F.first_market_any.median()) - 1250) / 100
F["late"] = (F.granted_first & (F.first_market_grant >= 1349)).astype(int)
for c in ("borough", "mint", "on_river", "on_roman", "coastal", "everitt_c1600"): F[c] = F[c].astype(int)
F["presc"] = (F.m_prescriptive > 0).astype(int)
F["bracton"] = F.bracton_close.fillna(False).astype(int)
F["wales"] = (F.country == "Wales").astype(int)
VARS = [("borough", "Borough"), ("mint", "Mint"), ("presc", "Prescriptive market"), ("n_markets2", "Two or more markets"), ("fair", "Has a fair"),
        ("on_river", "Major river within 1 km"), ("on_roman", "Roman road within 1 km"), ("coastal", "Sea within 3 km"),
        ("bracton", "Older market within 10.7 km"), ("late", "First granted 1349 or later")]


def logit(df, vars_, extra=None):
    cols = [v for v, _ in vars_] + (extra or [])
    Xm = sm.add_constant(df[cols].astype(float)); res = sm.Logit(df.town.astype(int), Xm).fit(disp=0)
    ci = res.conf_int()
    rows = [dict(var=v, label=l, odds_ratio=float(np.exp(res.params[v])), lo=float(np.exp(ci.loc[v, 0])), hi=float(np.exp(ci.loc[v, 1])), p=float(res.pvalues[v]))
            for v, l in vars_ + [(e, {"log_hh": "Domesday households (log, per unit)", "wales": "Wales"}[e]) for e in (extra or [])]]
    return dict(n=int(res.nobs), pseudo_r2=float(res.prsquared), rows=rows)


R["model_all"] = logit(F, VARS, ["wales"])
Fd = F[F.dd_households.notna()]
R["model_domesday"] = logit(Fd, VARS, ["log_hh"])
R["or_all"] = {r["var"]: r for r in R["model_all"]["rows"]}
R["or_dd"] = {r["var"]: r for r in R["model_domesday"]["rows"]}
hh_or = [r for r in R["model_domesday"]["rows"] if r["var"] == "log_hh"][0]
R["model_domesday"]["hh_double_or"] = float(hh_or["odds_ratio"] ** math.log(2))
pd.DataFrame([dict(model="all market places", **r) for r in R["model_all"]["rows"]] + [dict(model="Domesday-matched", **r) for r in R["model_domesday"]["rows"]]).to_csv(os.path.join(DATA, "model.csv"), index=False)

# ---------- spacing and Bracton
ge = M[M.granted_first & M.nn_earlier_km.notna()]
R["spacing"] = dict(median_nn_km=float(M.nn_market_km.median()), share_nn_within_bracton=float((M.nn_market_km < BRACTON_KM).mean()),
                    bracton_km=BRACTON_KM, granted_n=int(len(ge)), granted_close=int((ge.nn_earlier_km < BRACTON_KM).sum()),
                    granted_close_share=float((ge.nn_earlier_km < BRACTON_KM).mean()), granted_median_earlier_km=float(ge.nn_earlier_km.median()),
                    close_town=share(ge[ge.nn_earlier_km < BRACTON_KM].town), far_town=share(ge[ge.nn_earlier_km >= BRACTON_KM].town),
                    close_n=int((ge.nn_earlier_km < BRACTON_KM).sum()), far_n=int((ge.nn_earlier_km >= BRACTON_KM).sum()),
                    within5_share=float((ge.nn_earlier_km < 5).mean()))
bins = [0, 2.5, 5, 7.5, BRACTON_KM, 15, 20, 1e9]; labs = ["under 2.5", "2.5 to 5", "5 to 7.5", "7.5 to 10.7", "10.7 to 15", "15 to 20", "20 or more"]
ge = ge.assign(b=pd.cut(ge.nn_earlier_km, bins, labels=labs, right=False))
R["spacing"]["bands"] = [dict(band=l, n=int((ge.b == l).sum()), town_share=share(ge[ge.b == l].town)) for l in labs]

# ---------- Everitt midpoint
E = M[M.everitt_c1600]; NE = M[~M.everitt_c1600]
R["everitt"] = dict(n=int(len(E)), share_of_markets=float(M.everitt_c1600.mean()), town_share=share(E.town), urban_share=share(E.urban),
                    not_n=int(len(NE)), not_town_share=share(NE.town), not_town_n=int(NE.town.sum()),
                    village_now=int(E.outcome.isin(["village", "hamlet", "gone"]).sum()),
                    town_n=int(E.town.sum()),
                    fell=sorted([dict(place=r.place, county=r.county, outcome=r.outcome, pop=None if pd.isna(r.pop2021) else int(r.pop2021), src=r.pop2021_src)
                                 for r in E[E.outcome.isin(["village", "hamlet", "gone"])].itertuples()], key=lambda d: d["place"]))
R["everitt"]["fell_n"] = len(R["everitt"]["fell"])

# ---------- failures and lists
def item(r):
    return dict(place=r.place, county=r.county, first=None if pd.isna(r.first_market_any) else int(r.first_market_any), kind=r.market_kind,
                markets=int(r.n_markets), fairs=int(r.n_fairs), borough=bool(r.borough), hh=None if pd.isna(r.dd_households) else int(r.dd_households),
                outcome=r.outcome, os_name=r.os_name, os_type=r.os_type, pop=None if pd.isna(r.pop2021) else int(r.pop2021), pop_src=r.pop2021_src,
                lat=r.lat, lon=r.lon)


FB = M[M.borough & M.outcome.isin(["hamlet", "gone"])].sort_values("place")
R["failed_boroughs"] = [item(r) for r in FB.itertuples()]
R["failed_boroughs_n"] = len(FB); R["boroughs_village"] = int((M.borough & (M.outcome == "village")).sum())
R["borough_town_share"] = share(M[M.borough].town)
FM = M[(M.n_markets >= 2) & M.outcome.isin(["hamlet", "gone"])].sort_values("place")
R["failed_multi"] = [item(r) for r in FM.itertuples()]
FD = M[(M.dd_households >= 60) & M.outcome.isin(["hamlet", "gone"])].sort_values("dd_households", ascending=False)
R["failed_big_domesday"] = [item(r) for r in FD.itertuples()]
GONE = M[M.outcome == "gone"].sort_values("place")
R["gone_n"] = len(GONE)
R["gone_examples"] = [item(r) for r in GONE.itertuples()]

# named examples used in the text (checked to exist)
EX = {}
for nm, cty in [("Ravenserodd", "Yorkshire"), ("Old Winchelsea", "Sussex"), ("New Winchelsea", "Sussex"), ("Dunwich", "Suffolk"), ("Stratford upon Avon", "Warwickshire"),
                ("Salisbury", "Wiltshire"), ("Liverpool", "Lancashire"), ("Wigan", "Lancashire"), ("Thaxted", "Essex"), ("Ashford", "Kent"), ("Newborough", "Wales"),
                ("Chipping Campden", "Gloucestershire"), ("Castle Combe", "Wiltshire"), ("Lavenham", "Suffolk"), ("Kenfig", "Wales"), ("Torksey", "Lincolnshire"),
                ("Shipden", "Norfolk"), ("Bere Ferrers", "Devon"), ("Newton", "Dorset"), ("Appledore", "Kent"), ("Manchester", "Lancashire"), ("Birmingham", "Warwickshire"),
                ("Leeds", "Yorkshire"), ("Sheffield", "Yorkshire"), ("Hedon", "Yorkshire"), ("Newtown", "Hampshire"), ("Mitchell", "Cornwall"), ("Bossiney", "Cornwall"),
                ("Old Sarum", "Wiltshire"), ("Clopton", "Cambridgeshire"), ("Tan Hill", "Wiltshire"), ("St Benet's Holme", "Norfolk"), ("Brough", "Westmorland")]:
    s = M[(M.place == nm) & (M.county == cty)]
    if not s.empty:
        EX[nm] = item(s.iloc[0])
R["examples"] = EX

# ---------- counties
C = M.groupby("county").agg(n=("town", "size"), town=("town", "sum"), urban=("urban", "sum"), everitt=("everitt_c1600", "sum"), median_nn_km=("nn_market_km", "median")).reset_index()
C["town_share"] = C.town / C.n; C["urban_share"] = C.urban / C.n
C = C.sort_values("town_share", ascending=False)
C.to_csv(os.path.join(DATA, "counties.csv"), index=False)
R["counties"] = C.to_dict(orient="records")
R["county_nn"] = {r.county: float(r.median_nn_km) for r in C.itertuples()}
GC = pd.read_csv(os.path.join(DATA, "grid_checks.csv"))
R["grid_checks"] = dict(n=int(len(GC)), max_offset_m=float(GC.offset_m.max()), median_offset_m=float(GC.offset_m.median()))
CE = C[C.county != "Wales"]
R["county_extremes"] = dict(top=CE.head(3).to_dict(orient="records"), bottom=CE[CE.n >= 20].tail(3).to_dict(orient="records"),
                            most=C.sort_values("n", ascending=False).head(3).to_dict(orient="records"))

# ---------- towns today with no medieval market (context): OS towns and cities in England and Wales
O = pd.read_csv(os.path.join(HIST, "osnames_gb.tsv"), sep="\t", usecols=["name1", "type", "local_type", "x", "y", "country"], dtype=str)
O = O[(O.type == "populatedPlace") & O.local_type.isin(["Town", "City"]) & O.country.isin(["England", "Wales"])]
OX = np.c_[O.x.astype(float), O.y.astype(float)]
dmk = cKDTree(np.c_[M.easting_used, M.northing_used]).query(OX)[0]
R["os_towns"] = dict(n=int(len(O)), with_market_2km=int((dmk <= 2000).sum()), share_with_market_2km=float((dmk <= 2000).mean()))
matched_towns = int(M.town.sum())
R["os_towns"]["market_towns_matched"] = matched_towns

# ---------- headline numbers
R["headline"] = dict(market_places=R["counts"]["market_places"], town_n=R["outcomes"]["town"]["n"], town_share=R["town_share"],
                     absorbed_n=R["outcomes"]["absorbed"]["n"], village_n=R["outcomes"]["village"]["n"],
                     hamlet_gone_n=R["hamlet_or_gone"], gone_n=R["outcomes"]["gone"]["n"])

# ---------- save place data (derived variables only)
keep = ["place", "county", "country", "easting", "northing", "easting_used", "northing_used", "grid_note", "lat", "lon", "n_markets", "n_fairs",
        "m_charter", "m_letter_close", "m_letter_patent", "m_grant_other", "m_prescriptive", "market_kind", "first_market_grant", "first_market_prescriptive",
        "first_market_any", "first_fair_any", "borough", "borough_year", "mint", "everitt_c1600", "harrison_fair_1587",
        "os_name", "os_type", "os_match", "os_dist_m", "outcome", "outcome_note", "bua", "bua_code", "bua_pop2021", "dd_place", "dd_id", "dd_households", "dd_dist_m",
        "parish", "parish_pop2021", "area_bua", "area_bua_pop2021", "river_km", "roman_km", "coast_km", "nn_market_km", "nn_earlier_km"]
OUTD = P[keep].copy()
for c in ("first_market_grant", "first_market_prescriptive", "first_market_any", "first_fair_any", "borough_year", "bua_pop2021", "parish_pop2021", "area_bua_pop2021", "dd_id", "os_dist_m", "dd_dist_m"):
    OUTD[c] = OUTD[c].round().astype("Int64")
OUTD = OUTD.sort_values(["county", "place"])
OUTD.to_csv(os.path.join(DATA, "markets.csv"), index=False)
feats = []
for r in OUTD.itertuples():
    pr = {k: (None if (isinstance(v, float) and np.isnan(v)) or v is pd.NA else (v.item() if hasattr(v, "item") else v)) for k, v in r._asdict().items() if k not in ("Index", "lat", "lon")}
    feats.append(dict(type="Feature", properties=pr, geometry=dict(type="Point", coordinates=[r.lon, r.lat])))
json.dump(dict(type="FeatureCollection", features=feats), open(os.path.join(DATA, "markets.geojson"), "w"), ensure_ascii=False, default=lambda o: None if o is pd.NA else str(o))

# page data: compact rows
OC = {o: i for i, o in enumerate(OUT)}
KC = {"prescriptive": 0, "granted": 1, "none": 2, "unclear": 1}
rows = []
for r in P.itertuples():
    rows.append([r.place, r.county, round(r.lat, 4), round(r.lon, 4), None if pd.isna(r.first_market_any) else int(r.first_market_any),
                 KC.get(r.market_kind, 2), int(r.n_markets), int(r.n_fairs), int(r.borough) + 2 * int(r.mint) + 4 * int(r.everitt_c1600),
                 OC[r.outcome], r.os_name if r.os_match != "none" else None, None if pd.isna(r.pop2021) else int(r.pop2021),
                 {"built-up area": 1, "parish": 2}.get(r.pop2021_src, 0), None if pd.isna(r.dd_households) else int(r.dd_households),
                 None if pd.isna(r.first_market_grant) else int(r.first_market_grant), r.os_type if r.os_match != "none" else None])
json.dump(dict(cols=["place", "county", "lat", "lon", "first", "kind", "nm", "nf", "flags", "out", "os", "pop", "popsrc", "hh", "grant", "ostype"], rows=rows),
          open(os.path.join(DATA, "page_data.json"), "w"), ensure_ascii=False, separators=(",", ":"))
R["county_dates"] = json.load(open(os.path.join(ROOT, "work", "county_dates.json")))
json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, ensure_ascii=False, default=lambda o: None if o is pd.NA else (o.item() if hasattr(o, "item") else str(o)))
print(json.dumps({k: R[k] for k in ("counts", "outcomes", "town_share", "grants", "grant_share_by_years", "spacing", "everitt", "domesday", "pop", "os_towns")}, indent=0, default=str)[:6000])
for k in ("model_all", "model_domesday"):
    print(k, R[k]["n"], round(R[k]["pseudo_r2"], 3))
    for r in R[k]["rows"]: print(f"   {r['label']:40s} {r['odds_ratio']:.2f} ({r['lo']:.2f} to {r['hi']:.2f}) p={r['p']:.3g}")
for k, v in R["single"].items(): print(k, v)
print(R["by_period"]); print(R["domesday_bands"]); print(len(R["failed_boroughs"]), [f["place"] for f in R["failed_boroughs"]])
print(R["everitt"]["fell_n"], [f["place"] for f in R["everitt"]["fell"]])
