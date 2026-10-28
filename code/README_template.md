# Market towns that failed

What became of the medieval market places of England and Wales? Between the Norman Conquest and 1516 the Crown licensed markets in their thousands, each one a bet that a place would grow into a town. This study follows every place with a market in the Gazetteer of Markets and Fairs in England and Wales to 1516 to today, and asks which became towns and which are villages or fields now.

**Interactive version:** https://tristan-hotham.github.io/medieval-markets/

This repository holds the interactive page, derived data and the analysis code for the data study *Market towns that failed: what became of the medieval market places of England and Wales* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Paper and archived release: https://doi.org/10.5281/zenodo.23727144

## Headline results

- The Gazetteer has {{counts.places|int}} places with {{counts.markets|int}} markets and {{counts.fairs|int}} fairs; {{counts.market_places|int}} placed places have at least one market ({{counts.england_market_places|int}} in England, {{counts.wales_market_places|int}} in Wales).
- It records {{counts.market_lines_granted|int}} royal market grants ({{counts.market_lines_charter|int}} by charter) and {{counts.market_lines_prescriptive|int}} markets held by custom. {{grants.share_1200_1349|pct0}} of grants fall in 1200 to 1348; the peak decade is the {{grants.peak_decade|raw}}s with {{grants.peak_n|int}}; the 1350s have {{grants.d1350s|int}}.
- Today {{outcomes.town.n|int}} market places ({{outcomes.town.share|pct0}}) are towns or cities, {{outcomes.absorbed.n|int}} ({{outcomes.absorbed.share|pct0}}) have been swallowed by a bigger town, {{outcomes.village.n|int}} ({{outcomes.village.share|pct0}}) are villages, {{outcomes.hamlet.n|int}} are hamlets and {{outcomes.gone.n|int}} have gone from the map.
- {{period.prescriptive.town_share|pct0}} of markets held by custom are towns today; for first grants the share falls from {{period.1200 to 1249.town_share|pct0}} (1200 to 1249) to {{period.1250 to 1299.town_share|pct0}} (1250 to 1299) and {{period.1300 to 1348.town_share|pct0}} (1300 to 1348).
- {{spacing.granted_close_share|pct0}} of granted markets lay within Bracton's six and two-thirds miles ({{spacing.bracton_km|km1}} km) of an older market; {{spacing.close_town|pct0}} of those are towns today against {{spacing.far_town|pct0}} of the rest.
- Logistic regression ({{model_all.n|int}} places): borough odds ratio {{or_all.borough.odds_ratio|f2}}, mint {{or_all.mint.odds_ratio|f2}}, prescriptive market {{or_all.presc.odds_ratio|f2}}, fair {{or_all.fair.odds_ratio|f2}}, major river {{or_all.on_river.odds_ratio|f2}}, Roman road {{or_all.on_roman.odds_ratio|f2}}, older market within {{spacing.bracton_km|km1}} km {{or_all.bracton.odds_ratio|f2}}.
- {{everitt.town_share|pct0}} of the {{everitt.n|int}} market places on Everitt's list of market towns around 1600 are towns today, against {{everitt.not_town_share|pct0}} of the other {{everitt.not_n|int}}.
- {{failed_boroughs_n|int}} boroughs are hamlets or gone today, among them Ravenserodd, Old Winchelsea, Old Sarum, Castell y Bere and Dryslwyn.

## Files

