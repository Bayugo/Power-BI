"""Generate the 'City Briefing' Power BI Project (PBIR report + TMDL model) from the Design v2 assets."""
import json, os, shutil, sys, textwrap
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "CityBriefing"
DESIGN = HERE.parent / "Design v2"
FACT = "washington_crimes_clean"
BASE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"

if OUT.exists(): shutil.rmtree(OUT)
def w(path, content):
    p = OUT / path; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content if isinstance(content, str) else json.dumps(content, indent=2), encoding="utf-8")

# ============ SEMANTIC MODEL (TMDL) ============
def meas(name, expr, fmt=None, folder=None):
    q = f"'{name}'" if any(c in name for c in " %") else name
    lines = expr.strip("\n").split("\n")
    body = lines[0] if len(lines) == 1 else "\n" + "\n".join("\t\t\t" + l for l in lines)
    out = f"\tmeasure {q} = {body}\n"
    if fmt: out += f"\t\tformatString: {fmt}\n"
    if folder: out += f"\t\tdisplayFolder: {folder}\n"
    return out + "\n"

def col(name, dtype, summ="none", fmt=None, sort=None, hidden=False, extra=""):
    q = f"'{name}'" if " " in name else name
    s = f"\tcolumn {q}\n\t\tdataType: {dtype}\n"
    if fmt: s += f"\t\tformatString: {fmt}\n"
    s += f"\t\tsummarizeBy: {summ}\n\t\tsourceColumn: {name}\n"
    if sort: s += f"\t\tsortByColumn: {sort}\n"
    if hidden: s += "\t\tisHidden\n"
    return s + extra + "\n"

F = FACT
measures = "".join([
    meas("Crimes", f"COUNTROWS ( {F} )", "#,0", "1 Base"),
    meas("Violent", f"CALCULATE ( [Crimes], {F}[is_violent] = TRUE () )", "#,0", "1 Base"),
    meas("Property", "[Crimes] - [Violent]", "#,0", "1 Base"),
    meas("Gun", f"CALCULATE ( [Crimes], {F}[is_gun] = TRUE () )", "#,0", "1 Base"),
    meas("Days", f"DISTINCTCOUNT ( {F}[report_date] )", "0", "1 Base"),
    meas("Violent %", "DIVIDE ( [Violent], [Crimes] )", "0.0%", "2 Ratios"),
    meas("Gun %", "DIVIDE ( [Gun], [Crimes] )", "0.0%", "2 Ratios"),
    meas("Per Day", "DIVIDE ( [Crimes], [Days] )", "0", "2 Ratios"),
    meas("City Share", f"DIVIDE ( [Crimes], CALCULATE ( [Crimes], ALL ( {F} ) ) )", "0%", "2 Ratios"),
    meas("7D Avg", "AVERAGEX ( DATESINPERIOD ( 'Date'[Date], MAX ( 'Date'[Date] ), -7, DAY ), [Crimes] )", "0.0", "2 Ratios"),
    meas("Top Volume Ward", f"VAR t = TOPN ( 1, ALL ( {F}[ward] ), [Crimes] )\nRETURN \"Ward \" & MAXX ( t, {F}[ward] )", None, "3 Rankings"),
    meas("Top Violent Ward", f"VAR t = TOPN ( 1, ALL ( {F}[ward] ), [Violent %] )\nRETURN \"Ward \" & MAXX ( t, {F}[ward] )", None, "3 Rankings"),
    meas("Selected Metric", "SWITCH ( SELECTEDVALUE ( Metric[Metric], \"All\" ), \"Violent\", [Violent], \"Gun\", [Gun], [Crimes] )", "#,0", "4 Switcher"),
    meas("Headline Brief",
         f"VAR theft = CALCULATE ( [Crimes], {F}[offense] IN {{ \"theft/other\", \"theft f/auto\", \"motor vehicle theft\" }} )\n"
         "RETURN FORMAT ( [Crimes], \"#,0\" ) & \" crimes in \" & [Days] & \" days — \" & FORMAT ( DIVIDE ( theft, [Crimes] ), \"0%\" ) & \" were theft, only \" & FORMAT ( [Violent %], \"0%\" ) & \" violent\"", None, "5 Text"),
    meas("Headline Where", "[Top Volume Ward] & \" has the volume. \" & [Top Violent Ward] & \" has the violence.\"", None, "5 Text"),
    meas("Insight Where",
         f"VAR t = TOPN ( 1, ALL ( {F}[ward] ), [Violent %] )\n"
         "RETURN [Top Violent Ward] & \": \" & FORMAT ( MAXX ( t, [Violent %] ), \"0%\" ) & \" of crimes are violent, with \" & MAXX ( t, [Gun] ) & \" gun incidents.\"", None, "5 Text"),
    meas("Insight When",
         f"\"Midnight is \" & FORMAT ( CALCULATE ( [Violent %], ALL ( {F} ), {F}[shift] = \"Midnight\" ), \"0%\" ) & \" violent vs \" & FORMAT ( CALCULATE ( [Violent %], ALL ( {F} ), {F}[shift] = \"Day\" ), \"0%\" ) & \" by day.\"", None, "5 Text"),
    meas("Insight What",
         f"\"Theft from auto + vehicle theft = \" & FORMAT ( DIVIDE ( CALCULATE ( [Crimes], {F}[offense] IN {{ \"theft f/auto\", \"motor vehicle theft\" }} ), [Crimes] ), \"0%\" ) & \" of reports.\"", None, "5 Text"),
])

