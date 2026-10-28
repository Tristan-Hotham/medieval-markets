"""Step 2. Place every Gazetteer market on the map and find what is there today.

1. Coordinates: the Gazetteer's hectometre grid reference (OSGB36 National Grid, EPSG:27700) is
   converted to WGS84 latitude and longitude with pyproj. The conversion is checked on known
   places (CHECKS below: OS Open Names coordinates of the town of the same name).
2. Today: OS Open Names populated places (Ordnance Survey, OGL v3). A market place is matched to
   the nearest OS populated place of the same name (letters only, ignoring case, "St"/"Saint",
   apostrophes, hyphens, ", Isle of Wight" and any Welsh alternative after "/") within 4 km of
   the grid reference. If none, the nearest OS populated place of any name within 1.5 km is
   recorded instead, and the outcome is flagged as a match by distance. Its OS local type (City,
   Town, Village, Hamlet, Other Settlement, Suburban Area) is the outcome.
3. Population: Census 2021 usual residents of the 2022 built-up area (BUA22) of the same name
   whose centroid lies within 6 km (LSOA populations summed by best-fit lookup, ONS, OGL v3).
   Without such a built-up area: the civil parish population of a matched Domesday place.
4. Domesday: Domesday place of the same name within 4 km (Hull Domesday Project households 1086,
   via domesday-destiny/data/domesday_places.csv), and that place's parish population in 2021.

Inputs (read in place): work/places_raw.json; ../../osnames_gb.tsv; ../../_data8/ons_geo.json,
lsoa21_bua22_lookup.json, census/census2021-ts001-lsoa.csv; ../../domesday-destiny/data/domesday_places.csv
Output: work/places_today.json, data/grid_checks.csv
Run: python3 02_places.py
"""
import json, os, re
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); HIST = os.path.join(ROOT, "..")
D8 = os.path.join(HIST, "_data8")
P = pd.DataFrame(json.load(open(os.path.join(ROOT, "work", "places_raw.json"))))
to_wgs = Transformer.from_crs(27700, 4326, always_xy=True)


def norm(s):
    s = str(s).lower().replace("�", "'").replace("’", "'")
    s = re.sub(r",\s*isle of wight", "", s)
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\bsaint\b", "st", s); s = re.sub(r"\bst\.", "st", s)
    return re.sub(r"[^a-z]", "", s)


def names(gaz):
    out = []
    for part in re.split(r"\s*/\s*", gaz):
        n = norm(part)
        if n: out.append(n)
    return out


def display(gaz):
    s = gaz.replace("�", "'").replace("’", "'")
    s = s.split(" / ")[0] if " / " in s else s.split("/")[0]
    w = []
    for t in re.split(r"(\s+|-)", s.title()):
        w.append(t.lower() if t.lower() in ("upon", "on", "le", "in", "the", "de", "of", "by", "under", "next", "cum", "and", "en", "la") and w else t)
    s = "".join(w).replace("'S ", "'s ").replace("'S", "'s")
    s = re.sub(r"\bSt\.", "St", s)
    return s


ll = to_wgs.transform(P.easting.fillna(0).values, P.northing.fillna(0).values)
P["lon"] = np.where(P.easting.notna(), np.round(ll[0], 5), np.nan)
P["lat"] = np.where(P.easting.notna(), np.round(ll[1], 5), np.nan)
P["place"] = [display(n) for n in P.name_gaz]
P["keys"] = [names(n) for n in P.name_gaz]

# --- OS Open Names populated places
O = pd.read_csv(os.path.join(HIST, "osnames_gb.tsv"), sep="\t", usecols=["name1", "name2", "type", "local_type", "lat", "lon", "x", "y", "district", "county", "country"], dtype=str)
O = O[(O.type == "populatedPlace") & O.country.isin(["England", "Wales"])].copy()
for c in ("lat", "lon", "x", "y"): O[c] = O[c].astype(float)
O = O.reset_index(drop=True)
O["k1"] = O.name1.map(norm); O["k2"] = O.name2.fillna("").map(norm)
OT = cKDTree(O[["x", "y"]].values)
byname = {}
for i, (a, b) in enumerate(zip(O.k1, O.k2)):
    byname.setdefault(a, []).append(i)
    if b: byname.setdefault(b, []).append(i)

# --- Domesday places
DD = pd.read_csv(os.path.join(HIST, "domesday-destiny", "data", "domesday_places.csv"))
DD = DD[DD.lat.notna()].reset_index(drop=True)
to_bng = Transformer.from_crs(4326, 27700, always_xy=True)
DD["x"], DD["y"] = to_bng.transform(DD.lng.values, DD.lat.values)
DD["k"] = DD.name.map(norm)
ddname = {}
for i, k in enumerate(DD.k): ddname.setdefault(k, []).append(i)

