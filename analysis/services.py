import io
import json
import numpy as np
import pandas as pd
import matplotlib
# "Agg" is a non-interactive Matplotlib backend that renders to memory buffers.
# It must be set BEFORE importing pyplot, otherwise Matplotlib tries to open a
# display which fails on a headless server.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import date
from scipy import stats

from .models import YearlyRecord, MonthlyRecord

# Module-level constant: the handwashing pivot date as a pandas Timestamp.
# Using pd.Timestamp allows direct comparison with DataFrame date columns.
PIVOT = pd.Timestamp("1847-06-01")


# ─────────────────────────────────────────────────────────────────────────────
# CSV IMPORT
# Each importer: reads the uploaded file with pandas, wipes the existing table,
# then uses bulk_create for a single efficient INSERT rather than one per row.
# ─────────────────────────────────────────────────────────────────────────────

def import_yearly_csv(file_obj):
    """
    Parses an uploaded yearly_deaths_by_clinic.csv file and populates the
    YearlyRecord table from scratch.
    file_obj is a Django InMemoryUploadedFile (behaves like a file handle).
    """
    df = pd.read_csv(file_obj)
    YearlyRecord.objects.all().delete()   # wipe first to avoid duplicates
    YearlyRecord.objects.bulk_create([
        YearlyRecord(
            year=int(row["year"]),
            births=int(row["births"]),
            deaths=int(row["deaths"]),
            clinic=str(row["clinic"]).strip(),  # .strip() removes accidental spaces
        )
        for _, row in df.iterrows()
    ])


def import_monthly_csv(file_obj):
    """
    Parses an uploaded monthly_deaths.csv file and populates the
    MonthlyRecord table from scratch.
    parse_dates=["date"] tells pandas to convert that column to Timestamps
    so .date() can be called to get a Python date object for the model field.
    """
    df = pd.read_csv(file_obj, parse_dates=["date"])
    MonthlyRecord.objects.all().delete()
    MonthlyRecord.objects.bulk_create([
        MonthlyRecord(
            date=row["date"].date(),   # pandas Timestamp → Python date
            births=int(row["births"]),
            deaths=int(row["deaths"]),
        )
        for _, row in df.iterrows()
    ])


# ─────────────────────────────────────────────────────────────────────────────
# DATAFRAMES
# Convert the Django ORM queryset into a pandas DataFrame.
# .values() returns a ValuesQuerySet (list of dicts) which pandas can read
# directly. This avoids instantiating full model objects for every row.
# ─────────────────────────────────────────────────────────────────────────────

def yearly_to_dataframe():
    """Returns all YearlyRecord rows as a DataFrame with a proportion_deaths column."""
    qs = YearlyRecord.objects.values("year", "births", "deaths", "clinic")
    df = pd.DataFrame(list(qs))
    if not df.empty:
        df["proportion_deaths"] = (df["deaths"] / df["births"]).round(6)
    return df


def monthly_to_dataframe():
    """
    Returns all MonthlyRecord rows as a DataFrame sorted by date,
    with a proportion_deaths column and dates converted to Timestamps.
    """
    qs = MonthlyRecord.objects.values("date", "births", "deaths")
    df = pd.DataFrame(list(qs))
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])   # Python date → Timestamp for comparisons
        df["proportion_deaths"] = (df["deaths"] / df["births"]).round(6)
        df = df.sort_values("date").reset_index(drop=True)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# CHART.JS JSON DATA
# These functions return JSON strings that are injected directly into <script>
# blocks in templates as JavaScript objects.
# {"empty": True} is a sentinel value: the JS checks `if (cd && !cd.empty)`
# before calling the render functions so no error is thrown on an empty DB.
# ─────────────────────────────────────────────────────────────────────────────

def yearly_chart_data():
    """
    Builds the data object for renderClinicChart() in charts.js.
    Returns: { labels: [year,...], clinic1: [proportion,...], clinic2: [...] }
    """
    df = yearly_to_dataframe()
    if df.empty:
        return json.dumps({"empty": True})
    c1 = df[df["clinic"] == "clinic 1"].sort_values("year")
    c2 = df[df["clinic"] == "clinic 2"].sort_values("year")
    return json.dumps({
        "labels":  c1["year"].tolist(),
        "clinic1": c1["proportion_deaths"].tolist(),
        "clinic2": c2["proportion_deaths"].tolist(),
    })


def monthly_chart_data():
    """
    Builds the data object for renderMonthlyChart() in charts.js.
    Splits the records into two separate datasets at PIVOT (June 1847) so the
    JS can render them as two colour-coded line segments on the same chart.
    Returns: { labelsBefore, before, labelsAfter, after }
    """
    df = monthly_to_dataframe()
    if df.empty:
        return json.dumps({"empty": True})
    before = df[df["date"] < PIVOT]
    after  = df[df["date"] >= PIVOT]
    return json.dumps({
        "labelsBefore": [str(d.date()) for d in before["date"]],
        "before":       before["proportion_deaths"].tolist(),
        "labelsAfter":  [str(d.date()) for d in after["date"]],
        "after":        after["proportion_deaths"].tolist(),
    })


