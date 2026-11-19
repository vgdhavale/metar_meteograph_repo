# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 10:01:48 2026

@author: Radio
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Nov 18 15:27:22 2026

@author: Radio
"""

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
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

AIRPORTS = ["VABB", "VAAU", "VAPO", "VANP"]

BASE_URL = "https://www.ogimet.com/cgi-bin/getmetar"
OUTPUT_DIR = "output"
LOOKBACK_DAYS = 2

UTC = timezone.utc
IST = ZoneInfo("Asia/Kolkata")


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

            # OGIMET timestamps are in UTC.
            timestamp = datetime(year, month, day, hour, minute, tzinfo=UTC)

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


def format_extreme_time(timestamp):
    """
    Returns both UTC and IST time for an extreme-value timestamp.
    """
    utc_time = timestamp.astimezone(UTC)
    ist_time = timestamp.astimezone(IST)

    return (
        f"UTC: {utc_time:%d-%b-%Y %H:%M}\n"
        f"IST: {ist_time:%d-%b-%Y %H:%M}"
    )


def annotate_extremes(ax, series, label, unit, show_min=True):
    """
    Adds bold, enlarged maximum and minimum annotations to a plot.
    """
    if series is None or series.empty:
        return

    valid = series.dropna()

    if valid.empty:
        return

    max_value = valid.max()
    max_time = valid.idxmax()

    max_text = (
        f"MAX {label.upper()}: {max_value:.1f} {unit}\n"
        f"{format_extreme_time(max_time)}"
    )

    ax.annotate(
        max_text,
        xy=(max_time, max_value),
        xytext=(12, 15),
        textcoords="offset points",
        fontsize=11,
        fontweight="bold",
        color="darkred",
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": "darkred",
            "alpha": 0.85,
        },
        arrowprops={
            "arrowstyle": "->",
            "color": "darkred",
            "lw": 1.5,
        },
    )

    if show_min:
        min_value = valid.min()
        min_time = valid.idxmin()

        min_text = (
            f"MIN {label.upper()}: {min_value:.1f} {unit}\n"
            f"{format_extreme_time(min_time)}"
        )

        ax.annotate(
            min_text,
            xy=(min_time, min_value),
            xytext=(12, -45),
            textcoords="offset points",
            fontsize=11,
            fontweight="bold",
            color="darkblue",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "white",
                "edgecolor": "darkblue",
                "alpha": 0.85,
            },
            arrowprops={
                "arrowstyle": "->",
                "color": "darkblue",
                "lw": 1.5,
            },
        )


def style_axis(ax, ylabel):
    """
    Makes axis labels, tick labels, and legend text bold.
    """
    ax.set_ylabel(
        ylabel,
        fontsize=13,
        fontweight="bold",
    )

    ax.set_xlabel(
        "Time (UTC)",
        fontsize=12,
        fontweight="bold",
    )

    ax.tick_params(axis="both", labelsize=11)

    for tick_label in ax.get_xticklabels() + ax.get_yticklabels():
        tick_label.set_fontweight("bold")

    legend = ax.legend(loc="best", fontsize=11)
    legend.set_title(None)

    for text in legend.get_texts():
        text.set_fontweight("bold")

    ax.grid(True, alpha=0.3)


def plot_meteograph(df, icao_code):
    if df.empty:
        print(f"{icao_code}: No valid METAR observations found.")
        return

    fig, axes = plt.subplots(5, 1, figsize=(14, 14), sharex=True)
    ax1, ax2, ax3, ax4, ax5 = axes

    fig.suptitle(
        f"Meteograph Panel: {icao_code}",
        fontsize=18,
        fontweight="bold",
    )

    # Temperature and dew point
    ax1.plot(
        df.index,
        df["Temperature"],
        color="red",
        marker="o",
        markersize=4,
        linewidth=2,
        label="Temperature (°C)",
    )

    if "DewPoint" in df.columns:
        ax1.plot(
            df.index,
            df["DewPoint"],
            color="blue",
            linestyle="--",
            marker="o",
            markersize=4,
            linewidth=2,
            label="Dew Point (°C)",
        )

    annotate_extremes(
        ax1,
        df["Temperature"],
        "Temperature",
        "°C",
        show_min=True,
    )

    style_axis(ax1, "Temperature (°C)")

    # Wind speed
    ax2.plot(
        df.index,
        df["WindSpeed"],
        color="purple",
        marker="x",
        markersize=5,
        linewidth=2,
        label="Wind Speed (kt)",
    )

    annotate_extremes(
        ax2,
        df["WindSpeed"],
        "Wind Speed",
        "kt",
        show_min=False,
    )

    style_axis(ax2, "Wind Speed (kt)")

    # Wind direction
    ax3.plot(
        df.index,
        df["WindDir"],
        color="green",
        marker="x",
        markersize=5,
        linewidth=2,
        label="Wind Direction (°)",
    )

    ax3.set_ylim(0, 360)
    ax3.set_yticks([0, 90, 180, 270, 360])

    style_axis(ax3, "Wind Direction (°)")

    # Pressure
    ax4.plot(
        df.index,
        df["Pressure"],
        color="darkorange",
        marker="x",
        markersize=5,
        linewidth=2,
        label="Pressure (hPa)",
    )

    annotate_extremes(
        ax4,
        df["Pressure"],
        "Pressure",
        "hPa",
        show_min=True,
    )

    style_axis(ax4, "Pressure (hPa)")

    # Visibility
    ax5.plot(
        df.index,
        df["Visibility"],
        color="teal",
        marker="x",
        markersize=5,
        linewidth=2,
        label="Visibility (m)",
    )

    annotate_extremes(
        ax5,
        df["Visibility"],
        "Visibility",
        "m",
        show_min=True,
    )

    style_axis(ax5, "Visibility (m)")

    fig.autofmt_xdate()
    fig.tight_layout(rect=[0, 0, 1, 0.97])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"meteograph_{icao_code}.png")

    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {output_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    end_dt = datetime.now(UTC)
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
