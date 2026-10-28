"""Step 1. Parse the Gazetteer of Markets and Fairs in England and Wales to 1516 into derived variables.

Source: Samantha Letters, Online Gazetteer of Markets and Fairs in England and Wales to 1516,
https://archives.history.ac.uk/gazetteer/ (Centre for Metropolitan History), one HTML page per
pre-1974 county plus Wales, read in place from ../../_data11/markets_gazetteer.json.gz.

The Gazetteer is copyright. This script keeps ONLY derived variables: place name, county,
grid reference converted to coordinates, counts of markets and fairs, the kind of evidence
(charter, letter close, letter patent, other grant, prescriptive), the earliest year of each
kind, and flags (borough, mint, market town c.1600 in Everitt's list, fair in 1587 in Harrison,
a 1334 lay subsidy valuation given). No sentence of the Gazetteer's text is written out.

Each place entry begins with the name in capitals and a grid reference written as two numbers
in hectometres (e.g. ASHFORD 6008 1428 = easting 600,800 m, northing 142,800 m, OSGB36 National
Grid). Each M (market) or F (fair) line begins with its kind in brackets.
Year of a market or fair: the first year between 600 and 1540 written in the line (for grants
this is the year of the grant date "gr 13 Oct 1243"; for prescriptive markets, the year first
recorded). Ranges like 1114x40 give the first year.

Output: ../work/places_raw.json (one record per place, derived variables only) and
../work/county_dates.json (each county page's "last updated" date, for the credit line).
Run: python3 01_parse.py
"""
import gzip, html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
SRC = os.path.join(ROOT, "..", "_data11", "markets_gazetteer.json.gz")
G = json.load(gzip.open(SRC))["pages"]
SKIP = {"templ.html", "summy.html", "places.html", "counties.html"}
COUNTY = {"beds": "Bedfordshire", "berks": "Berkshire", "bucks": "Buckinghamshire", "cambs": "Cambridgeshire",
          "cheshire": "Cheshire", "cornwall": "Cornwall", "cumb": "Cumberland", "derbys": "Derbyshire", "devon": "Devon",
          "dorset": "Dorset", "durham": "County Durham", "essex": "Essex", "gloucs": "Gloucestershire",
          "hants": "Hampshire", "herefs": "Herefordshire", "herts": "Hertfordshire", "hunts": "Huntingdonshire",
          "kent": "Kent", "lancs": "Lancashire", "leics": "Leicestershire", "lincs": "Lincolnshire", "middx": "Middlesex",
          "norf": "Norfolk", "nhants": "Northamptonshire", "northum": "Northumberland", "notts": "Nottinghamshire",
          "oxon": "Oxfordshire", "rutland": "Rutland", "salop": "Shropshire", "somer": "Somerset",
          "staffs": "Staffordshire", "suff": "Suffolk", "surrey": "Surrey", "sussex": "Sussex",
          "warws": "Warwickshire", "westmor": "Westmorland", "wilts": "Wiltshire", "worcs": "Worcestershire",
          "yorks": "Yorkshire", "wales": "Wales"}


