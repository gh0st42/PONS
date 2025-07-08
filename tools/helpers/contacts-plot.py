#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import logging
import os
import argparse

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def detect_column_name(
    df: pd.DataFrame, possible_names: list, rename_to: str | None = None
) -> str | None:
    """
    Detects the first valid column name from a list of possible names.
    """
    col_name = None
    for col in possible_names:
        if col in df.columns:
            col_name = col
            break
    if col_name is not None:
        if rename_to is not None:
            logger.debug(f"Detected column '{col_name}' for renaming to '{rename_to}'")
            df.rename(columns={col_name: rename_to}, inplace=True)
        return col_name
    return None


def plot_contacts(
    filename: str,
    sep: str = ",",
    names: list[str] | None = None,
    is_core_contact_plan: bool = False,
):

    logger.info(f"Loading contact data from {filename}")
    # Load data
    df = pd.read_csv(
        filename, sep=sep, on_bad_lines="warn", skip_blank_lines=True, names=names
    )
    # drop lines which contain NaN values in the start_time or end_time columns
    if is_core_contact_plan:
        df.dropna(subset=["start_time", "end_time"], inplace=True)
        max_time = df["end_time"].max()

    print(df)
    logger.info(f"Data loaded with {len(df)} records")
    logger.info("Preprocessing data...")

    POSSIBLE_START_COLUMN_NAMES = ["start_time", "start"]
    START_COLUMN_NAME = detect_column_name(
        df, POSSIBLE_START_COLUMN_NAMES, rename_to="start_time"
    )
    if START_COLUMN_NAME is None:
        logger.error("No valid start time column found in the data.")
        return

    # Define the end time column
    POSSIBLE_END_COLUMN_NAMES = ["end_time", "end"]
    END_COLUMN_NAME = detect_column_name(
        df, POSSIBLE_END_COLUMN_NAMES, rename_to="end_time"
    )
    if END_COLUMN_NAME is None:
        logger.error("No valid end time column found in the data.")
        return

    # check if start_time and end_time are integers in seconds or strings indicating a datetime
    using_datetime = False
    if df["start_time"].dtype == "int64" and df["end_time"].dtype == "int64":
        # Convert from seconds to datetime
        pass
        # df["start_time"] = pd.to_datetime(df["start_time"], unit="s")
        # df["end_time"] = pd.to_datetime(df["end_time"], unit="s")
    elif df["start_time"].dtype == "object" and df["end_time"].dtype == "object":
        # Assume they are already in datetime format
        # pass

        df["start_time"] = pd.to_datetime(df["start_time"])
        df["end_time"] = pd.to_datetime(df["end_time"])
        using_datetime = True

    # determine source and destination nodes
    POSSIBLE_SOURCE_COLUMN_NAMES = ["groundstation", "source", "src", "node1"]
    SOURCE_COLUMN_NAME = detect_column_name(
        df, POSSIBLE_SOURCE_COLUMN_NAMES, rename_to="src"
    )
    if SOURCE_COLUMN_NAME is None:
        logger.error("No valid source column found in the data.")
        return

    POSSIBLE_DESTINATION_COLUMN_NAMES = ["satellite", "destination", "dst", "node2"]
    DESTINATION_COLUMN_NAME = detect_column_name(
        df, POSSIBLE_DESTINATION_COLUMN_NAMES, rename_to="dst"
    )
    if DESTINATION_COLUMN_NAME is None:
        logger.error("No valid destination column found in the data.")
        return
    total_time = df["end_time"].max() - df["start_time"].min()
    logger.info(f"Total time span of contacts: {total_time}")
    # replace any end times that are -1 with the total time
    df["end_time"].replace(-1, df["end_time"].max(), inplace=True)

    # Create unique combinations and assign y-positions

    combinations = df[["src", "dst"]].drop_duplicates()

    combinations["y_pos"] = range(len(combinations))
    df = df.merge(combinations, on=["src", "dst"])
    logger.info("Data preprocessing complete.")

    logger.info(f"Unique combinations found: {len(combinations)}")
    logger.debug(f"Combinations:\n{combinations}")
    logger.debug(f"DataFrame:\n{df}")

    logger.info("Plotting contact plan...")
    # Create figure
    plt.figure(figsize=(12, 6))

    colors = plt.colormaps.get_cmap("tab10")

    # Plot each contact period
    for idx, row in df.iterrows():
        row_color = colors(row["y_pos"])
        plt.barh(
            y=row["y_pos"],
            width=row["end_time"] - row["start_time"],
            left=row["start_time"],
            height=0.5,
            edgecolor="black",
            color=row_color,
        )

    # Format y-axis
    plt.yticks(
        ticks=combinations["y_pos"],
        labels=combinations["src"] + " - " + combinations["dst"],
    )

    # Format x-axis with dates
    if using_datetime:
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M:%S"))
    # plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    plt.gcf().autofmt_xdate()

    # Add labels and title
    plt.xlabel("Time")
    plt.ylabel("Contact (Node 1 - Node 2)")
    plt.title("Contact Plan")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot contact plan from CSV file.")
    parser.add_argument(
        "-s", "--sep", type=str, default=",", help="Separator used in the CSV file."
    )
    parser.add_argument(
        "-n",
        "--names",
        nargs="*",
        type=str,
        help="Optional list of column names to use in the CSV file.",
    )
    parser.add_argument(
        "-C",
        "--core-contact-plan",
        action="store_true",
        help="Parse a core contact plan file.",
    )
    parser.add_argument("filename", type=str, help="Path to the contacts CSV file.")
    args = parser.parse_args()

    if args.core_contact_plan:
        # If it's a core contact plan, we expect specific column names
        names = [
            "1",
            "2",
            "start_time",
            "end_time",
            "src",
            "dst",
            "bw",
            "loss",
            "delay",
            "jitter",
        ]
        sep = " "
        plot_contacts(args.filename, sep=sep, names=names, is_core_contact_plan=True)
    else:
        plot_contacts(args.filename)
