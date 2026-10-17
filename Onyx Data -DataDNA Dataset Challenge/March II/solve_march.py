"""Washington Crimes (Jan-Feb 2025): clean data, compute insights, render a single-image dashboard."""
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = "Onyx Data -DataDNA Dataset Challenge - Washington Crimes Dataset - March 2025.xlsx"
FMT = "%m/%d/%Y, %I:%M:%S %p"

d = pd.read_excel(SRC)
d.columns = [c.lower().replace("-", "_") for c in d.columns]
d = d.drop_duplicates("ccn").drop(columns=["octo_record_id"])
d["report_dt"] = pd.to_datetime(d.report_dat, format=FMT)
d["start_dt"] = pd.to_datetime(d.start_date, format=FMT, errors="coerce")
d["end_dt"] = pd.to_datetime(d.end_date, format=FMT, errors="coerce")
d["ward"] = d.ward.astype("Int64")
d["offense_label"] = d.offense.str.title()
d["month"] = d.report_dt.dt.strftime("%b")
d["weekday"] = d.report_dt.dt.day_name()
d["hour"] = d.report_dt.dt.hour
d["report_date"] = d.report_dt.dt.date
d["weekday_num"] = d.report_dt.dt.dayofweek + 1
d["report_lag_days"] = (d.report_dt.dt.normalize() - d.start_dt.dt.normalize()).dt.days.clip(lower=0).astype("Int64")
d["is_violent"] = d.offensegroup.eq("violent")
d["is_gun"] = d.method.eq("gun")
d["shift"] = pd.Categorical(d["shift"].str.title(), ["Day", "Evening", "Midnight"], ordered=True)
d.to_csv("washington_crimes_clean.csv", index=False)

n = len(d)
viol = d.is_violent.sum()
wards = d.groupby("ward").agg(total=("ccn", "size"), violent=("is_violent", "sum"), gun=("is_gun", "sum"))
wards["violent_pct"] = wards.violent / wards.total * 100
daily = d.groupby(d.report_dt.dt.date).size()
mon = d.groupby("month").size().reindex(["Jan", "Feb"])
off = d.offense_label.value_counts()
shift = d.groupby(["shift", "offensegroup"], observed=True).size().unstack(fill_value=0)
hours = d.groupby("hour").size().reindex(range(24), fill_value=0)

insights = [
    f"{n:,} crimes reported 1 Jan - 26 Feb 2025 (~{daily.mean():.0f}/day); {viol/n:.1%} violent, {1-viol/n:.1%} property.",
    f"Theft/other + theft from auto + motor vehicle theft = {off[['Theft/Other','Theft F/Auto','Motor Vehicle Theft']].sum()/n:.0%} of all crimes.",
    f"Ward {wards.total.idxmax()} has the most crimes ({wards.total.max()}); Ward {wards.violent_pct.idxmax()} has the highest violent share ({wards.violent_pct.max():.0f}%) and the most gun incidents ({wards.gun.max()}).",
    f"Ward 3 is safest: {wards.total.min()} crimes, {wards.violent_pct.min():.0f}% violent.",
    f"Evening is the busiest shift ({shift.sum(axis=1).loc['Evening']:,}); midnight has the highest violent share ({shift.loc['Midnight','violent']/shift.loc['Midnight'].sum():.0%}).",
    f"Guns were used in {d.is_gun.sum()} incidents ({d.is_gun.mean():.1%}); knives in {(d.method=='knife').sum()}.",
    f"Feb daily rate is {daily[daily.index>=pd.Timestamp('2025-02-01').date()].mean():.0f} vs Jan {daily[daily.index<pd.Timestamp('2025-02-01').date()].mean():.0f}.",
]
open("insights.md", "w").write("# Key insights\n\n" + "\n".join(f"- {i}" for i in insights) + "\n")

BG, FG, MUT = "#0f172a", "#e2e8f0", "#94a3b8"
C = {"prop": "#38bdf8", "viol": "#f43f5e", "acc": "#fbbf24"}
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "text.color": FG, "axes.labelcolor": MUT,
                     "xtick.color": MUT, "ytick.color": MUT, "axes.edgecolor": "#334155", "font.size": 11})
fig = plt.figure(figsize=(16, 10))
fig.text(.03, .955, "Washington, D.C. Crime Report", fontsize=26, fontweight="bold")
fig.text(.03, .925, "Jan - Feb 2025  |  #dataDNA  |  Onyx Data DataDNA Dataset Challenge - March 2025", color=MUT)
kpis = [("Total crimes", f"{n:,}", FG), ("Violent", f"{viol:,} ({viol/n:.0%})", C["viol"]),
        ("Gun incidents", f"{d.is_gun.sum()}", C["acc"]), ("Avg / day", f"{daily.mean():.0f}", C["prop"]),
        ("Hotspot ward", f"Ward {wards.total.idxmax()}", FG)]
for i, (k, v, c) in enumerate(kpis):
    x = .03 + i * .195
    fig.patches.append(plt.Rectangle((x, .80), .18, .095, transform=fig.transFigure, fc="#1e293b", ec="none"))
    fig.text(x + .01, .865, k, color=MUT, fontsize=10)
    fig.text(x + .01, .815, v, color=c, fontsize=20, fontweight="bold")

def ax_at(l, b, w, h, t):
    a = fig.add_axes([l, b, w, h]); a.set_title(t, loc="left", color=FG, fontsize=12, fontweight="bold", pad=8)
    for s in ("top", "right"): a.spines[s].set_visible(False)
    return a

a = ax_at(.17, .43, .17, .30, "Offense type (violent in red)")
o = off.sort_values()
a.barh(o.index, o.values, color=[C["viol"] if x in {"Robbery","Homicide","Sex Abuse","Assault W/Dangerous Weapon"} else C["prop"] for x in o.index])
for y, v in enumerate(o.values): a.text(v + 15, y, f"{v:,}", va="center", color=MUT, fontsize=9)
a.set_xlim(0, o.max() * 1.15)

a = ax_at(.42, .43, .25, .30, "Crimes by ward")
w = wards.sort_index()
a.bar(w.index.astype(str), w.total - w.violent, color=C["prop"], label="Property")
a.bar(w.index.astype(str), w.violent, bottom=w.total - w.violent, color=C["viol"], label="Violent")
a.set_xlabel("Ward"); a.legend(frameon=False, labelcolor=FG, fontsize=9)

a = ax_at(.73, .43, .24, .30, "Shift x offense group")
shift.plot.bar(stacked=True, ax=a, color=[C["prop"], C["viol"]], legend=False, rot=0); a.set_xlabel("")

a = ax_at(.06, .06, .42, .28, "Daily crimes (7-day average)")
a.plot(daily.index, daily.values, color="#334155", lw=1)
a.plot(daily.index, daily.rolling(7, min_periods=1).mean().values, color=C["acc"], lw=2.5)
import matplotlib.dates as mdates
a.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2)); a.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

a = ax_at(.55, .06, .42, .28, "Crimes by hour reported")
a.bar(hours.index, hours.values, color=[C["acc"] if h == hours.idxmax() else C["prop"] for h in hours.index])
a.set_xticks(range(0, 24, 3))

fig.text(.03, .015, "Source: DC Crime Cards (crimecards.dc.gov)", color=MUT, fontsize=9)
fig.savefig("Washington_Crimes_Dashboard.png", dpi=130)
print("\n".join(insights))