- `index.html`: the interactive page (Leaflet map with a year slider, outcome filters and place search, charts, tables).
- `header.png`: social card.
- `data/markets.csv` and `data/markets.geojson`: one row per Gazetteer place (derived variables only): county, grid reference as printed and as used (with any correction noted), latitude and longitude, counts of markets and fairs and of markets by kind of evidence, first year with evidence of a granted market, prescriptive market, any market and any fair, borough and mint flags with the first borough year, Everitt c.1600 and Harrison 1587 flags, matched OS Open Names place, its type, match method and distance, outcome, 2022 built-up area and Census 2021 population, Domesday match and households, civil parish population, built-up area around the point, distances to a major river, a Roman road, the coast, the nearest market place and the nearest older market place.
- `data/decades.csv`: market and fair grants per decade, and places whose first market was granted in each decade with how many are towns today.
- `data/counties.csv`: market places, towns today and c.1600 market towns by county.
- `data/model.csv`: logistic regression odds ratios.
- `data/grid_checks.csv`: the grid reference conversion checked on {{grid_checks.n|int}} known places.
- `data/page_data.json`: compact data for the page.
- `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `code/`: Python scripts, run in order: `01_parse.py` (derived variables from the Gazetteer), `02_places.py` (coordinates, OS Open Names, built-up areas, Domesday), `03_analysis.py` (all statistics), `04_build_site.py` (page and README), `05_header.py` (social card), `06_release_figs.py` (paper and blog figures), `07_paper.py` (paper PDF via xelatex), `08_release.py` (blog post and Zenodo files).
- `release/`: paper PDF and LaTeX source, blog post and figures, Zenodo files. `reddit/`: collage and post text.

## Method in brief

**Markets.** The Gazetteer's {{counts.counties|int}} county pages (39 English pre-1974 counties and Wales) were parsed into derived variables. A market's kind is the evidence in brackets at the start of its line (charter, letter close, letter patent, other grant, prescriptive); its year is the first year between 600 and 1540 written in the line (the grant year, or for prescriptive markets the first record). Grid references are two four-digit numbers in hectometres on the National Grid (e.g. Ashford 6008 1428 = 600,800 m E, 142,800 m N), converted from EPSG:27700 to WGS84 with pyproj and checked on {{grid_checks.n|int}} known places (all within {{grid_checks.max_offset_m|int}} m of the OS point). {{counts.grid_fixed|int}} references were corrected: four whose northing is in decametres, and Wigan, Sisland and Trefnant, which lie far from the only place of that name nearby.

**Today.** OS Open Names populated places of the same name within 4 km (similar spellings, contained names and reordered words within 3 km). Outcome: town or city (OS City or Town); swallowed by a town (OS Suburban Area, or a village or hamlet-type entry inside a built-up area of 20,000 or more people, or a lost name next to a town); village (OS Village, or a hamlet-type entry with a same-name built-up area of 1,000 or more); hamlet; gone (name not on the map and no town within 1.5 km). Old Sarum is counted as gone by hand. Census 2021 populations are summed from LSOAs to the 2022 built-up area of the same name.

**Predictors.** Borough and mint flags from the Gazetteer; major river = OS Open Rivers named watercourse of 40 km or more within 1 km; Roman road = Itiner-e conjectured road within 1 km; coast = Natural Earth coastline within 3 km; Bracton distance = 20 miles / 3 = {{spacing.bracton_km|km1}} km to the nearest market place with an earlier first market. Fisher's exact tests and logistic regressions (statsmodels).

**Caveats.** A grant is not proof that a market was held. OS place types are a cartographic judgement. Name matching can misplace a few places. Domesday households could be matched for {{domesday.n|int}} places. All results are associations.

## How to rerun

Python 3 with pandas, numpy, scipy, statsmodels, pyproj, shapely and matplotlib (Playwright for the header, xelatex for the paper). From `code/`: `python3 01_parse.py && python3 02_places.py && python3 03_analysis.py && python3 04_build_site.py`. Inputs are read one folder up and are not included: `_data11/markets_gazetteer.json.gz` (the Gazetteer pages), `osnames_gb.tsv` (OS Open Names), `osrivers/` (OS Open Rivers), `_data8/` (ONS Census 2021 and geography), `domesday-destiny/data/domesday_places.csv`, `how-roman-is-your-road/data/itinere_gb.geojson` and a Natural Earth land outline.

## Sources and licence

- Markets and fairs: {{GAZ_CREDIT}} Now hosted at https://archives.history.ac.uk/gazetteer/ (Centre for Metropolitan History, Institute of Historical Research). The information in the Gazetteer is copyright. This repository contains only derived variables (counts, years, kinds of evidence, flags and converted coordinates), never the Gazetteer's text; please acknowledge the Gazetteer as above when using them.
- Bracton on the Laws and Customs of England, translated by S.E. Thorne, vol. 3, p. 198 (Ames Foundation, Harvard Law School Library): the day's journey of twenty miles in three parts.
- Places: OS Open Names and OS Open Rivers, Ordnance Survey, Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2026.
- Census 2021 and ONS geography lookups: Office for National Statistics, Open Government Licence v3.0.
- Domesday: Hull Domesday Project, Professor J.J.N. Palmer, George Slater and the University of Hull (CC BY-NC-SA), via my Domesday Destiny study.
- Roman roads: de Soto, P., Pažout, A., Brughmans, T. and others (2025), Itiner-e, https://zenodo.org/records/17122148 (CC BY 4.0).
- Coastline: Natural Earth (public domain). Base map tiles on the page: Esri. Map library: Leaflet.

Because the derived data include Hull Domesday Project figures (CC BY-NC-SA), the derived data and the page text are released under CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/). Code is MIT (see `LICENSE`).

Companion studies: [Is Domesday destiny?](https://tristan-hotham.github.io/domesday-destiny/) and [Minted: the Anglo-Saxon and Norman mint towns](https://tristan-hotham.github.io/saxon-mints/).

## Citation

Hotham, T. (2026) *Market towns that failed: what became of the medieval market places of England and Wales*. Zenodo. https://doi.org/10.5281/zenodo.23727144

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