cols = "".join([
    col("ccn", "int64"), col("report_dt", "dateTime", fmt="General Date"),
    col("report_date", "dateTime", fmt="Long Date"),
    col("offense", "string"), col("offense_label", "string"), col("offensegroup", "string"),
    col("method", "string"), col("shift", "string"), col("ward", "int64"),
    col("neighborhood_cluster", "string"), col("block", "string"),
    col("latitude", "double", extra=""), col("longitude", "double"),
    col("hour", "int64"), col("weekday_num", "int64"), col("report_lag_days", "int64"), col("lag_bucket", "string"),
    col("is_violent", "boolean"), col("is_gun", "boolean"),
])
fact_m = f'''let
    Source = Csv.Document(File.Contents(DataPath), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{{{"ccn", Int64.Type}}, {{"report_dt", type datetime}}, {{"report_date", type date}}, {{"offense", type text}}, {{"offense_label", type text}}, {{"offensegroup", type text}}, {{"method", type text}}, {{"shift", type text}}, {{"ward", Int64.Type}}, {{"neighborhood_cluster", type text}}, {{"block", type text}}, {{"latitude", type number}}, {{"longitude", type number}}, {{"hour", Int64.Type}}, {{"weekday_num", Int64.Type}}, {{"report_lag_days", Int64.Type}}, {{"is_violent", type logical}}, {{"is_gun", type logical}}}}, "en-US"),
    Bucket = Table.AddColumn(Typed, "lag_bucket", each if [report_lag_days] = null then null else if [report_lag_days] >= 7 then "7+" else Text.From([report_lag_days]), type text),
    Keep = Table.SelectColumns(Bucket, {{"ccn","report_dt","report_date","offense","offense_label","offensegroup","method","shift","ward","neighborhood_cluster","block","latitude","longitude","hour","weekday_num","report_lag_days","lag_bucket","is_violent","is_gun"}})
in
    Keep'''
def partition(name, m):
    return f"\tpartition {name} = m\n\t\tmode: import\n\t\tsource =\n" + "\n".join("\t\t\t" + l for l in m.split("\n")) + "\n"

w(f"CityBriefing.SemanticModel/definition/tables/{F}.tmdl", f"table {F}\n\n{measures}{cols}{partition(F, fact_m)}")

def dim(name, m, columns, extra_table=""):
    w(f"CityBriefing.SemanticModel/definition/tables/{name}.tmdl", f"table {name}\n{extra_table}\n{columns}{partition(name, m)}")