def bootstrap_chart_data_json(boot_diffs, ci_lower, ci_upper):
    """
    Converts the bootstrap difference list into a histogram-friendly JSON blob
    for renderBootstrapHistogram() in charts.js.
    np.histogram returns (counts, bin_edges); we take the bin midpoints as labels.
    """
    counts, edges = np.histogram(boot_diffs, bins=40)
    return json.dumps({
        "labels":   [round((edges[i] + edges[i + 1]) / 2, 5) for i in range(len(counts))],
        "counts":   counts.tolist(),
        "ci_lower": round(ci_lower, 5),   # used by charts.js to colour bars outside the CI
        "ci_upper": round(ci_upper, 5),
    })


# ─────────────────────────────────────────────────────────────────────────────
# FULL ANALYSIS
# Called once by AnalysisView.get_context_data(). Returns a single dict that
# is merged into the template context with ctx.update(services.run_full_analysis()).
# ─────────────────────────────────────────────────────────────────────────────

def run_full_analysis():
    """
    Runs the complete Semmelweis analysis and returns a context dict with:
      clinic_comparison   – list of {year, clinic1, clinic2} dicts for the table
      yearly_chart_data   – JSON string for Chart.js
      monthly_chart_data  – JSON string for Chart.js
      mean_before         – mean proportion deaths before June 1847
      mean_after          – mean proportion deaths after June 1847
      mean_diff           – difference (after - before)
      bootstrap_chart_data– JSON string for Chart.js histogram
      ci_lower / ci_upper – 2.5th and 97.5th percentiles of bootstrap distribution
      ci_lower_pct / ci_upper_pct – same values as percentages for display
      t_stat / p_value    – Welch's t-test results
      p_value_fmt         – formatted p-value string (scientific notation)
      significant         – bool: True if p < 0.05
    """
    ctx = {}

    # ── Clinic comparison table (yearly) ──────────────────────────────────────
    ydf = yearly_to_dataframe()
    if not ydf.empty:
        # set_index makes year-based lookup via c1[year] possible.
        c1 = ydf[ydf["clinic"] == "clinic 1"].set_index("year")["proportion_deaths"]
        c2 = ydf[ydf["clinic"] == "clinic 2"].set_index("year")["proportion_deaths"]
        years = sorted(set(c1.index) | set(c2.index))
        ctx["clinic_comparison"] = [
            {
                "year":    y,
                "clinic1": round(c1[y], 4) if y in c1.index else "—",
                "clinic2": round(c2[y], 4) if y in c2.index else "—",
            }
            for y in years
        ]
    else:
        ctx["clinic_comparison"] = []

    ctx["yearly_chart_data"] = yearly_chart_data()

    # ── Monthly handwashing effect ─────────────────────────────────────────────
    mdf = monthly_to_dataframe()
    ctx["monthly_chart_data"] = monthly_chart_data()

    if not mdf.empty:
        before_s = mdf[mdf["date"] < PIVOT]["proportion_deaths"]
        after_s  = mdf[mdf["date"] >= PIVOT]["proportion_deaths"]
        ctx["mean_before"] = round(float(before_s.mean()), 4)
        ctx["mean_after"]  = round(float(after_s.mean()),  4)
        # mean_diff is negative: after < before, confirming deaths fell.
        ctx["mean_diff"]   = round(float(after_s.mean() - before_s.mean()), 4)
    else:
        ctx.update(mean_before=0, mean_after=0, mean_diff=0)
        before_s = after_s = pd.Series(dtype=float)

    # ── Bootstrap 95 % Confidence Interval ────────────────────────────────────
    # We resample the before and after groups 3 000 times with replacement and
    # compute the mean difference each time. The 2.5th and 97.5th percentiles
    # of the resulting distribution are the 95 % CI bounds.
    # np.random.default_rng(42): seed=42 makes results reproducible.
    if len(before_s) > 1 and len(after_s) > 1:
        rng = np.random.default_rng(42)
        boot_diffs = [
            rng.choice(after_s.values,  size=len(after_s),  replace=True).mean() -
            rng.choice(before_s.values, size=len(before_s), replace=True).mean()
            for _ in range(3000)
        ]
        ci_lower = float(np.quantile(boot_diffs, 0.025))
        ci_upper = float(np.quantile(boot_diffs, 0.975))
        ctx["bootstrap_chart_data"] = bootstrap_chart_data_json(boot_diffs, ci_lower, ci_upper)
    else:
        ci_lower = ci_upper = 0.0
        ctx["bootstrap_chart_data"] = json.dumps({"empty": True})

    ctx["ci_lower"]     = round(ci_lower, 4)
    ctx["ci_upper"]     = round(ci_upper, 4)
    # abs() because ci_lower is negative (deaths went down); *100 for display as %
    ctx["ci_lower_pct"] = round(abs(ci_lower) * 100, 2)
    ctx["ci_upper_pct"] = round(abs(ci_upper) * 100, 2)

    # ── Welch's t-test ─────────────────────────────────────────────────────────
    # equal_var=False → Welch's variant, which does NOT assume equal variances.
    # This is the safer default when comparing two independent groups.
    if len(before_s) > 1 and len(after_s) > 1:
        t_stat, p_value = stats.ttest_ind(before_s, after_s, equal_var=False)
    else:
        t_stat = p_value = float("nan")

    ctx["t_stat"]      = round(float(t_stat), 4)
    ctx["p_value"]     = float(p_value)
    # f"{p_value:.2e}" formats as scientific notation, e.g. "1.23e-10".
    # The `p_value != p_value` check is a NaN test (NaN is the only float not equal to itself).
    ctx["p_value_fmt"] = f"{p_value:.2e}" if not (p_value != p_value) else "N/A"
    ctx["significant"] = (p_value < 0.05) if not (p_value != p_value) else False

    return ctx


