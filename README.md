# Market towns that failed

What became of the medieval market places of England and Wales? Between the Norman Conquest and 1516 the Crown licensed markets in their thousands, each one a bet that a place would grow into a town. This study follows every place with a market in the Gazetteer of Markets and Fairs in England and Wales to 1516 to today, and asks which became towns and which are villages or fields now.

**Interactive version:** https://tristan-hotham.github.io/medieval-markets/

This repository holds the interactive page, derived data and the analysis code for the data study *Market towns that failed: what became of the medieval market places of England and Wales* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Paper and archived release: https://doi.org/10.5281/zenodo.23727144

## Headline results

- The Gazetteer has 2,411 places with 2,590 markets and 2,936 fairs; 2,173 placed places have at least one market (2,047 in England, 126 in Wales).
- It records 1,879 royal market grants (1,549 by charter) and 710 markets held by custom. 88% of grants fall in 1200 to 1348; the peak decade is the 1250s with 254; the 1350s have 29.
- Today 665 market places (31%) are towns or cities, 144 (7%) have been swallowed by a bigger town, 1,168 (54%) are villages, 129 are hamlets and 67 have gone from the map.
- 54% of markets held by custom are towns today; for first grants the share falls from 29% (1200 to 1249) to 17% (1250 to 1299) and 11% (1300 to 1348).
- 82% of granted markets lay within Bracton's six and two-thirds miles (10.7 km) of an older market; 15% of those are towns today against 41% of the rest.
- Logistic regression (2,173 places): borough odds ratio 3.59, mint 2.88, prescriptive market 2.46, fair 3.10, major river 1.95, Roman road 1.66, older market within 10.7 km 0.54.
- 74% of the 732 market places on Everitt's list of market towns around 1600 are towns today, against 8% of the other 1,441.
- 30 boroughs are hamlets or gone today, among them Ravenserodd, Old Winchelsea, Old Sarum, Castell y Bere and Dryslwyn.

## Files

