# q2_temperatures_monthwide.py
import glob
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

# =========================
# Paths (no hardcoding)
# =========================
BASE_DIR = Path(__file__).parent.resolve()
TEMPS_DIR = BASE_DIR / "temperatures"          # folder with your CSVs
OUTPUT_DIR = TEMPS_DIR / "results"             # outputs here
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_SEASONAL_AVG = OUTPUT_DIR / "average_temp.txt"
OUTPUT_RANGE = OUTPUT_DIR / "largest_temp_range_station.txt"
OUTPUT_STABILITY = OUTPUT_DIR / "temperature_stability_stations.txt"

# =========================
# Dataset structure (months as columns)
# =========================
MONTH_COLS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
STATION_COL_CANDIDATES = ["STATION_NAME", "Station", "station", "station_name", "name"]
ID_COL_CANDIDATES = ["STN_ID", "station_id", "id"]

# Map month name to month number
MONTH_NAME_TO_NUM = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12
}

def month_to_season_au(month_num: int) -> Optional[str]:
    if month_num in (12, 1, 2):
        return "Summer"
    if month_num in (3, 4, 5):
        return "Autumn"
    if month_num in (6, 7, 8):
        return "Winter"
    if month_num in (9, 10, 11):
        return "Spring"
    return None

def c_fmt(x: float) -> str:
    return f"{x:.1f}°C"

def find_first_col(cols: List[str], candidates: List[str]) -> Optional[str]:
    lower_to_actual = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower_to_actual:
            return lower_to_actual[cand.lower()]
    return None

# =========================
# Load & reshape all CSVs
# =========================
def load_all_files_longform() -> pd.DataFrame:
    files = sorted(glob.glob(str(TEMPS_DIR / "*.csv")))
    if not files:
        raise FileNotFoundError(f"No CSV files found in '{TEMPS_DIR}'. Put your stations_group_YYYY.csv files there.")

    frames = []
    for fp in files:
        try:
            df = pd.read_csv(fp)
        except Exception as e:
            print(f"[WARN] Skipping {fp}: cannot read CSV ({e})")
            continue

        # Identify station/name columns
        station_col = find_first_col(df.columns.tolist(), STATION_COL_CANDIDATES)
        stn_id_col = find_first_col(df.columns.tolist(), ID_COL_CANDIDATES)

        # Ensure month columns exist (some files might have slightly different casing)
        present_months = [c for c in df.columns if c in MONTH_COLS]
        if not present_months:
            print(f"[WARN] Skipping {fp}: no recognizable month columns found.")
            continue

        # Melt months to rows
        long_df = df.melt(
            id_vars=[c for c in [station_col, stn_id_col, "LAT", "LON"] if c in df.columns],
            value_vars=present_months,
            var_name="month_name",
            value_name="temperature"
        )

        # Add station label fallback
        if station_col is None:
            long_df["station"] = Path(fp).stem  # fallback to filename
        else:
            long_df["station"] = long_df[station_col].astype(str)

        # Add numeric month
        long_df["month_num"] = long_df["month_name"].map(MONTH_NAME_TO_NUM).astype("Int64")

        # Coerce temperature to numeric
        long_df["temperature"] = pd.to_numeric(long_df["temperature"], errors="coerce")

        frames.append(long_df[["station", "month_num", "temperature"]])

    if not frames:
        raise RuntimeError("No usable data found across CSVs.")
    return pd.concat(frames, ignore_index=True)

# =========================
# Calculations
# =========================
def compute_seasonal_averages(all_rows: pd.DataFrame) -> pd.Series:
    ok = all_rows.dropna(subset=["temperature", "month_num"]).copy()
    ok["season"] = ok["month_num"].astype(int).map(month_to_season_au)
    ok = ok.dropna(subset=["season"])
    seasonal = ok.groupby("season")["temperature"].mean().round(1)
    return seasonal.reindex(["Summer", "Autumn", "Winter", "Spring"])

