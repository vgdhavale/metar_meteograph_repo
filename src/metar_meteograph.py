# -*- coding: utf-8 -*-
"""
Daily METAR meteographs for selected Indian airports.

Data source: OGIMET getmetar
Output: PNG charts in output/
"""

import os
import time
import requests
import pandas as pd
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from metar import Metar
from datetime import datetime, timedelta

AIRPORTS = ["VABB", "VAAU", "VAPO", "VANP"]

BASE_URL = "https://www.ogimet.com/cgi-bin/getmetar"
OUTPUT_DIR = "output"
LOOKBACK_DAYS = 2


def fetch_metar(icao_code, start_dt, end_dt):
    params = {
        "icao": icao_code,
        "begin": start_dt.strftime("%Y%m%d%H%M"),
        "end": end_dt.strftime("%Y%m%d%H%M"),
    }

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    return response.text


def parse_metar_csv(raw_csv):
    records = []

    if not raw_csv or not raw_csv.strip():
        return pd.DataFrame()

    for line in raw_csv.strip().splitlines():
        if not line.strip():
            continue

        parts = line.split(",")

        # OGIMET CSV: ICAO,YEAR,MONTH,DAY,HOUR,MINUTE,METAR
        if len(parts) < 7:
            continue

        try:
            year, month, day, hour, minute = map(int, parts[1:6])
            timestamp = datetime(year, month, day, hour, minute)
        except ValueError:
            continue

        raw_metar = parts[6].strip()

        try:
            obs = Metar.Metar(raw_metar)
        except Exception:
            continue

        records.append({
            "Timestamp": timestamp,
            "Temperature": obs.temp.value("C") if obs.temp else None,
            "DewPoint": obs.dewpt.value("C") if obs.dewpt else None,
            "WindSpeed": obs.wind_speed.value("KT") if obs.wind_speed else None,
            "WindDir": obs.wind_dir.value() if obs.wind_dir else None,
            "Visibility": obs.vis.value("M") if obs.vis else None,
            "Pressure": obs.press.value("MB") if obs.press else None,
        })

    df = pd.DataFrame(records)

    if df.empty:
        return df

    df.set_index("Timestamp", inplace=True)
    df.sort_index(inplace=True)

    return df


def annotate_extremes(ax, series, label, unit, show_min=True):
    if series is None or series.empty:
        return

    valid = series.dropna()

    if valid.empty:
        return

    max_value = valid.max()
    max_time = valid.idxmax()

    ax.annotate(
        f"Max {label}: {max_value:.1f} {unit}\n{max_time:%d-%b %H:%M}",
        xy=(max_time, max_value),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=8,
        color="darkred",
        arrowprops={"arrowstyle": "->", "color": "darkred", "lw": 1},
    )

    if show_min:
        min_value = valid.min()
        min_time = valid.idxmin()

        ax.annotate(
            f"Min {label}: {min_value:.1f} {unit}\n{min_time:%d-%b %H:%M}",
            xy=(min_time, min_value),
            xytext=(10, -28),
            textcoords="offset points",
            fontsize=8,
            color="darkblue",
            arrowprops={"arrowstyle": "->", "color": "darkblue", "lw": 1},
        )


def plot_meteograph(df, icao_code):
    if df.empty:
        print(f"{icao_code}: No valid METAR observations found.")
        return

    fig, axes = plt.subplots(5, 1, figsize=(12, 12), sharex=True)
    ax1, ax2, ax3, ax4, ax5 = axes

    fig.suptitle(
        f"Meteograph Panel: {icao_code}",
        fontsize=14,
        fontweight="bold",
    )

    ax1.plot(
        df.index,
        df["Temperature"],
        color="red",
        marker="o",
        markersize=3,
        label="Temperature (°C)",
    )

    if "DewPoint" in df.columns:
        ax1.plot(
            df.index,
            df["DewPoint"],
            color="blue",
            linestyle="--",
            marker="o",
            markersize=3,
            label="Dew Point (°C)",
        )

    ax1.set_ylabel("Temperature (°C)")
    ax1.legend(loc="best")
    ax1.grid(True, alpha=0.3)

    annotate_extremes(
        ax1,
        df["Temperature"],
        "Temperature",
        "°C",
        show_min=True,
    )

    ax2.plot(
        df.index,
        df["WindSpeed"],
        color="purple",
        marker="x",
        markersize=4,
        label="Wind Speed (kt)",
    )

    ax2.set_ylabel("Wind Speed (kt)")
    ax2.legend(loc="best")
    ax2.grid(True, alpha=0.3)

    annotate_extremes(
        ax2,
        df["WindSpeed"],
        "Wind Speed",
        "kt",
        show_min=False,
    )

    ax3.plot(
        df.index,
        df["WindDir"],
        color="green",
        marker="x",
        markersize=4,
        label="Wind Direction (°)",
    )

    ax3.set_ylabel("Wind Direction (°)")
    ax3.set_ylim(0, 360)
    ax3.set_yticks([0, 90, 180, 270, 360])
    ax3.legend(loc="best")
    ax3.grid(True, alpha=0.3)

    ax4.plot(
        df.index,
        df["Pressure"],
        color="darkorange",
        marker="x",
        markersize=4,
        label="Pressure (hPa)",
    )

    ax4.set_ylabel("Pressure (hPa)")
    ax4.legend(loc="best")
    ax4.grid(True, alpha=0.3)

    annotate_extremes(
        ax4,
        df["Pressure"],
        "Pressure",
        "hPa",
        show_min=True,
    )

    ax5.plot(
        df.index,
        df["Visibility"],
        color="teal",
        marker="x",
        markersize=4,
        label="Visibility (m)",
    )

    ax5.set_ylabel("Visibility (m)")
    ax5.legend(loc="best")
    ax5.grid(True, alpha=0.3)

    annotate_extremes(
        ax5,
        df["Visibility"],
        "Visibility",
        "m",
        show_min=True,
    )

    fig.autofmt_xdate()
    fig.tight_layout(rect=[0, 0, 1, 0.97])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"meteograph_{icao_code}.png")

    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=LOOKBACK_DAYS)

    for icao_code in AIRPORTS:
        print("=" * 70)
        print(f"Processing {icao_code}")
        print("=" * 70)

        try:
            raw_csv = fetch_metar(icao_code, start_dt, end_dt)
            df = parse_metar_csv(raw_csv)

            if df.empty:
                print(f"{icao_code}: No data available.")
                continue

            print(df.tail())
            plot_meteograph(df, icao_code)

        except requests.RequestException as error:
            print(f"{icao_code}: Request failed: {error}")

        time.sleep(1)


if __name__ == "__main__":
    main()