# --- BUA22 populations
geo = json.load(open(os.path.join(D8, "ons_geo.json")))
lk = pd.DataFrame(json.load(open(os.path.join(D8, "lsoa21_bua22_lookup.json"))))
c21 = pd.read_csv(os.path.join(D8, "census", "census2021-ts001-lsoa.csv")); c21.columns = ["date", "name", "code", "pop", "hh", "ce"]
lk = lk.merge(c21[["code", "pop"]], left_on="LSOA21CD", right_on="code", how="left")
BP = lk.groupby(["BUA22CD", "BUA22NM"])["pop"].sum().reset_index()
BG = pd.DataFrame(geo["bua22_gb"])[["BUA22CD", "BNG_E", "BNG_N", "Shape__Area"]]
BP = BP.merge(BG, on="BUA22CD", how="left")
BP["k"] = [norm(re.sub(r"\s*\(.*\)$", "", n)) for n in BP.BUA22NM]
buaname = {}
for i, k in enumerate(BP.k): buaname.setdefault(k, []).append(i)


def nearest_named(keys, x, y, index, X, Y, maxd):
    best = None
    for k in keys:
        for i in index.get(k, []):
            d = float(np.hypot(X[i] - x, Y[i] - y))
            if d <= maxd and (best is None or d < best[1]): best = (i, d)
    return best


import difflib

STOP = {"in", "the", "le", "on", "upon", "de", "la", "of", "by", "next", "cum"}


def tokens(name):
    """Sorted significant words of a name (word order variants: Soham Earl / Earl Soham; Burgh in the Marsh / Burgh le Marsh)."""
    if not isinstance(name, str): return ()
    w = [re.sub(r"[^a-z]", "", t) for t in re.split(r"[\s\-]+", name.lower().replace("\u2019", "'").split("/")[0])]
    return tuple(sorted(t for t in w if t and t not in STOP))


def fuzzy_named(keys, x, y, maxd, tkeys):
    """OS populated place within maxd whose name contains, or is contained in, the market's name,
    or is at least 0.85 similar (spelling variants such as Hurstpierpont / Hurstpierpoint)."""
    idx = OT.query_ball_point([x, y], maxd); best = None
    for i in idx:
        for ok, raw in ((O.k1[i], O.name1[i]), (O.k2[i], O.name2[i])):
            if not ok: continue
            for k, kt in zip(keys, tkeys):
                sim = difflib.SequenceMatcher(None, k, ok).ratio()
                ot = tokens(raw)
                tok = (kt == ot and len(kt) > 1) or any(len(t) >= 6 and difflib.SequenceMatcher(None, t, ok).ratio() >= 0.9 for t in kt)
                if (len(k) >= 4 and len(ok) >= 4 and (k in ok or ok in k)) or sim >= 0.85 or tok:
                    d = float(np.hypot(OX[i] - x, OY[i] - y))
                    if best is None or d < best[1]: best = (i, d)
    return best


def relocate(r):
    """Where no OS place of the same or a similar name lies near the grid reference, test two slips:
    a northing written in decametres (some south-western entries), and failing that a single OS
    populated place of exactly the same name within 12 km, or a single town or city of that name
    within 40 km. Returns (x, y, note) or None."""
    for fx, fy, note in ((1, 0.1, "northing read as decametres (a leading zero appears to be missing)"),):
        x, y = r.easting * fx, r.northing * fy
        m = nearest_named(r.keys, x, y, byname, OX, OY, 1500)
        if m: return x, y, note
    if OT.query([r.easting, r.northing])[0] > 5000 and OT.query([r.easting, r.northing / 10])[0] <= 1500:
        return r.easting, r.northing / 10, "northing read as decametres (a leading zero appears to be missing; the grid reference as printed falls far from any settlement)"
    cands = sorted({i for k in r.keys for i in byname.get(k, []) if np.hypot(OX[i] - r.easting, OY[i] - r.northing) <= 40000})
    if len(cands) == 1:
        i = cands[0]; d = np.hypot(OX[i] - r.easting, OY[i] - r.northing)
        if d <= 12000 or O.local_type[i] in ("Town", "City"):
            return OX[i], OY[i], f"placed at the only OS place of that name within {'12' if d <= 12000 else '40'} km (grid reference appears mistyped)"
    return None


