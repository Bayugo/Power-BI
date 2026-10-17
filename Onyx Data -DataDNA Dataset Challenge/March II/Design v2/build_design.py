"""Design v2: 'City Briefing' - theme JSON, page backgrounds and page mockups (1280x720)."""
import json, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

SRC = "../washington_crimes_clean.csv"
d = pd.read_csv(SRC, parse_dates=["report_dt"])
d["ward"] = d.ward.astype("Int64")
P = dict(canvas="#F4F1EA", card="#FFFFFF", ink="#14213D", mut="#6B7280", grid="#E5E1D8",
         prop="#5B7C99", viol="#D1495B", acc="#EDAE49", rail="#14213D")
W, H = 1280, 720

# ---------- theme ----------
theme = {
    "name": "City Briefing",
    "dataColors": [P["prop"], P["viol"], P["acc"], "#2A9D8F", "#8E7DBE", "#9AA5B1", "#264653", "#E76F51"],
    "background": P["card"], "foreground": P["ink"], "tableAccent": P["viol"],
    "good": "#2A9D8F", "neutral": P["acc"], "bad": P["viol"],
    "maximum": P["viol"], "center": "#F3E3C3", "minimum": "#FBF6EC",
    "textClasses": {
        "title": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": P["ink"]},
        "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": P["mut"]},
        "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 28, "color": P["ink"]},
        "header": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": P["ink"]},
    },
    "visualStyles": {"*": {"*": {
        "title": [{"show": True, "fontColor": {"solid": {"color": P["ink"]}}, "fontFamily": "Segoe UI Semibold", "fontSize": 12, "alignment": "left"}],
        "background": [{"show": True, "color": {"solid": {"color": P["card"]}}, "transparency": 0}],
        "border": [{"show": False}],
        "dropShadow": [{"show": False}],
        "visualHeader": [{"show": False}],
        "padding": [{"top": 12, "bottom": 12, "left": 14, "right": 14}],
        "categoryAxis": [{"gridlineShow": False, "labelColor": {"solid": {"color": P["mut"]}}, "fontSize": 10}],
        "valueAxis": [{"gridlineColor": {"solid": {"color": P["grid"]}}, "labelColor": {"solid": {"color": P["mut"]}}, "fontSize": 10}],
    }}, "page": {"*": {"background": [{"color": {"solid": {"color": P["canvas"]}}, "transparency": 0}]}}},
}
json.dump(theme, open("CityBriefing_theme.json", "w"), indent=2)

# ---------- helpers ----------
def new_fig(bg=True):
    f = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=P["canvas"])
    f.add_artist(Rectangle((0, 0), 1, 1, transform=f.transFigure, fc=P["canvas"], ec="none", zorder=-10))
    return f

def px(x, y, w, h):               # top-left pixel box -> figure fractions
    return [x / W, 1 - (y + h) / H, w / W, h / H]

def card(f, x, y, w, h):
    b = px(x, y, w, h)
    f.add_artist(FancyBboxPatch((b[0], b[1]), b[2], b[3], boxstyle="round,pad=0,rounding_size=0.008",
                 transform=f.transFigure, fc=P["card"], ec=P["grid"], lw=0.8, mutation_aspect=W / H, zorder=-5))

def txt(f, x, y, s, size=10, color=None, weight="normal", ha="left"):
    f.text(x / W, 1 - y / H, s, fontsize=size, color=color or P["ink"], fontweight=weight, ha=ha, va="top")

def rail(f, active):
    f.add_artist(Rectangle((0, 0), 64 / W, 1, transform=f.transFigure, fc=P["rail"], ec="none", zorder=-4))
    for i, (g, n) in enumerate([("B", "Brief"), ("W", "Where"), ("T", "When")]):
        cy = 110 + i * 78
        if i == active:
            f.add_artist(FancyBboxPatch((10 / W, 1 - (cy + 24) / H), 44 / W, 48 / H, boxstyle="round,pad=0,rounding_size=0.01",
                         transform=f.transFigure, fc="#26365C", ec="none", mutation_aspect=W / H, zorder=-3))
        txt(f, 32, cy - 10, g, 15, "#FFFFFF" if i == active else "#8FA0C4", "bold", "center")
        txt(f, 32, cy + 12, n, 7, "#FFFFFF" if i == active else "#8FA0C4", "normal", "center")
    f.add_artist(Rectangle((26 / W, 1 - 52 / H), 12 / W, 12 / H, transform=f.transFigure, fc=P["viol"], ec="none", zorder=-3))