dim("Date", '''let
    Dates = List.Dates(#date(2025, 1, 1), 59, #duration(1, 0, 0, 0)),
    T = Table.FromList(Dates, Splitter.SplitByNothing(), {"Date"}),
    Typed = Table.TransformColumnTypes(T, {{"Date", type date}}),
    Month = Table.AddColumn(Typed, "Month", each Date.ToText([Date], "MMM"), type text),
    MonthNum = Table.AddColumn(Month, "MonthNum", each Date.Month([Date]), Int64.Type)
in
    MonthNum''', col("Date", "dateTime", fmt="Long Date", extra="\t\tisKey\n") + col("Month", "string", sort="MonthNum") + col("MonthNum", "int64", hidden=True), "\tdataCategory: Time\n")
dim("Hour", '''let
    T = Table.FromList(List.Numbers(0, 24), Splitter.SplitByNothing(), {"Hour"}),
    Typed = Table.TransformColumnTypes(T, {{"Hour", Int64.Type}})
in
    Typed''', col("Hour", "int64"))
dim("Weekday", '''let
    T = #table(type table [Num = Int64.Type, Name = text], {{1, "Mon"}, {2, "Tue"}, {3, "Wed"}, {4, "Thu"}, {5, "Fri"}, {6, "Sat"}, {7, "Sun"}})
in
    T''', col("Num", "int64", hidden=True) + col("Name", "string", sort="Num"))
dim("Metric", '''let
    T = #table(type table [Metric = text, Order = Int64.Type], {{"All", 1}, {"Violent", 2}, {"Gun", 3}})
in
    T''', col("Metric", "string", sort="Order") + col("Order", "int64", hidden=True))

w("CityBriefing.SemanticModel/definition/expressions.tmdl",
  'expression DataPath = "C:\\PBI\\washington_crimes_clean.csv" meta [IsParameterQuery = true, IsParameterQueryRequired = true, Type = "Text"]\n\tlineageTag: 3f8c6c52-9d52-4d7a-8f44-0b1a5d3f6e01\n')
w("CityBriefing.SemanticModel/definition/relationships.tmdl",
  "\n".join(f"relationship {g}\n\tfromColumn: {F}.{a}\n\ttoColumn: {b}\n" for g, a, b in [
      ("a1111111-0000-4000-8000-000000000001", "report_date", "Date.Date"),
      ("a1111111-0000-4000-8000-000000000002", "hour", "Hour.Hour"),
      ("a1111111-0000-4000-8000-000000000003", "weekday_num", "Weekday.Num")]))
w("CityBriefing.SemanticModel/definition/database.tmdl", "database\n\tcompatibilityLevel: 1567\n")
w("CityBriefing.SemanticModel/definition/model.tmdl",
  "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n\n"
  + "ref expression DataPath\n" + "".join(f"ref table {t}\n" for t in (F, "Date", "Hour", "Weekday", "Metric")))
w("CityBriefing.SemanticModel/definition.pbism", {"version": "4.2", "settings": {}})
w("CityBriefing.SemanticModel/.platform", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {"type": "SemanticModel", "displayName": "CityBriefing"}, "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000001"}})

# ============ REPORT (PBIR) ============
def lit(v): return {"expr": {"Literal": {"Value": v}}}
def sol(hexc): return {"solid": {"color": lit(f"'{hexc}'")}}
def ref(table, prop, kind="Column"): return {kind: {"Expression": {"SourceRef": {"Entity": table}}, "Property": prop}}
def proj(table, prop, kind="Column", display=None):
    p = {"field": ref(table, prop, kind), "queryRef": f"{table}.{prop}", "nativeQueryRef": prop}
    if display: p["displayName"] = display
    return p
C = lambda t, p: proj(t, p, "Column"); M = lambda p, d=None: proj(F, p, "Measure", d)
INK, MUT, VIOL, PROP, ACC = "#14213D", "#6B7280", "#D1495B", "#5B7C99", "#EDAE49"

