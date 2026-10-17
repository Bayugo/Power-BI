# Washington Crimes (Jan–Feb 2025): Power BI build guide

I can't write a `.pbix` here, so this folder holds the analysis and a recipe. Power BI Desktop (Windows) is needed to build the final report.

## Files
| File | Purpose |
|---|---|
| `washington_crimes_clean.csv` | Cleaned data: deduplicated, dates parsed, ward as an integer, helper columns. Load this into Power BI. |
| `Washington_Crimes_Dashboard.png` | Single-image dashboard for the LinkedIn post. Mockup for the layout. |
| `insights.md` | Headline findings to paste into the post and the report. |
| `solve_march.py` | Reproduces everything (`python3 -I solve_march.py`). |

## Cleaning applied
- Removed 1 duplicate `CCN` (3,867 to 3,866 rows).
- Parsed `REPORT_DAT`, `START_DATE` and `END_DATE` (format `M/D/YYYY, h:mm:ss AM/PM`).
- Dropped `OCTO_RECORD_ID`, which is empty.
- `START_DATE` has 172 values before 2025, some as early as 1989. Use `REPORT_DAT` for time analysis. `report_lag_days` captures the delay.
- Added `is_violent`, `is_gun`, `hour`, `weekday` and `offense_label`.

## Report plan (3 pages, at least 2 ZoomCharts Drill Down visuals)
1. **Overview**: KPI cards, a Drill Down Combo PRO (month > week > day, with offense group as series), and a Drill Down Donut PRO (offense group > offense > method).
2. **Where**: a Drill Down Map PRO (ward > neighborhood cluster > district, using latitude and longitude) and a Drill Down Combo Bar PRO (crimes by ward). Cross-filters everything.
3. **When**: shift x hour x weekday heatmap, plus a Drill Down Timeline PRO.

Add a page-navigation bar, a reset-filters bookmark and a short tooltip on each visual.

## DAX measures
```DAX
Total Crimes = COUNTROWS ( washington_crimes_clean )
Violent Crimes = CALCULATE ( [Total Crimes], washington_crimes_clean[is_violent] = TRUE () )
Violent % = DIVIDE ( [Violent Crimes], [Total Crimes] )
Gun Incidents = CALCULATE ( [Total Crimes], washington_crimes_clean[method] = "gun" )
Gun % = DIVIDE ( [Gun Incidents], [Total Crimes] )
Active Days = DISTINCTCOUNT ( washington_crimes_clean[report_date] )
Avg Per Day = DIVIDE ( [Total Crimes], [Active Days] )
7D Avg =
AVERAGEX (
    DATESINPERIOD ( 'Date'[Date], MAX ( 'Date'[Date] ), -7, DAY ),
    [Total Crimes]
)
Share of Total = DIVIDE ( [Total Crimes], CALCULATE ( [Total Crimes], ALL ( washington_crimes_clean ) ) )
Hotspot Ward =
VAR t = TOPN ( 1, VALUES ( washington_crimes_clean[ward] ), [Total Crimes] )
RETURN "Ward " & MAXX ( t, washington_crimes_clean[ward] )
```
Create a `Date` table with `Date = CALENDAR ( DATE(2025,1,1), DATE(2025,2,28) )` and relate it to `report_dt` (date part). Add a `report_date` column in Power Query (`Date.From([report_dt])`).

## Key findings
See `insights.md`. In short: 85% of crime is theft or auto crime. Ward 5 has the most volume. Ward 8 has the highest violent share and the most gun incidents. Midnight is the most violent shift, while evening is the busiest.

## Submission checklist (from the README)
1. Register for the ZoomCharts Mini Challenge to get the free Drill Down Visuals license.
2. Build the report and use at least 2 ZoomCharts visuals.
3. Submit the `.pbix` on the ZoomCharts submit page.
4. Post one image on LinkedIn, tagging @OnyxData, @ZoomCharts, @Enterprise DNA, @BCS, @Smart Frames UI and @Data Career Jumpstart, with #dataDNA and #builtwithzoomcharts.
5. Complete the DataDNA form: https://forms.office.com/r/S1ES7vxDUF