rows = []
OX, OY = O.x.values, O.y.values
for r in P.itertuples():
    out = dict(idx=r.Index)
    if pd.isna(r.easting):
        rows.append(out); continue
    x, y = r.easting, r.northing
    tkeys = [tokens(p) for p in re.split(r"\s*/\s*", r.name_gaz)][:len(r.keys)]
    tkeys += [()] * (len(r.keys) - len(tkeys))
    m = nearest_named(r.keys, x, y, byname, OX, OY, 4000)
    if not m and not fuzzy_named(r.keys, x, y, 3000, tkeys):
        fix = relocate(r)
        if fix:
            x, y, note = fix; out.update(x=x, y=y, grid_note=note)
            m = nearest_named(r.keys, x, y, byname, OX, OY, 4000)
    if m:
        o = O.iloc[m[0]]; out.update(os_name=o.name1, os_type=o.local_type, os_dist_m=round(m[1]), os_match="name", os_district=o.district)
    else:
        f = fuzzy_named(r.keys, x, y, 3000, tkeys)
        if f:
            o = O.iloc[f[0]]; out.update(os_name=o.name1, os_type=o.local_type, os_dist_m=round(f[1]), os_match="similar name", os_district=o.district)
        else:
            d, i = OT.query([x, y])
            if d <= 1500:
                o = O.iloc[i]; out.update(os_name=o.name1, os_type=o.local_type, os_dist_m=round(d), os_match="nearest", os_district=o.district)
            else:
                out.update(os_name=None, os_type="None within 1.5 km", os_dist_m=round(d), os_match="none", os_district=None)
    keys = list(r.keys) + ([norm(out["os_name"])] if out.get("os_match") in ("name", "similar name") else [])
    b = nearest_named(keys, x, y, buaname, BP.BNG_E.values, BP.BNG_N.values, 6000)
    if b:
        q = BP.iloc[b[0]]; out.update(bua=q.BUA22NM, bua_code=q.BUA22CD, bua_pop2021=int(q["pop"]), bua_dist_m=round(b[1]))
    dm = nearest_named(r.keys, x, y, ddname, DD.x.values, DD.y.values, 4000)
    if dm:
        q = DD.iloc[dm[0]]
        out.update(dd_place=q["name"], dd_id=int(q.placeId), dd_households=None if pd.isna(q.households1086) else float(q.households1086),
                   dd_burgesses=None if pd.isna(q.burgesses1086) else float(q.burgesses1086),
                   dd_dist_m=round(dm[1]), parish=None if pd.isna(q.parishName) else q.parishName,
                   parish_pop2021=None if pd.isna(q.parishResidents2021) else int(q.parishResidents2021))
    rows.append(out)
T = pd.DataFrame(rows).set_index("idx")
P = P.join(T)
# Built-up area around the point: the 2022 built-up area (best fit) of the nearest MSOA population-weighted
# centroid, if that centroid lies within 1 km (used to tell villages and hamlets from districts of big towns)
MS = pd.DataFrame(geo["msoa21_pwc"]).merge(pd.DataFrame(geo["msoa21_bua22_lookup"])[["MSOA21CD", "BUA22CD", "BUA22NM"]], on="MSOA21CD", how="left")
MS["x"], MS["y"] = to_bng.transform(MS["_x"].values, MS["_y"].values)
MS = MS.merge(BP[["BUA22CD", "pop"]], on="BUA22CD", how="left")
MT = cKDTree(MS[["x", "y"]].values)
ex = np.where(P.x.notna(), P.x, P.easting).astype(float); ny = np.where(P.y.notna(), P.y, P.northing).astype(float)
ok = ~np.isnan(ex)
d, i = MT.query(np.c_[ex[ok], ny[ok]])
P.loc[ok, "msoa_dist_m"] = np.round(d)
P.loc[ok, "area_bua"] = np.where(d <= 1000, MS.BUA22NM.values[i], None)
P.loc[ok, "area_bua_pop2021"] = np.where(d <= 1000, MS["pop"].values[i], np.nan)
fx = P.x.notna()
P.loc[fx, "easting_used"] = P.loc[fx, "x"]; P.loc[~fx, "easting_used"] = P.loc[~fx, "easting"]
P.loc[fx, "northing_used"] = P.loc[fx, "y"]; P.loc[~fx, "northing_used"] = P.loc[~fx, "northing"]
ll = to_wgs.transform(P.easting_used.fillna(0).values, P.northing_used.fillna(0).values)
P["lon"] = np.where(P.easting_used.notna(), np.round(ll[0], 5), np.nan)
P["lat"] = np.where(P.easting_used.notna(), np.round(ll[1], 5), np.nan)
print(P[P.grid_note.notna()][["place", "county", "easting", "northing", "easting_used", "northing_used", "grid_note", "os_name"]].to_string())

# --- grid reference checks against OS Open Names (town centres of the same name)
CHECKS = ["ASHFORD", "APPLEDORE", "YORK", "STAMFORD", "LUDLOW", "BOSTON", "TOTNES", "KENDAL", "HELSTON", "BERWICK UPON TWEED",
          "CARDIFF / CAERDYDD", "ST IVES", "THAXTED", "CHIPPING CAMPDEN", "SHEPTON MALLET", "BISHOP’S STORTFORD"]
ck = []
for g in CHECKS:
    for r in P[P.name_gaz == g].itertuples():
        ck.append(dict(place=r.place, county=r.county, grid_easting=r.easting, grid_northing=r.northing, lat=r.lat, lon=r.lon,
                       os_name=r.os_name, os_type=r.os_type, offset_m=r.os_dist_m))
CK = pd.DataFrame(ck)
CK.to_csv(os.path.join(ROOT, "data", "grid_checks.csv"), index=False)
print(CK.to_string())
P.drop(columns=["keys", "x", "y"]).to_json(os.path.join(ROOT, "work", "places_today.json"), orient="records", force_ascii=False)
print(P.os_match.value_counts(dropna=False)); print(P.os_type.value_counts(dropna=False))
print("median offset name matches (m):", P[P.os_match == "name"].os_dist_m.median(), " 90th pct:", P[P.os_match == "name"].os_dist_m.quantile(.9))
print("BUA:", P.bua.notna().sum(), " Domesday:", P.dd_place.notna().sum(), " Domesday households:", P.dd_households.notna().sum())
