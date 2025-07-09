#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import logging
import os
import re
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
    output: str | None = None,
    plot_fixed_links: bool = False,
    human_readable_timestamp: bool = False,
):
    """
    Plots contact periods from a CSV file.

    Args:
        filename (str): Path to the CSV file containing contact data.
        sep (str): Separator used in the CSV file. Defaults to ",".
        names (list[str] | None): List of column names if the CSV doesn't have a header.
                                   Defaults to None.
        is_core_contact_plan (bool): If True, drops rows with NaN in start_time/end_time.
                                     Defaults to False.
        output (str | None): Path to save the plot. If None, displays the plot.
                             Defaults to None.
        plot_fixed_links (bool): If False, removes fixed links (start_time=0, end_time=max_time).
                                 Defaults to False.
    """

    logger.info(f"Loading contact data from {filename}")
    # Load data
    df = pd.read_csv(
        filename, sep=sep, on_bad_lines="warn", skip_blank_lines=True, names=names
    )
    # drop lines which contain NaN values in the start_time or end_time columns
    if is_core_contact_plan:
        df.dropna(subset=["start_time", "end_time"], inplace=True)
        # also drop if column 2 is does not contain either fixed or contact
        df = df[df.iloc[:, 1].str.contains("fixed|contact", case=False, na=False)]
        # remove + from start_time and end_time if they are strings in the format of "+NUMBER" and convert to integers
        if df["start_time"].dtype == "object" and re.match(
            r"^\+\d+$", df["start_time"].iloc[0]
        ):
            df["start_time"] = (
                df["start_time"].str.replace("+", "", regex=False).astype(int)
            )
        if df["end_time"].dtype == "object" and re.match(
            r"^\+\d+$", df["end_time"].iloc[0]
        ):
            df["end_time"] = (
                df["end_time"].str.replace("+", "", regex=False).astype(int)
            )

        max_time = df["end_time"].max()

    print(df)
    logger.info(f"Data loaded with {len(df)} records")
    logger.info("Preprocessing data...")

    POSSIBLE_START_COLUMN_NAMES = [
        "start_time",
        "start",
        "contact_start",
        "start_ts",
        "contact_start(s)",
    ]
    START_COLUMN_NAME = detect_column_name(
        df, POSSIBLE_START_COLUMN_NAMES, rename_to="start_time"
    )
    if START_COLUMN_NAME is None:
        logger.error("No valid start time column found in the data.")
        logger.error(
            f"Searched for columns: %s in %s"
            % (POSSIBLE_START_COLUMN_NAMES, df.columns)
        )
        return

    # Define the end time column
    POSSIBLE_END_COLUMN_NAMES = [
        "end_time",
        "end",
        "contact_end",
        "end_ts",
        "contact_end(s)",
    ]
    END_COLUMN_NAME = detect_column_name(
        df, POSSIBLE_END_COLUMN_NAMES, rename_to="end_time"
    )
    if END_COLUMN_NAME is None:
        logger.error("No valid end time column found in the data.")
        logger.error(
            f"Searched for columns: %s in %s" % (POSSIBLE_END_COLUMN_NAMES, df.columns)
        )
        return

    # check if start_time and end_time are integers in seconds or strings indicating a datetime
    using_datetime = False
    print(df["start_time"].dtype, df["end_time"].dtype)
    if df["start_time"].dtype == "int64" and df["end_time"].dtype == "int64":
        pass
    elif df["start_time"].dtype == "object" and df["end_time"].dtype == "object":
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

    # If fixed links are not to be plotted, remove the ones where start_time equals 0 and end_time equals the maximum end_time
    if not plot_fixed_links:
        df = df[~((df["start_time"] == 0) & (df["end_time"] == df["end_time"].max()))]

    # --- New sorting logic to group src-dst and dst-src pairs ---
    # Create a canonical key for each pair to group reciprocal links
    # This ensures (A, B) and (B, A) map to the same key, e.g., ('A', 'B')
    df["canonical_pair_key"] = df.apply(
        lambda row: tuple(sorted((row["src"], row["dst"]))), axis=1
    )

    # Create a DataFrame of unique combinations with their canonical keys
    unique_combinations = df[["src", "dst", "canonical_pair_key"]].drop_duplicates()

    # add column symmetric to indicate if the pair is symmetric, by default set to '-' indicating asymmetric contact
    unique_combinations["symmetric"] = "-"

    # Sort these unique combinations:
    # 1. By the canonical pair key (to group A-B and B-A together)
    # 2. Then by src (to ensure a consistent order within the canonical group, e.g., A-B before B-A)
    unique_combinations_sorted = unique_combinations.sort_values(
        by=["canonical_pair_key", "src"]
    ).reset_index(drop=True)
    combinations = unique_combinations_sorted

    pairs = set()

    # for all canonical pairs, check if start_time and end_time in df are the same, if so set symmetric to '='
    for idx, row in combinations.iterrows():
        src = row["src"]
        dst = row["dst"]
        pair = row["canonical_pair_key"]
        pairs.add(pair)

        logger.debug(f"Checking pair: {pair} (src: {src}, dst: {dst})")
        # find the rows in df that matches this src and dst
        rows1 = df[(df["src"] == src) & (df["dst"] == dst)]
        rows2 = df[(df["src"] == dst) & (df["dst"] == src)]
        if rows1.empty or rows2.empty:
            logger.debug(f"No bidirectional link found for pair: {pair}")
            continue

        # compare shapes of rows1 and rows2
        if rows1.shape[0] != rows2.shape[0]:
            logger.debug(
                f"Different number of contacts for pair: {pair} (src: {src}, dst: {dst})"
            )
            continue

        # compare start_time and end_time of both rows to see if they are the same
        # if they are the same, set symmetric to '='
        if (
            rows1["start_time"].all() == rows2["start_time"].all()
            and rows1["end_time"].all() == rows2["end_time"].all()
        ):
            logger.debug(f"Found symmetric pair: {pair} (src: {src}, dst: {dst})")
            combinations.at[idx, "symmetric"] = "="

    pairs = list(pairs)

    # from symmetric links with "=", remove one of the links and only keep the one with the smaller src
    combinations = combinations[
        ~(
            (combinations["symmetric"] == "=")
            & (combinations["src"] > combinations["dst"])
        )
    ]

    combinations["y_pos"] = range(len(combinations))
    df = df.merge(combinations, on=["src", "dst"])
    # add canonical_pair_key to df
    df["canonical_pair_key"] = df.apply(
        lambda row: tuple(sorted((row["src"], row["dst"]))), axis=1
    )
    logger.info("Data preprocessing complete.")

    logger.info(f"Unique combinations found: {len(combinations)}")
    logger.debug(f"Combinations:\n{combinations}")
    logger.debug(f"DataFrame:\n{df}")

    logger.info("Plotting contact plan...")
    # Create a wide figure
    plt.figure(figsize=(12, 6))

    colors = plt.colormaps.get_cmap("tab20")

    for idx, row in df.iterrows():
        pair_idx = pairs.index(row["canonical_pair_key"])
        row_color = colors(pair_idx % colors.N)  # Use modulo to cycle through colors
        # Plot the contact period as a horizontal bar
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
        labels=combinations["src"] + combinations["symmetric"] + combinations["dst"],
    )

    # Format x-axis with dates or integers
    if using_datetime:
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M:%S"))
    else:
        # format numbers as plain integers
        if human_readable_timestamp:
            # format numbers as days, hours, minutes, seconds
            plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True))
            plt.gca().xaxis.set_major_formatter(
                plt.FuncFormatter(
                    lambda x, _: f"{int(x // 86400)}d {int((x % 86400) // 3600)}h {int((x % 3600) // 60)}m {int(x % 60)}s"
                )
            )
        else:
            plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True))
            plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: int(x)))
    # plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    plt.gcf().autofmt_xdate()

    # Add labels and title
    plt.xlabel("Time")
    plt.ylabel("Contact (Node 1 - Node 2)")
    plt.title("Contact Plan: " + os.path.basename(filename))

    plt.tight_layout()
    if output:
        plt.savefig(output)
        logger.info(f"Plot saved to {output}")
    else:
        logger.info("Displaying plot on screen.")
        plt.show()


def main():
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
    parser.add_argument(
        "-F",
        "--fixed-links",
        action="store_true",
        help="Also plot fixed links that span the whole duration.",
    )
    parser.add_argument(
        "-H",
        "--human-readable-timestamp",
        action="store_true",
        help="Use human-readable timestamps instead of integers.",
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Output file name for the plot (optional)."
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
        plot_contacts(
            args.filename,
            sep=sep,
            names=names,
            is_core_contact_plan=True,
            output=args.output,
            plot_fixed_links=args.fixed_links,
            human_readable_timestamp=args.human_readable_timestamp,
        )
    else:
        plot_contacts(
            args.filename,
            output=args.output,
            plot_fixed_links=args.fixed_links,
            human_readable_timestamp=args.human_readable_timestamp,
        )

    logger.info("Contact plotting completed.")


if __name__ == "__main__":
    main()
