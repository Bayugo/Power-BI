# City Briefing: design spec (Power BI, 1280 × 720)

## Concept
A calm, editorial briefing rather than a dashboard of charts. Every page opens with a headline that states the finding. A dynamic measure drives each headline, so it updates under any filter. The visuals below it prove the headline.

Principles: one story per page; one signal colour (red = violent) against a neutral slate; one 24 px grid; no gridlines unless they help a reading; no legends when direct labels fit; the same card, title and spacing everywhere.

## Set-up (10 minutes)
1. **View > Themes > Browse for themes** and pick `CityBriefing_theme.json`.
2. **Page size**: Format page > Canvas settings > Type: Custom, 1280 × 720.
3. **Page background**: Format page > Canvas background > Image > `background_<page>.png`. Fit: *Fit*, transparency 0%. The PNG contains the cards, KPI accent bars, the rail and the canvas. So visuals just sit on top, and no shapes are needed.
4. Import `../washington_crimes_clean.csv` (re-run `solve_march.py` first if your copy lacks `report_date`/`weekday_num`), set `report_date` to Date type, then create the tables and measures from `measures.dax`.
5. Fonts: Segoe UI and Segoe UI Semibold, which are already set in the theme.

## Palette
| Role | Hex |
|---|---|
| Canvas | `#F4F1EA` |
| Card | `#FFFFFF` |
| Ink | `#14213D` |
| Muted text | `#6B7280` |
| Gridline | `#E5E1D8` |
| Property | `#5B7C99` |
| **Violent (signal)** | `#D1495B` |
| Highlight | `#EDAE49` |

Red and slate also differ in lightness, so the pair stays readable for most colour-blind viewers.

## Type scale
Headline 21 pt Semibold · KPI value 28 pt Semibold · card title 12 pt Semibold · body 10 pt · axis and caption 9 pt muted.

## Grid
Left rail 0–64. Content starts at x = 92 with a 24 px gutter and 24 px outer margin. Cards have 8 px corners, no shadow and a 1 px border (already in the background PNGs).

## Page 1: Brief
| Element | Visual | x, y, w, h | Notes |
|---|---|---|---|
| Headline | Text box, `[Headline Brief]` via fx | 92, 20, 900, 36 | Segoe UI Semibold 21 |
| Sub-line | Text box | 92, 56, 700, 20 | muted 10 |
| KPI 1–4 | Card (new) ×4 | 92 / 382 / 672 / 962, 88, 270, 92 | `[Crimes]`, `[Violent %]`, `[Gun]`, `[Top Volume Ward]`. The category label sits above the value, with a 4 px accent bar on the left. |
| Daily volume | **ZoomCharts Drill Down Combo PRO** | 92, 196, 700, 300 | Axis: Date hierarchy (Month > Week > Date). Columns = `[Crimes]` in light slate. Line = `[7D Avg]` in red 2.5 px. Drill-down on click. |
| Crime type | **ZoomCharts Drill Down Donut PRO** | 808, 196, 448, 300 | Hierarchy: offensegroup > offense_label > method. Centre text = total. Colours: property slate, violent red. |
| Insight cards ×3 | Text box (title) + text box (body) | 92 / 481 / 870, 512, 370, 180 | Body bound to `[Insight Where]` and similar measures. |

## Page 2: Where
| Element | Visual | x, y, w, h | Notes |
|---|---|---|---|
| Headline | Text box, `[Headline Where]` | 92, 20, 900, 36 | |
| Ward bars | Stacked bar: Property, Violent | 92, 88, 440, 604 | Sort by `[Crimes]` descending. Data labels outside. Add `[Violent %]` as a tooltip. |
| Incident map | **ZoomCharts Drill Down Map PRO** | 548, 88, 708, 604 | Latitude/Longitude. Size = `[Crimes]`. Colour rule from `[Violent % Colour]`. Hierarchy: ward > neighborhood_cluster > block. |

Interaction: clicking a ward bar zooms the map, and drilling the map filters the bars (edit interactions: Filter).

## Page 3: When
| Element | Visual | x, y, w, h | Notes |
|---|---|---|---|
| Headline | Text box, `[Headline When]` | 92, 20, 900, 36 | |
| Heat-map | Matrix: rows = Weekday[Num], columns = Hour[Hour], values = `[Selected Metric]` | 92, 88, 820, 604 | Cell background colour scale: min `#FBF6EC` > mid `#F3E3C3` > max `#D1495B`. Turn off totals and subtotals. Add a `Metric` slicer (tile style) in the card header. |
| Shift mix | Bar chart: shift by `[Violent %]` | 928, 88, 328, 296 | Reference band shows the city average. |
| Reporting delay | Column chart: `report_lag_days` capped at 7 | 928, 396, 328, 296 | Use a calculated bucket column. |

## Navigation
- Left rail: 3 transparent **Page navigator** buttons over the rail icons (x = 10, y = 86 / 164 / 242, 44 × 48). Set the selected-state fill to `#26365C`.
- **Reset** bookmark with a ↺ button, placed top right, with "Selected visuals" turned off.
- Page navigator and slicers sync across pages.

## ZoomCharts requirement
Pages 1 and 2 use three Drill Down PRO visuals (Combo, Donut, Map). The challenge needs at least 2. Check that the licence key is applied before exporting.

## Pre-submit checks
- Tab order and alt text on every visual.
- Click through each drill path to make sure nothing breaks.
- Test on 1366 × 768 and in dark-mode Windows (the canvas stays light on purpose).
- Export page 1 as PNG for the LinkedIn post (it must be a single image).

## Files
| File | Use |
|---|---|
| `CityBriefing_theme.json` | Import as the report theme. |
| `background_1_Brief.png` / `2_Where` / `3_When` | Page backgrounds (1920 × 1080, 16:9). |
| `mockup_*.png` | What each finished page should look like. These are matplotlib mockups, not Power BI exports. |
| `measures.dax` | All tables and measures. |
| `build_design.py` | Regenerates the theme, backgrounds and mockups. |

## Known limits
I couldn't open Power BI Desktop here, so the theme JSON and DAX are untested. If Desktop rejects a theme property, remove that property and the rest still applies. The mockups show intent, not exact Power BI rendering.