def container(title=None, sub=None, transparent=True, extra=None):
    o = {"background": [{"properties": {"show": lit("false")}}]} if transparent else {}
    o["border"] = [{"properties": {"show": lit("false")}}]
    o["dropShadow"] = [{"properties": {"show": lit("false")}}]
    o["visualHeader"] = [{"properties": {"show": lit("false")}}]
    if title:
        o["title"] = [{"properties": {"show": lit("true"), "text": lit(f"'{title}'"), "fontColor": sol(INK), "fontSize": lit("12D"), "bold": lit("true"), "alignment": lit("'left'")}}]
    if sub:
        o["subTitle"] = [{"properties": {"show": lit("true"), "text": lit(f"'{sub}'"), "fontColor": sol(MUT), "fontSize": lit("9D")}}]
    if extra: o.update(extra)
    return o

pages, z = [], [0]
def visual(page, name, vtype, x, y, wd, ht, query=None, objects=None, vco=None):
    z[0] += 1
    v = {"visualType": vtype}
    if query: v["query"] = query
    if objects: v["objects"] = objects
    v["visualContainerObjects"] = vco if vco is not None else container()
    v["drillFilterOtherVisuals"] = True
    w(f"CityBriefing.Report/definition/pages/{page}/visuals/{name}/visual.json",
      {"$schema": f"{BASE}/visualContainer/2.0.0/schema.json", "name": name,
       "position": {"x": x, "y": y, "z": z[0] * 100, "height": ht, "width": wd, "tabOrder": z[0] * 100}, "visual": v})

def q(**roles): return {"queryState": {r: {"projections": ps} for r, ps in roles.items()}}
def textbox(page, name, x, y, wd, ht, runs):
    paras = [{"textRuns": [{"value": t, "textStyle": {"fontSize": f"{s}pt", "fontWeight": "bold" if b else "normal", "color": c, "fontFamily": "Segoe UI Semibold" if b else "Segoe UI"}}]} for t, s, b, c in runs]
    visual(page, name, "textbox", x, y, wd, ht, objects={"general": [{"properties": {"paragraphs": paras}}]}, vco=container())
def card(page, name, x, y, wd, ht, measure, label, color=INK):
    visual(page, name, "card", x, y, wd, ht, q(Values=[M(measure)]),
           objects={"labels": [{"properties": {"fontSize": lit("26D"), "color": sol(color), "fontFamily": lit("'Segoe UI Semibold'")}}],
                    "categoryLabels": [{"properties": {"show": lit("false")}}]},
           vco=container(title=label))
def navbuttons(page):
    for i, tgt in enumerate(["brief", "where", "when"]):
        visual(page, f"nav_{tgt}", "actionButton", 10, 86 + i * 78, 44, 48,
               objects={"icon": [{"properties": {"shapeType": lit("'blank'")}}], "fill": [{"properties": {"show": lit("false")}}], "outline": [{"properties": {"show": lit("false")}}]},
               vco={**container(), "visualLink": [{"properties": {"show": lit("true"), "type": lit("'PageNavigation'"), "navigationSection": lit(f"'{tgt}'")}}]})
def axis_fmt(color=MUT):
    return {"categoryAxis": [{"properties": {"fontSize": lit("9D"), "labelColor": sol(color), "showAxisTitle": lit("false")}}],
            "valueAxis": [{"properties": {"fontSize": lit("9D"), "labelColor": sol(color), "gridlineColor": sol("#E5E1D8"), "showAxisTitle": lit("false")}}],
            "legend": [{"properties": {"show": lit("false")}}]}
def colors(*pairs):  # (series value, hex) point colours via dataPoint selectors
    return {"dataPoint": [{"properties": {"fill": sol(h)}, "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": None}}}]}} for _, h in pairs]} if False else {}

def add_page(name, display, actives):
    pages.append(name)
    w(f"CityBriefing.Report/definition/pages/{name}/page.json", {
        "$schema": f"{BASE}/page/2.0.0/schema.json", "name": name, "displayName": display, "displayOption": "FitToPage",
        "height": 720, "width": 1280,
        "objects": {"background": [{"properties": {
            "image": {"image": {"name": f"bg_{name}", "url": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1, "ItemName": f"bg_{name}.png"}}},
                                "scaling": lit("'Fit'")}},
            "transparency": lit("0D")}}]}})
    navbuttons(name)