def clean(s):
    s = re.sub(r"</?(?:font|i|a)\b[^>]*>", "", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("\x96", " ").replace("–", " ").replace("—", " ")
    return re.sub(r"\s+", " ", s).strip()


def kind(t):
    m = re.match(r"\s*\(([^)]*)\)", t)
    k = (m.group(1) if m else "").lower()
    if "prescriptive" in k:
        return "prescriptive"
    if k.startswith("charter"):
        return "charter"
    if "letter close" in k:
        return "letter_close"
    if "letter patent" in k:
        return "letter_patent"
    if k.startswith("grant"):
        return "grant_other"
    return "unclear"


def year(t):
    t = re.sub(r"^\s*\([^)]*\)", "", t)
    for m in re.finditer(r"(?<![\d/])(\d{3,4})(?![\d])", t):
        y = int(m.group(1))
        if 600 <= y <= 1540:
            return y
    return None


def parse_page(fn, page):
    rows = re.findall(r"<tr.*?</tr>", page, flags=re.S | re.I)
    places, cur = [], None
    for r in rows:
        if re.search(r"colspan=\"?3", r, flags=re.I):
            b = re.search(r"<b>(.*?)</b>", r, flags=re.S | re.I)
            txt = clean(r)
            name = clean(b.group(1)).rstrip(".,") if b else ""
            if name and len(name) > 1 and name.upper() == name and re.search(r"[A-Z]", name):
                rest = txt[txt.find(name) + len(name):] if name in txt else txt
                rest = re.sub(r"^(\s*\d{2}) (\d{2}) (\d{3,4})\b", r"\1\2 \3", rest)
                g = re.match(r"\s*\.?\s*(\d{3,4})\.?\s+(\d{3,4})\b", rest)
                cur = dict(name=name, file=fn, county=COUNTY[fn[:-5]], e_hm=int(g.group(1)) if g else None,
                           n_hm=int(g.group(2)) if g else None, head=rest, lines=[])
                places.append(cur)
            elif cur is not None:
                cur["head"] += " " + txt
            continue
        if cur is None:
            continue
        tds = re.findall(r"<td.*?</td>", r, flags=re.S | re.I)
        if len(tds) >= 3:
            mf, body = clean(tds[1]), clean(tds[2])
            if mf in ("M", "F"):
                cur["lines"].append((mf, kind(body), year(body), body))
            elif mf == "" and re.match(r"\s*[MF]\s*\(", body):
                cur["lines"].append((body.strip()[0], kind(body.strip()[1:]), year(body.strip()[1:]), body))
    return places


def derive(p):
    h = p["head"]
    bor = re.search(r"\bBorough\b[^.;(]*?(\d{3,4})", h)
    out = dict(place=p["name"].title().replace("'S", "'s").replace("’S", "’s"), name_gaz=p["name"], county=p["county"],
               country="Wales" if p["file"] == "wales.html" else "England",
               easting=p["e_hm"] * 100 if p["e_hm"] is not None else None,
               northing=p["n_hm"] * 100 if p["n_hm"] is not None else None,
               borough=bool(re.search(r"(?:^|[.;]\s*)Borough\b", h)) or any("borough" in l[3][:40].lower() and l[1] == "prescriptive" for l in p["lines"]), borough_year=int(bor.group(1)) if bor else None,
               mint=bool(re.search(r"(?:^|[.;]\s*)Mint\b", h)) or any("mint" in l[3][:40].lower() and l[1] == "prescriptive" for l in p["lines"]),
               everitt_c1600=bool(re.search(r"Market town c\s*\.?\s*1600", h)),
               harrison_fair_1587=bool(re.search(r"Fair 1587", h)),
               subsidy1334=None)
    s = re.search(r"1334 (?:Lay )?Subsidy\s*\W?\s*£?\s*([\d,]+(?:\.\d+)?)", h.replace("�", "£"))
    if s:
        try:
            out["subsidy1334"] = float(s.group(1).replace(",", ""))
        except ValueError:
            pass
    M = [l for l in p["lines"] if l[0] == "M"]; F = [l for l in p["lines"] if l[0] == "F"]
    out["n_markets"] = len(M); out["n_fairs"] = len(F)
    for k in ("charter", "letter_close", "letter_patent", "grant_other", "prescriptive", "unclear"):
        out[f"m_{k}"] = sum(1 for l in M if l[1] == k)
    granted = [l[2] for l in M if l[1] in ("charter", "letter_close", "letter_patent", "grant_other") and l[2]]
    presc = [l[2] for l in M if l[1] == "prescriptive" and l[2]]
    allm = [l[2] for l in M if l[2]]
    allf = [l[2] for l in F if l[2]]
    out["first_market_grant"] = min(granted) if granted else None
    out["first_market_prescriptive"] = min(presc) if presc else None
    out["first_market_any"] = min(allm) if allm else None
    out["first_fair_any"] = min(allf) if allf else None
    out["first_any"] = min(allm + allf) if allm + allf else None
    out["market_kind"] = ("prescriptive" if out["m_prescriptive"] else "granted" if granted or any(l[1] != "unclear" for l in M) else
                          "none" if not M else "unclear")
    out["n_market_grants"] = len(granted)
    out["market_years"] = [[l[1], l[2]] for l in M]
    out["fair_years"] = [[l[1], l[2]] for l in F]
    return out


if __name__ == "__main__":
    P, dates = [], {}
    for fn, page in G.items():
        if fn in SKIP:
            continue
        lu = re.search(r"(?i)Last updated:\s*(?:</font>)?\s*(?:<font[^>]*>)?\s*(?:<!--[^>]*-->)?\s*([0-9]{1,2} [A-Za-z]+,? \d{4})", page)
        dates[COUNTY[fn[:-5]]] = lu.group(1).replace(",", "") if lu else None
        for p in parse_page(fn, page):
            if not p["lines"] and p["e_hm"] is None:
                continue
            P.append(derive(p))
    os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
    json.dump(P, open(os.path.join(ROOT, "work", "places_raw.json"), "w"), ensure_ascii=False)
    json.dump(dates, open(os.path.join(ROOT, "work", "county_dates.json"), "w"), indent=1)
    print(len(P), "places;", sum(p["n_markets"] for p in P), "markets;", sum(p["n_fairs"] for p in P), "fairs")
    print("no grid ref:", [p["place"] + " (" + p["county"] + ")" for p in P if p["easting"] is None])
    print("dates:", dates)