- `index.html`: the interactive page (Leaflet map with a year slider, outcome filters and place search, charts, tables).
- `header.png`: social card.
- `data/markets.csv` and `data/markets.geojson`: one row per Gazetteer place (derived variables only): county, grid reference as printed and as used (with any correction noted), latitude and longitude, counts of markets and fairs and of markets by kind of evidence, first year with evidence of a granted market, prescriptive market, any market and any fair, borough and mint flags with the first borough year, Everitt c.1600 and Harrison 1587 flags, matched OS Open Names place, its type, match method and distance, outcome, 2022 built-up area and Census 2021 population, Domesday match and households, civil parish population, built-up area around the point, distances to a major river, a Roman road, the coast, the nearest market place and the nearest older market place.
- `data/decades.csv`: market and fair grants per decade, and places whose first market was granted in each decade with how many are towns today.
- `data/counties.csv`: market places, towns today and c.1600 market towns by county.
- `data/model.csv`: logistic regression odds ratios.
- `data/grid_checks.csv`: the grid reference conversion checked on 16 known places.
- `data/page_data.json`: compact data for the page.
- `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `code/`: Python scripts, run in order: `01_parse.py` (derived variables from the Gazetteer), `02_places.py` (coordinates, OS Open Names, built-up areas, Domesday), `03_analysis.py` (all statistics), `04_build_site.py` (page and README), `05_header.py` (social card), `06_release_figs.py` (paper and blog figures), `07_paper.py` (paper PDF via xelatex), `08_release.py` (blog post and Zenodo files).
- `release/`: paper PDF and LaTeX source, blog post and figures, Zenodo files. `reddit/`: collage and post text.

## Method in brief

**Markets.** The Gazetteer's 40 county pages (39 English pre-1974 counties and Wales) were parsed into derived variables. A market's kind is the evidence in brackets at the start of its line (charter, letter close, letter patent, other grant, prescriptive); its year is the first year between 600 and 1540 written in the line (the grant year, or for prescriptive markets the first record). Grid references are two four-digit numbers in hectometres on the National Grid (e.g. Ashford 6008 1428 = 600,800 m E, 142,800 m N), converted from EPSG:27700 to WGS84 with pyproj and checked on 16 known places (all within 962 m of the OS point). 7 references were corrected: four whose northing is in decametres, and Wigan, Sisland and Trefnant, which lie far from the only place of that name nearby.

**Today.** OS Open Names populated places of the same name within 4 km (similar spellings, contained names and reordered words within 3 km). Outcome: town or city (OS City or Town); swallowed by a town (OS Suburban Area, or a village or hamlet-type entry inside a built-up area of 20,000 or more people, or a lost name next to a town); village (OS Village, or a hamlet-type entry with a same-name built-up area of 1,000 or more); hamlet; gone (name not on the map and no town within 1.5 km). Old Sarum is counted as gone by hand. Census 2021 populations are summed from LSOAs to the 2022 built-up area of the same name.

**Predictors.** Borough and mint flags from the Gazetteer; major river = OS Open Rivers named watercourse of 40 km or more within 1 km; Roman road = Itiner-e conjectured road within 1 km; coast = Natural Earth coastline within 3 km; Bracton distance = 20 miles / 3 = 10.7 km to the nearest market place with an earlier first market. Fisher's exact tests and logistic regressions (statsmodels).

**Caveats.** A grant is not proof that a market was held. OS place types are a cartographic judgement. Name matching can misplace a few places. Domesday households could be matched for 1,288 places. All results are associations.

## How to rerun

Python 3 with pandas, numpy, scipy, statsmodels, pyproj, shapely and matplotlib (Playwright for the header, xelatex for the paper). From `code/`: `python3 01_parse.py && python3 02_places.py && python3 03_analysis.py && python3 04_build_site.py`. Inputs are read one folder up and are not included: `_data11/markets_gazetteer.json.gz` (the Gazetteer pages), `osnames_gb.tsv` (OS Open Names), `osrivers/` (OS Open Rivers), `_data8/` (ONS Census 2021 and geography), `domesday-destiny/data/domesday_places.csv`, `how-roman-is-your-road/data/itinere_gb.geojson` and a Natural Earth land outline.

## Sources and licence

- Markets and fairs: Samantha Letters, Online Gazetteer of Markets and Fairs in England and Wales to 1516 <http://www.history.ac.uk/cmh/gaz/gazweb2.html>: Bedfordshire (last updated 27 February 2007); Berkshire (last updated 17 November 2006); Buckinghamshire (last updated 23 February 2005); Cambridgeshire (last updated 23 February 2005); Cheshire (last updated 12 April 2010); Cornwall (last updated 17 November 2006); Cumberland (last updated 17 November 2006); Derbyshire (last updated 26 February 2007); Devon (last updated 14 July 2010); Dorset (last updated 23 July 2007); County Durham (last updated 15 July 2010); Essex (last updated 16 November 2006); Gloucestershire (last updated 15 July 2010); Hampshire (last updated 17 November 2006); Herefordshire (last updated 23 February 2005); Hertfordshire (last updated 23 February 2005); Huntingdonshire (last updated 17 November 2006); Kent (last updated 26 February 2007); Lancashire (last updated 14 July 2010); Leicestershire (last updated 23 February 2005); Lincolnshire (last updated 17 November 2006); Middlesex (last updated 23 February 2005); Norfolk (last updated 17 November 2006); Northamptonshire (last updated 14 July 2010); Northumberland (last updated 23 February 2005); Nottinghamshire (last updated 14 July 2010); Oxfordshire (last updated 23 February 2005); Rutland (last updated 17 November 2006); Shropshire (last updated 14 July 2010); Somerset (last updated 14 July 2010); Staffordshire (last updated 17 November 2006); Suffolk (last updated 17 November 2006); Surrey (last updated 17 November 2006); Sussex (last updated 17 November 2006); Warwickshire (last updated 16 March 2007); Westmorland (last updated 23 February 2005); Wiltshire (last updated 17 November 2006); Worcestershire (last updated 15 July 2010); Yorkshire (last updated 14 July 2010); Wales (last updated 16 March 2007). Now hosted at https://archives.history.ac.uk/gazetteer/ (Centre for Metropolitan History, Institute of Historical Research). The information in the Gazetteer is copyright. This repository contains only derived variables (counts, years, kinds of evidence, flags and converted coordinates), never the Gazetteer's text; please acknowledge the Gazetteer as above when using them.
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