def compute_station_range(all_rows: pd.DataFrame) -> pd.DataFrame:
    ok = all_rows.dropna(subset=["temperature"]).copy()
    grouped = ok.groupby("station")["temperature"]
    stats = pd.DataFrame({"min": grouped.min(), "max": grouped.max()})
    stats["range"] = stats["max"] - stats["min"]
    max_range = stats["range"].max()
    if pd.isna(max_range):
        return pd.DataFrame(columns=["min", "max", "range"])
    winners = stats[stats["range"] == max_range].copy()
    return winners.sort_index()

def compute_station_stability(all_rows: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    ok = all_rows.dropna(subset=["temperature"]).copy()
    stds = ok.groupby("station")["temperature"].std(ddof=1).dropna()
    if stds.empty:
        return pd.DataFrame(), pd.DataFrame()
    min_std, max_std = stds.min(), stds.max()
    most_stable = stds[stds == min_std].to_frame(name="stddev").sort_index()
    most_variable = stds[stds == max_std].to_frame(name="stddev").sort_index()
    return most_stable, most_variable

# =========================
# Writers
# =========================
def write_seasonal_averages(seasonal: pd.Series, outfile: Path):
    lines = []
    for season in ["Summer", "Autumn", "Winter", "Spring"]:
        val = seasonal.get(season, np.nan)
        lines.append(f"{season}: {c_fmt(val)}" if pd.notna(val) else f"{season}: N/A")
    outfile.write_text("\n".join(lines), encoding="utf-8")

def write_range(winners: pd.DataFrame, outfile: Path):
    lines = []
    if winners.empty:
        lines.append("No data available.")
    else:
        for station, row in winners.iterrows():
            r, mn, mx = row["range"], row["min"], row["max"]
            lines.append(f"{station}: Range {c_fmt(r)} (Max: {c_fmt(mx)}, Min: {c_fmt(mn)})")
    outfile.write_text("\n".join(lines), encoding="utf-8")

def write_stability(most_stable: pd.DataFrame, most_variable: pd.DataFrame, outfile: Path):
    lines = []
    if most_stable.empty and most_variable.empty:
        lines.append("No data available.")
    else:
        if not most_stable.empty:
            s = [f"{st}: StdDev {most_stable.loc[st, 'stddev']:.1f}°C" for st in most_stable.index]
            lines.append(("Most Stable: " + s[0]) if len(s) == 1 else "Most Stable (tie): " + "; ".join(s))
        else:
            lines.append("Most Stable: N/A")
        if not most_variable.empty:
            v = [f"{st}: StdDev {most_variable.loc[st, 'stddev']:.1f}°C" for st in most_variable.index]
            lines.append(("Most Variable: " + v[0]) if len(v) == 1 else "Most Variable (tie): " + "; ".join(v))
        else:
            lines.append("Most Variable: N/A")
    outfile.write_text("\n".join(lines), encoding="utf-8")

# =========================
# Main
# =========================
def main():
    if not TEMPS_DIR.is_dir():
        raise FileNotFoundError(
            f"Folder '{TEMPS_DIR}' not found. Place all CSV files inside a folder named 'temperatures' next to this script."
        )

    all_rows = load_all_files_longform()

    # 1) Seasonal averages
    seasonal = compute_seasonal_averages(all_rows)
    write_seasonal_averages(seasonal, OUTPUT_SEASONAL_AVG)

    # 2) Largest temperature range (per station)
    winners = compute_station_range(all_rows)
    write_range(winners, OUTPUT_RANGE)

    # 3) Temperature stability
    most_stable, most_variable = compute_station_stability(all_rows)
    write_stability(most_stable, most_variable, OUTPUT_STABILITY)

    # Print absolute paths so you can find them easily
    print(f"Wrote: {OUTPUT_SEASONAL_AVG.resolve()}")
    print(f"Wrote: {OUTPUT_RANGE.resolve()}")
    print(f"Wrote: {OUTPUT_STABILITY.resolve()}")

if __name__ == "__main__":
    main()