H = lambda t: [(t, 21, True, INK)]
# ---- Page 1: Brief
add_page("brief", "Brief", 0)
textbox("brief", "headline", 92, 18, 1150, 40, [("3,866 crimes in 57 days — 85% were theft, only 11% violent", 21, True, INK)])
textbox("brief", "subline", 92, 56, 700, 22, [("The Brief  ·  what happened, how it moved, and what it was made of", 10, False, MUT)])
for i, (m, lbl, c) in enumerate([("Crimes", "TOTAL REPORTED", INK), ("Violent %", "VIOLENT SHARE", VIOL), ("Gun", "GUN INVOLVED", ACC), ("Top Volume Ward", "BUSIEST WARD", PROP)]):
    card("brief", f"kpi{i}", 92 + i * 290 + 8, 92, 262, 84, m, lbl, c)
visual("brief", "daily", "lineClusteredColumnComboChart", 100, 200, 684, 292,
       q(Category=[C("Date", "Date")], Y=[M("Crimes")], Y2=[M("7D Avg")]),
       objects={**axis_fmt(), "dataPoint": [{"properties": {"fill": sol("#D5DEE8")}}], "lineStyles": [{"properties": {"strokeWidth": lit("3D")}}]},
       vco=container("Daily volume", "Columns = crimes, line = 7-day average (swap for ZoomCharts Drill Down Combo PRO)"))
visual("brief", "donut", "donutChart", 816, 200, 432, 292,
       q(Category=[C(F, "offensegroup"), C(F, "offense_label")], Y=[M("Crimes")]),
       objects={"legend": [{"properties": {"show": lit("true"), "position": lit("'Right'"), "fontSize": lit("9D")}}],
                "labels": [{"properties": {"labelStyle": lit("'Percent of total'"), "fontSize": lit("9D")}}]},
       vco=container("What kind of crime", "Drill: group › offense (swap for ZoomCharts Drill Down Donut PRO)"))
for i, (k, c, m) in enumerate([("WHERE", VIOL, "Insight Where"), ("WHEN", ACC, "Insight When"), ("WHAT", PROP, "Insight What")]):
    x = 92 + i * 389
    textbox("brief", f"ins{i}_k", x + 12, 526, 340, 22, [(k, 8, True, c)])
    card("brief", f"ins{i}", x + 8, 552, 354, 130, m, "")
# ---- Page 2: Where
add_page("where", "Where", 1)
textbox("where", "headline", 92, 18, 1150, 40, [("Ward 5 has the volume. Ward 8 has the violence.", 21, True, INK)])
textbox("where", "subline", 92, 56, 700, 22, [("Where  ·  volume and violent share are different stories", 10, False, MUT)])
visual("where", "wardbars", "stackedBarChart", 100, 96, 424, 590,
       q(Category=[C(F, "ward")], Y=[M("Property"), M("Violent")]),
       objects={**axis_fmt(), "legend": [{"properties": {"show": lit("true"), "position": lit("'Bottom'")}}],
                "labels": [{"properties": {"show": lit("true"), "fontSize": lit("8D")}}]},
       vco=container("Crimes by ward", "Slate = property, red = violent"))
visual("where", "map", "map", 556, 96, 692, 590,
       q(Category=[C(F, "ccn")], Series=[C(F, "offensegroup")], X=[C(F, "longitude")], Y=[C(F, "latitude")]),
       objects={"legend": [{"properties": {"show": lit("true"), "position": lit("'Top'")}}]},
       vco=container("Incident map", "Every incident, coloured by group (swap for ZoomCharts Drill Down Map PRO)"))
# ---- Page 3: When
add_page("when", "When", 2)
textbox("when", "headline", 92, 18, 1150, 40, [("Crime peaks at 1pm and 9pm; violence waits for night", 21, True, INK)])
textbox("when", "subline", 92, 56, 700, 22, [("When  ·  weekday × hour pattern and shift mix", 10, False, MUT)])
visual("when", "metricslicer", "slicer", 640, 92, 260, 40, q(Values=[C("Metric", "Metric")]),
       objects={"data": [{"properties": {"mode": lit("'Basic'")}}], "selection": [{"properties": {"singleSelect": lit("true"), "selectAllCheckbox": lit("false")}}],
                "general": [{"properties": {"orientation": lit("1D")}}]},
       vco=container())