def header(f, title, sub):
    txt(f, 92, 22, title, 21, weight="bold")
    txt(f, 92, 56, sub, 10, P["mut"])
    txt(f, W - 24, 58, "1 Jan – 26 Feb 2025  ·  Washington, D.C.", 9, P["mut"], ha="right")

def style(a, grid_y=True):
    a.set_facecolor(P["card"])
    for s in ("top", "right", "left"): a.spines[s].set_visible(False)
    a.spines["bottom"].set_color(P["grid"])
    a.tick_params(colors=P["mut"], labelsize=8, length=0)
    if grid_y: a.grid(axis="y", color=P["grid"], lw=.7); a.set_axisbelow(True)

def ctitle(f, x, y, s, sub=None):
    txt(f, x + 14, y + 12, s, 10.5, weight="bold")
    if sub: txt(f, x + 14, y + 29, sub, 8, P["mut"])

def kpi(f, x, y, w, label, value, note, color):
    card(f, x, y, w, 92)
    f.add_artist(Rectangle((x / W, 1 - (y + 92) / H), 4 / W, 92 / H, transform=f.transFigure, fc=color, ec="none", zorder=-4))
    txt(f, x + 18, y + 12, label.upper(), 7.5, P["mut"], "bold")
    txt(f, x + 18, y + 30, value, 24, P["ink"], "bold")
    txt(f, x + 18, y + 68, note, 8, P["mut"])

n = len(d); viol = d.is_violent.sum(); days = d.report_dt.dt.date.nunique()
off = d.offense_label.value_counts()
prop3 = off[["Theft/Other", "Theft F/Auto", "Motor Vehicle Theft"]].sum() / n
w = d.groupby("ward").agg(t=("ccn", "size"), v=("is_violent", "sum"), g=("is_gun", "sum")); w["pct"] = w.v / w.t
daily = d.groupby(d.report_dt.dt.date).size(); daily.index = pd.to_datetime(daily.index)