# ─────────────────────────────────────────────────────────────────────────────
# PNG EXPORTS
# Each function builds a Matplotlib figure, converts it to PNG bytes via a
# BytesIO buffer, and closes the figure to free memory.
# ─────────────────────────────────────────────────────────────────────────────

def _fig_to_png(fig):
    """
    Shared helper: saves a Matplotlib figure to an in-memory PNG byte string.
    bbox_inches="tight" crops whitespace around the chart.
    dpi=150 gives a good balance of resolution and file size.
    plt.close(fig) is essential — without it each download call leaks a figure
    object and Matplotlib eventually logs a warning about too many open figures.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)       # rewind to the start so .read() returns the full content
    return buf.read()


def clinic_comparison_chart_png():
    """
    Generates a line chart comparing death proportions for Clinic 1 vs Clinic 2
    across years 1841–1846.
    """
    df = yearly_to_dataframe()
    fig, ax = plt.subplots(figsize=(8, 4))
    if not df.empty:
        for label, grp in df.groupby("clinic"):
            grp = grp.sort_values("year")
            ax.plot(grp["year"], grp["proportion_deaths"], marker="o", label=label)
        ax.legend()
    ax.set_xlabel("Year")
    ax.set_ylabel("Proportion of deaths")
    ax.set_title("Death Proportion by Clinic (1841–1846)")
    return _fig_to_png(fig)


def monthly_proportion_chart_png():
    """
    Generates a line chart of monthly death proportions, with the before and
    after handwashing periods drawn in separate colours and a vertical dashed
    line at the pivot date.
    """
    df = monthly_to_dataframe()
    fig, ax = plt.subplots(figsize=(10, 4))
    if not df.empty:
        before = df[df["date"] < PIVOT].sort_values("date")
        after  = df[df["date"] >= PIVOT].sort_values("date")
        ax.plot(before["date"], before["proportion_deaths"],
                color="tab:red",   label="Before handwashing")
        ax.plot(after["date"],  after["proportion_deaths"],
                color="tab:green", label="After handwashing")
        ax.axvline(PIVOT, color="gray", linestyle="--", linewidth=1)
        ax.legend()
    ax.set_ylabel("Proportion of deaths")
    ax.set_title("Monthly Proportion of Deaths — Clinic 1")
    return _fig_to_png(fig)


def bootstrap_histogram_png():
    """
    Generates a histogram of the bootstrap distribution (3 000 resamples)
    with vertical dashed lines at the 2.5th and 97.5th percentile (the CI bounds).
    """
    mdf = monthly_to_dataframe()
    fig, ax = plt.subplots(figsize=(8, 4))
    if not mdf.empty:
        before_s = mdf[mdf["date"] < PIVOT]["proportion_deaths"]
        after_s  = mdf[mdf["date"] >= PIVOT]["proportion_deaths"]
        rng = np.random.default_rng(42)
        boot_diffs = [
            rng.choice(after_s.values,  size=len(after_s),  replace=True).mean() -
            rng.choice(before_s.values, size=len(before_s), replace=True).mean()
            for _ in range(3000)
        ]
        ci = np.quantile(boot_diffs, [0.025, 0.975])
        ax.hist(boot_diffs, bins=40, color="steelblue", alpha=0.7)
        ax.axvline(ci[0], color="red",   linestyle="--", label=f"2.5%  = {ci[0]:.4f}")
        ax.axvline(ci[1], color="green", linestyle="--", label=f"97.5% = {ci[1]:.4f}")
        ax.legend()
    ax.set_xlabel("Mean difference in proportion deaths")
    ax.set_ylabel("Frequency")
    ax.set_title("Bootstrap Distribution (3 000 resamples)")
    return _fig_to_png(fig)