visual("when", "heat", "pivotTable", 100, 136, 804, 548,
       {"queryState": {"Rows": {"projections": [C("Weekday", "Name")]}, "Columns": {"projections": [C("Hour", "Hour")]}, "Values": {"projections": [M("Selected Metric")]}}},
       objects={"values": [{"properties": {"backColor": {"solid": {"color": {"expr": {"FillRule": {"Input": ref(F, "Selected Metric", "Measure"),
                   "FillRule": {"linearGradient2": {"min": {"color": lit("'#FBF6EC'")}, "max": {"color": lit("'#D1495B'")}, "nullColoringStrategy": {"strategy": lit("'asZero'")}}}}}}}}},
                   "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"{F}.Selected Metric"}}],
                "rowTotal": [{"properties": {"show": lit("false")}}], "columnTotal": [{"properties": {"show": lit("false")}}],
                "grid": [{"properties": {"gridVertical": lit("false"), "gridHorizontal": lit("false")}}]},
       vco=container("Weekday × hour", "Pick All / Violent / Gun"))
visual("when", "shift", "clusteredBarChart", 936, 96, 312, 280,
       q(Category=[C(F, "shift")], Y=[M("Violent %")]),
       objects={**axis_fmt(), "labels": [{"properties": {"show": lit("true"), "fontSize": lit("9D")}}], "dataPoint": [{"properties": {"fill": sol(VIOL)}}]},
       vco=container("Shift mix", "Share of crimes that are violent"))
visual("when", "lag", "clusteredColumnChart", 936, 408, 312, 276,
       q(Category=[C(F, "lag_bucket")], Y=[M("Crimes")]),
       objects={**axis_fmt(), "dataPoint": [{"properties": {"fill": sol(PROP)}}]},
       vco=container("Reporting delay", "Days between incident and report"))

w("CityBriefing.Report/definition/pages/pages.json", {"$schema": f"{BASE}/pagesMetadata/1.0.0/schema.json", "pageOrder": pages, "activePageName": "brief"})
w("CityBriefing.Report/definition/version.json", {"$schema": f"{BASE}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
theme = json.load(open(DESIGN / "CityBriefing_theme.json"))
w("CityBriefing.Report/StaticResources/RegisteredResources/CityBriefing_theme.json", theme)
for name in ["brief", "where", "when"]:
    src = DESIGN / f"background_{ {'brief':'1_Brief','where':'2_Where','when':'3_When'}[name] }.png"
    dst = OUT / f"CityBriefing.Report/StaticResources/RegisteredResources/bg_{name}.png"
    shutil.copy(src, dst)
w("CityBriefing.Report/definition/report.json", {
    "$schema": f"{BASE}/report/3.0.0/schema.json",
    "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": {"visual": "1.8.50", "report": "2.0.50", "page": "1.3.50"}, "type": "SharedResources"},
                        "customTheme": {"name": "CityBriefing_theme.json", "reportVersionAtImport": {"visual": "1.8.50", "report": "2.0.50", "page": "1.3.50"}, "type": "RegisteredResources"}},
    "objects": {"outspacePane": [{"properties": {"visible": lit("false")}}]},
    "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                          "items": [{"name": "CityBriefing_theme.json", "path": "CityBriefing_theme.json", "type": "CustomTheme"}] +
                                   [{"name": f"bg_{n}.png", "path": f"bg_{n}.png", "type": "Image"} for n in ["brief", "where", "when"]]}],
    "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized"}})
w("CityBriefing.Report/definition.pbir", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
                                           "version": "4.0", "datasetReference": {"byPath": {"path": "../CityBriefing.SemanticModel"}}})
w("CityBriefing.Report/.platform", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {"type": "Report", "displayName": "CityBriefing"}, "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000002"}})
w("CityBriefing.pbip", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0",
                         "artifacts": [{"report": {"path": "CityBriefing.Report"}}], "settings": {"enableAutoRecovery": True}})
w(".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
print("generated", sum(1 for _ in OUT.rglob("*") if _.is_file()), "files")