# ---------- PAGE 1: Brief ----------
def page1(bg_only=False):
    f = new_fig(); rail(f, 0)
    if not bg_only:
        header(f, f"{n:,} crimes in {days} days — {prop3:.0%} were theft, only {viol/n:.0%} violent",
               "The Brief  ·  what happened, how it moved, and what it was made of")
    for i, (l, v, nt, c) in enumerate([
        ("Total reported", f"{n:,}", f"{n/days:.0f} per day on average", P["ink"]),
        ("Violent share", f"{viol/n:.1%}", f"{viol:,} incidents", P["viol"]),
        ("Gun involved", f"{d.is_gun.sum()}", f"{d.is_gun.mean():.1%} of all crime", P["acc"]),
        ("Busiest ward", f"Ward {w.t.idxmax()}", f"{w.t.max()} crimes · {w.t.max()/n:.0%} of city", P["prop"])]):
        if bg_only:
            card(f, 92 + i * 290, 88, 270, 92)
            f.add_artist(Rectangle(((92 + i * 290) / W, 1 - 180 / H), 4 / W, 92 / H, transform=f.transFigure, fc=c, ec="none", zorder=-4))
        else: kpi(f, 92 + i * 290, 88, 270, l, v, nt, c)
    card(f, 92, 196, 700, 300); card(f, 808, 196, 448, 300)
    if not bg_only:
        ctitle(f, 92, 196, "Daily volume", "Drill Down Combo PRO · month › week › day, 7-day trend")
        a = f.add_axes(px(110, 244, 664, 226)); style(a)
        a.bar(daily.index, daily.values, color="#D5DEE8", width=.8)
        a.plot(daily.index, daily.rolling(7, min_periods=1).mean(), color=P["viol"], lw=2.4)
        a.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %d")); a.xaxis.set_major_locator(matplotlib.dates.WeekdayLocator(byweekday=0, interval=2))
        ctitle(f, 808, 196, "What kind of crime", "Drill Down Donut PRO · group › offense › method")
        a = f.add_axes(px(830, 240, 190, 190)); a.set_facecolor(P["card"])
        g = d.offensegroup.value_counts()
        a.pie(g.values, colors=[P["prop"], P["viol"]], startangle=90, counterclock=False, wedgeprops=dict(width=.38, edgecolor="white"))
        a.text(0, .05, f"{g.iloc[0]/n:.0%}", ha="center", fontsize=17, fontweight="bold", color=P["ink"]); a.text(0, -.25, "property", ha="center", fontsize=8, color=P["mut"])
        top = off.head(5)
        for i, (k, v) in enumerate(top.items()):
            yy = 254 + i * 38
            txt(f, 1040, yy, k, 8.5); txt(f, 1236, yy, f"{v:,}", 8.5, P["mut"], ha="right")
            f.add_artist(Rectangle((1040 / W, 1 - (yy + 26) / H), (196 * v / top.max()) / W, 5 / H, transform=f.transFigure, fc=P["viol"] if k in ("Robbery",) else P["prop"], ec="none", zorder=-2))
        txt(f, 842, 440, f"Violent: {viol:,} incidents, led by robbery ({off['Robbery']})", 8, P["mut"])
    for i in range(3): card(f, 92 + i * 389, 512, 370, 180)
    if not bg_only:
        evi = d[d["shift"] == "Midnight"].is_violent.mean(); eve = (d["shift"] == "Evening").sum()
        cards = [("WHERE", f"Ward {w.pct.idxmax()} carries the heaviest violence", f"{w.pct.max():.0%} of its crimes are violent and it logs {w.g.max()} gun incidents — vs {w.pct.min():.0%} in Ward {w.pct.idxmin()}.", P["viol"]),
                 ("WHEN", "Midnight is quieter, but far more violent", f"{evi:.0%} of midnight crime is violent vs {d[d['shift']=='Day'].is_violent.mean():.0%} by day. Evening is the busiest shift ({eve:,}).", P["acc"]),
                 ("WHAT", "Cars drive the volume", f"Theft from auto + vehicle theft = {(off['Theft F/Auto']+off['Motor Vehicle Theft'])/n:.0%} of all reports. Theft/other adds {off['Theft/Other']/n:.0%}.", P["prop"])]
        for i, (k, h, b, c) in enumerate(cards):
            x = 92 + i * 389
            txt(f, x + 18, 530, k, 8, c, "bold"); txt(f, x + 18, 552, h, 12.5, weight="bold")
            import textwrap
            txt(f, x + 18, 596, "\n".join(textwrap.wrap(b, 52)), 9, P["mut"])
    return f

# ---------- PAGE 2: Where ----------
def page2(bg_only=False):
    f = new_fig(); rail(f, 1)
    if not bg_only: header(f, f"Ward {w.t.idxmax()} has the volume. Ward {w.pct.idxmax()} has the violence.",
                           "Where  ·  volume and violent share are different stories")
    card(f, 92, 88, 440, 604); card(f, 548, 88, 708, 604)
    if not bg_only:
        ctitle(f, 92, 88, "Crimes by ward", "bar = volume · red = violent incidents")
        ws = w.sort_values("t")
        a = f.add_axes(px(150, 140, 360, 520)); style(a, False); a.grid(axis="x", color=P["grid"], lw=.7)
        a.barh([f"Ward {i}" for i in ws.index], ws.t, color=P["prop"], height=.55)
        a.barh([f"Ward {i}" for i in ws.index], ws.v, color=P["viol"], height=.55)
        for yv, (t, p) in enumerate(zip(ws.t, ws.pct)): a.text(t + 10, yv, f"{t}  ·  {p:.0%} violent", va="center", fontsize=8, color=P["mut"])
        a.set_xlim(0, ws.t.max() * 1.45)
        ctitle(f, 548, 88, "Incident map", "Drill Down Map PRO · ward › cluster › block · bubble = incidents")
        m = f.add_axes(px(566, 130, 672, 548)); m.set_facecolor("#EEF1F4")
        pr, vi = d[~d.is_violent], d[d.is_violent]
        m.hexbin(pr.longitude, pr.latitude, gridsize=38, cmap="Blues", mincnt=1, linewidths=.2, edgecolors="white", alpha=.9)
        m.scatter(vi.longitude, vi.latitude, s=9, c=P["viol"], alpha=.75, lw=0)
        m.set_xlim(-77.12, -76.91); m.set_ylim(38.80, 38.99); m.set_aspect(1.28); m.axis("off")
    return f

