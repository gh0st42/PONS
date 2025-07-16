from networkx.algorithms.operators.binary import symmetric_difference
from pons.net.plans import bandwidth_parser
import logging
import pandas as pd
from pons.net.plans import Contact, CommonContactPlan
from pons.net.plans.core import CoreContact

logger = logging.getLogger(__name__)


def contains_column_or_insert_with_default_value(
    df: pd.DataFrame, col_name: str, default_value: any
) -> bool:
    """
    Checks if a column exists in the DataFrame. If it does not exist, it inserts the column with a default value.
    Returns True if the column already exists or False if it was inserted with the default value.
    """
    if col_name in df.columns:
        return True
    else:
        df[col_name] = default_value
        logger.debug(
            f"Inserted column '{col_name}' with default value '{default_value}'"
        )
        return False


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
            return rename_to
        return col_name
    return None


NODE1_IDENTIFIERS = ["node1", "n1", "src", "source"]
NODE2_IDENTIFIERS = ["node2", "n2", "dst", "destination"]
START_TIMESPAN_IDENTIFIERS = [
    "start",
    "start_time",
    "start_ts",
    "start_timestamp",
    "begin",
    "begin_time",
    "begin_ts",
    "begin_timestamp",
    "contact_start",
    "contact_start(s)",
]
END_TIMESPAN_IDENTIFIERS = [
    "end",
    "end_time",
    "end_ts",
    "end_timestamp",
    "contact_end",
    "contact_end(s)",
]
BANDWIDTH_IDENTIFIERS = [
    "bandwidth",
    "bw",
]


def read_csv(
    filename: str, sep: str = ",", mapping: dict[str, int] | None = None
) -> list[Contact]:
    """
    Reads a CSV file containing contact information and returns a list of contacts.
    :param filename: The path to the CSV file.
    :param sep: The separator used in the CSV file (default is comma).
    :param mapping: An optional mapping from string node identifiers to integer node IDs.
    :return: A list of Contact objects.
    :raises ValueError: If the file cannot be read or if required columns are missing.
    """

    df = pd.read_csv(filename, sep=sep, on_bad_lines="warn", skip_blank_lines=True)
    logger.debug(f"Read {len(df)} rows from {filename}")
    logger.debug("Identifying columns in the data...")
    START_COLUMN_NAME = detect_column_name(
        df, START_TIMESPAN_IDENTIFIERS, rename_to="start_time"
    )
    if START_COLUMN_NAME is None:
        raise ValueError(
            "No valid start time column found in the data. Please check the CSV file."
        )

    END_COLUMN_NAME = detect_column_name(
        df, END_TIMESPAN_IDENTIFIERS, rename_to="end_time"
    )
    if END_COLUMN_NAME is None:
        raise ValueError(
            "No valid end time column found in the data. Please check the CSV file."
        )
    NODE1_COLUMN_NAME = detect_column_name(df, NODE1_IDENTIFIERS, rename_to="node1")
    if NODE1_COLUMN_NAME is None:
        raise ValueError(
            "No valid node1 column found in the data. Please check the CSV file."
        )
    NODE2_COLUMN_NAME = detect_column_name(df, NODE2_IDENTIFIERS, rename_to="node2")
    if NODE2_COLUMN_NAME is None:
        raise ValueError(
            "No valid node2 column found in the data. Please check the CSV file."
        )
    BANDWIDTH_COLUMN_NAME = detect_column_name(
        df, BANDWIDTH_IDENTIFIERS, rename_to="bandwidth"
    )
    if BANDWIDTH_COLUMN_NAME is None:
        logger.warning(
            "No valid bandwidth column found in the data. Defaulting to None for all contacts."
        )
        contains_column_or_insert_with_default_value(df, "bandwidth", None)

    contains_column_or_insert_with_default_value(
        df, "loss", 0.0
    )  # Default loss to 0.0 if not present
    contains_column_or_insert_with_default_value(
        df, "delay", 0.0
    )  # Default delay to 0.0 if not present
    contains_column_or_insert_with_default_value(
        df, "jitter", 0.0
    )  # Default jitter to 0.0 if not present
    contacts = []
    for _, row in df.iterrows():
        try:
            node1 = row[NODE1_COLUMN_NAME]
            node2 = row[NODE2_COLUMN_NAME]
            # check whether node1 and node2 are valid integers
            if not isinstance(node1, int) or not isinstance(node2, int):
                # try mapping them if a mapping is provided
                if mapping is not None:
                    if node1 in mapping:
                        node1 = mapping[str(node1)]
                    else:
                        logger.error(f"Node1 {node1} not found in mapping.")
                        raise ValueError(
                            f"Node1 {node1} not found in mapping. Please check the mapping."
                        )
                    if node2 in mapping:
                        node2 = mapping[str(node2)]
                    else:
                        logger.error(f"Node2 {node2} not found in mapping.")
                        raise ValueError(
                            f"Node2 {node2} not found in mapping. Please check the mapping."
                        )
                else:
                    logger.error(
                        f"Node1 {node1} and Node2 {node2} must be integers or mapped to integers."
                    )
                    raise ValueError(
                        f"Node1 {node1} and Node2 {node2} must be integers or mapped to integers."
                    )
            start_ts = float(row[START_COLUMN_NAME])
            end_ts = float(row[END_COLUMN_NAME])
            is_fixed = end_ts < 0
            bw = None
            if BANDWIDTH_COLUMN_NAME in row and pd.notna(row[BANDWIDTH_COLUMN_NAME]):
                bw = row[BANDWIDTH_COLUMN_NAME]
                bw = bandwidth_parser(bw)
            contact = Contact(
                timespan=(start_ts, end_ts),
                nodes=(node1, node2),
                bw=bw,
                loss=float(row["loss"]),
                delay=float(row["delay"]),
                jitter=float(row["jitter"]),
                fixed=is_fixed,
            )
            contacts.append(contact)
        except Exception as e:
            logger.error(f"Error processing row {row}: {e}")
            continue
    return contacts