# ---------- PAGE 3: When ----------
def page3(bg_only=False):
    f = new_fig(); rail(f, 2)
    hr = d.groupby("hour").size()
    if not bg_only: header(f, f"Crime peaks at {hr.idxmax()-12}pm and {hr[17:].idxmax()-12}pm; violence waits for night",
                           "When  ·  weekday × hour pattern and shift mix")
    card(f, 92, 88, 820, 604); card(f, 928, 88, 328, 296); card(f, 928, 396, 328, 296)
    if not bg_only:
        ctitle(f, 92, 88, "Weekday × hour", "Matrix with colour scale · switch measure: all / violent / gun")
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        pv = d.pivot_table(index=d.report_dt.dt.day_name(), columns="hour", values="ccn", aggfunc="count", fill_value=0).reindex(order)
        a = f.add_axes(px(180, 140, 710, 500)); a.set_facecolor(P["card"])
        from matplotlib.colors import LinearSegmentedColormap
        cm = LinearSegmentedColormap.from_list("b", ["#FBF6EC", "#F3E3C3", "#E8A27C", P["viol"]])
        im = a.imshow(pv.values, cmap=cm, aspect="auto")
        a.set_yticks(range(7)); a.set_yticklabels([o[:3] for o in order]); a.set_xticks(range(0, 24, 3)); a.set_xticklabels([f"{h}:00" for h in range(0, 24, 3)])
        for s in a.spines.values(): s.set_visible(False)
        a.tick_params(colors=P["mut"], labelsize=8, length=0)
        for (r, c_), v in np.ndenumerate(pv.values):
            a.text(c_, r, v, ha="center", va="center", fontsize=6.5, color="white" if v > pv.values.max() * .7 else P["mut"])
        ctitle(f, 928, 88, "Shift mix", "share of violent crime by shift")
        sh = d.groupby("shift", observed=False).agg(t=("ccn", "size"), v=("is_violent", "mean")).reindex(["Day", "Evening", "Midnight"])
        for i, (k, r) in enumerate(sh.iterrows()):
            yy = 150 + i * 68
            txt(f, 946, yy, k, 9.5, weight="bold"); txt(f, 1238, yy, f"{int(r.t):,} crimes", 9, P["mut"], ha="right")
            f.add_artist(Rectangle((946 / W, 1 - (yy + 32) / H), 292 / W, 10 / H, transform=f.transFigure, fc=P["grid"], ec="none", zorder=-2))
            f.add_artist(Rectangle((946 / W, 1 - (yy + 32) / H), 292 * r.v / .3 / W, 10 / H, transform=f.transFigure, fc=P["viol"], ec="none", zorder=-2))
            txt(f, 946, yy + 38, f"{r.v:.0%} violent", 8, P["viol"], "bold")
        ctitle(f, 928, 396, "Reporting delay", "days between incident and report")
        lag = d.report_lag_days.clip(upper=7).value_counts(normalize=True).sort_index()
        a = f.add_axes(px(950, 450, 286, 210)); style(a)
        a.bar([("7+" if i == 7 else str(int(i))) for i in lag.index], lag.values, color=P["prop"]); a.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, 0))
    return f

for fn, name in [(page1, "1_Brief"), (page2, "2_Where"), (page3, "3_When")]:
    fn().savefig(f"mockup_{name}.png", dpi=150, facecolor=P["canvas"]); plt.close("all")
    fn(True).savefig(f"background_{name}.png", dpi=150, facecolor=P["canvas"]); plt.close("all")
print("done")