def validate_json_contact(item: dict) -> list[str]:
    """
    Validates a contact item from JSON data.
    :param item: A dictionary representing a contact item.
    :return: True if the item is valid, False otherwise.
    """

    is_fixed = item.get("fixed", False)

    # check for start time key
    START_ID = None
    for key in START_TIMESPAN_IDENTIFIERS:
        if key in item:
            logger.debug(f"Found required key '{key}' in item: {item}")
            START_ID = key
            break
    if START_ID == None:
        if is_fixed:
            item["start_time"] = 0.0
            START_ID = "start_time"
        else:
            raise ValueError(
                f"Missing required start time key in item: {item}. Please check the JSON data."
            )
    # check for end time key
    END_ID = None
    for key in END_TIMESPAN_IDENTIFIERS:
        if key in item:
            logger.debug(f"Found required key '{key}' in item: {item}")
            END_ID = key
            break
    if END_ID == None:
        if is_fixed:
            item["end_time"] = -1.0
            END_ID = "end_time"
        else:
            raise ValueError(
                f"Missing required end time key in item: {item}. Please check the JSON data."
            )
    # check for node1 key
    NODE1_ID = None
    for key in NODE1_IDENTIFIERS:
        if key in item:
            logger.debug(f"Found required key '{key}' in item: {item}")
            NODE1_ID = key
            break
    if NODE1_ID == None:
        raise ValueError(
            f"Missing required node1 key in item: {item}. Please check the JSON data."
        )
    # check for node2 key
    NODE2_ID = None
    for key in NODE2_IDENTIFIERS:
        if key in item:
            logger.debug(f"Found required key '{key}' in item: {item}")
            NODE2_ID = key
            break
    if NODE2_ID == None:
        raise ValueError(
            f"Missing required node2 key in item: {item}. Please check the JSON data."
        )

    return [START_ID, END_ID, NODE1_ID, NODE2_ID]


def unify_json_contact(item: dict, found_keys: list[str]) -> dict:
    """
    Unifies the contact item from JSON data by renaming keys to a standard format.
    :param item: A dictionary representing a contact item.
    :param found_keys: A list of keys that were found in the item.
    :return: A dictionary with unified keys.
    """
    unified_item = {}

    unified_item["start_time"] = item[found_keys[0]]
    unified_item["end_time"] = item[found_keys[1]]
    unified_item["node1"] = item[found_keys[2]]
    unified_item["node2"] = item[found_keys[3]]

    # Optional fields
    if "bandwidth" in item:
        unified_item["bandwidth"] = item["bandwidth"]
    elif "bw" in item:
        unified_item["bandwidth"] = item["bw"]
    else:
        unified_item["bandwidth"] = None

    if unified_item["bandwidth"] is not None and isinstance(
        unified_item["bandwidth"], str
    ):
        unified_item["bandwidth"] = bandwidth_parser(unified_item["bandwidth"])

    unified_item["loss"] = item.get("loss", 0.0)
    unified_item["delay"] = item.get("delay", 0.0)
    unified_item["jitter"] = item.get("jitter", 0.0)
    unified_item["fixed"] = item.get("fixed", False)
    unified_item["symmetric"] = item.get("symmetric", False)

    return unified_item


def read_json(filename: str, mapping: dict[str, int] | None = None) -> list[Contact]:
    """
    Reads a JSON file containing contact information and returns a list of contacts.
    :param filename: The path to the JSON file.
    :param mapping: An optional mapping from string node identifiers to integer node IDs.
    :return: A list of Contact objects.
    :raises ValueError: If the file cannot be read or if required fields are missing.
    """
    import json

    with open(filename, "r") as f:
        data = json.load(f)

    contacts = []
    for item in data:
        try:
            # Validate the contact item
            found_keys = validate_json_contact(item)
            # Unify the contact item
            item = unify_json_contact(item, found_keys)

            node1 = item["node1"]
            node2 = item["node2"]
            # check whether node1 and node2 are valid integers
            if not isinstance(node1, int) or not isinstance(node2, int):
                # try mapping them if a mapping is provided
                if mapping is not None:
                    if str(node1) in mapping:
                        node1 = mapping[str(node1)]
                    else:
                        raise ValueError(
                            f"Node1 {node1} not found in mapping. Please check the mapping."
                        )
                    if str(node2) in mapping:
                        node2 = mapping[str(node2)]
                    else:
                        raise ValueError(
                            f"Node2 {node2} not found in mapping. Please check the mapping."
                        )
                else:

                    raise ValueError(
                        f"Node1 {node1} and Node2 {node2} must be integers or mapped to integers."
                    )

            is_fixed = item.get("fixed", False)
            start_ts = float(item.get("start_time", 0.0))
            end_ts = float(item.get("end_time", -1.0))
            if is_fixed:
                if end_ts >= 0:
                    raise ValueError(
                        f"Contact with fixed=True but end_time {item['end_time']} is not negative."
                    )
                if start_ts != 0.0:
                    raise ValueError(
                        f"Contact with fixed=True but start_time {start_ts} is not 0.0."
                    )
            if end_ts < 0 and start_ts == 0 and "fixed" not in item:
                logger.warning(
                    f"Contact with negative end_time {end_ts} and start_time {start_ts} but no 'fixed' key. Assuming fixed contact."
                )
                is_fixed = True

            contact = Contact(
                timespan=(start_ts, end_ts),
                nodes=(node1, node2),
                bw=item.get("bandwidth"),
                loss=item.get("loss", 0.0),
                delay=item.get("delay", 0.0),
                jitter=item.get("jitter", 0.0),
                fixed=is_fixed,
            )
            # Append the contact to the list
            contacts.append(contact)

            if "symmetric" in item and item["symmetric"]:
                # Create a symmetric contact if specified
                symmetric_contact = Contact(
                    timespan=(start_ts, end_ts),
                    nodes=(node2, node1),
                    bw=item.get("bandwidth"),
                    loss=item.get("loss", 0.0),
                    delay=item.get("delay", 0.0),
                    jitter=item.get("jitter", 0.0),
                    fixed=is_fixed,
                )
                contacts.append(symmetric_contact)

        except KeyError as e:
            logger.error(f"Missing key in item {item}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error processing item {item}: {e}")
            continue
    return contacts


def read_ccp(
    filename: str,
    sep: str = ",",
    mapping: dict[str, int] | None = None,
    symmetric: bool = False,
) -> list[Contact]:
    """
    Reads a core contact plan and returns a list of contacts.
    :param filename: The path to the CSV file.
    :param sep: The separator used in the CSV file (default is comma).
    :param mapping: An optional mapping from string node identifiers to integer node IDs.
    :return: A list of Contact objects.
    :raises ValueError: If the file cannot be read or if required columns are missing.
    """

    contacts = []
    for line in open(filename, "r").readlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("a "):
            core_contact = CoreContact.from_string(line, mapping=mapping)
            contact = Contact(
                timespan=core_contact.timespan,
                nodes=core_contact.nodes,
                bw=core_contact.bw,
                loss=core_contact.loss,
                delay=core_contact.delay,
                jitter=core_contact.jitter,
                fixed=core_contact.fixed,
            )
            contacts.append(contact)
            if symmetric:
                symmetric_contact = Contact(
                    timespan=core_contact.timespan,
                    nodes=(core_contact.nodes[1], core_contact.nodes[0]),
                    bw=core_contact.bw,
                    loss=core_contact.loss,
                    delay=core_contact.delay,
                    jitter=core_contact.jitter,
                    fixed=core_contact.fixed,
                )
                contacts.append(symmetric_contact)
    # remove duplicates
    contacts = list({(c.nodes, c.timespan): c for c in contacts}.values())

    return contacts
