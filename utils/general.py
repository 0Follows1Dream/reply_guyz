# -*- coding: utf-8 -*-
"""
Created
@author:
@links:
@description:
"""

# ┌─────────┐
# │ Imports │
# └─────────┘

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests

# ┌────────────┐
# │ Parameters │
# └────────────┘
# ┌───────────────────┐
# │ Program functions │
# └───────────────────┘


def filter_dict(d: Dict[str, Any], filter_keys: List[str]) -> Dict[str, Any]:
    """
    Filters a dictionary based on a list of keys. If the key 'description' is present,
    it extracts the 'en' value from the nested dictionary.
    """
    filter_keys = [key for key in d.keys() if key in filter_keys]

    if filter_keys:
        new_dict = {}
        for k in filter_keys:
            if k == "description":
                new_dict[k] = d[k]["en"]
            else:
                new_dict[k] = d[k]

        return new_dict

    return {}


def flatten_dict(d: dict, parent_key: str = "", sep: str = "_") -> dict:
    """
    Flatten nested elements within a dictionary.
    :param d: Dictionary to have nested elements flattened within.
    :param parent_key: Define a parent key to assign the dictionary items.
    :param sep: Seperator key for the variable names created.
    :return: The flattened dictionary.
    """

    items = {}
    if d is None:  # Handle None values gracefully
        return items

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


def dict_to_dataframe(d: Dict[str, Any]) -> pd.DataFrame:
    """
    Converts a nested dictionary into a pandas DataFrame by flattening the dictionary
    and using the flattened data as a single row in the DataFrame.

    Args:
        d (Dict[str, Any]): The input dictionary to be converted into a DataFrame.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the flattened dictionary as a single row.
    """
    flat_dict = flatten_dict(d)
    return pd.DataFrame([flat_dict])


def sanitize_table_name(table_name: str) -> str:
    """
    Ensures the table name contains only alphanumeric characters and underscores.

    Args:
        table_name (str): The table name to be sanitized.

    Returns:
        str: The sanitized table name.
    """
    # Ensure the table name contains only alphanumeric characters and underscores
    if not re.match(r"^[A-Za-z0-9_]+$", table_name):
        raise ValueError("Invalid table name provided")
    return table_name


def api_call(
    url: str,
    method: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None,
    params: Optional[Dict[str, str]] = None,
    retries: int = 5,
    time_sleep: int = 20,
) -> Optional[Dict[str, Any]]:
    """
    Makes an API call with the specified parameters, handling retries for specific HTTP errors.

    Args:
        url (str): The URL of the API endpoint.
        method (str): The HTTP method to use for the request (e.g., 'GET', 'POST').
        headers (Optional[Dict[str, str]]): Optional HTTP headers for the request.
        data (Optional[Any]): Optional data to send in the body of the request.
        params (Optional[Dict[str, str]]): Optional query parameters for the request.
        retries (int): The number of retry attempts for the request.
        time_sleep (int): The amount of time to sleep between retries, in seconds.

    Returns:
        Optional[Dict[str, Any]]: The JSON response from the API as a dictionary if successful, otherwise None.
    """

    for attempt in range(retries):
        try:
            response = requests.request(method, url, headers=headers, data=data, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            if response.status_code == 429:
                print(f"429 Too Many Requests. Retrying in {time_sleep} seconds...")
                time.sleep(time_sleep)
                continue  # Retry the request
            else:
                print(f"HTTP Error: {err}")
                break  # Exit loop on other HTTP errors
    return None  # Return None if all retries fail


def convert_text_to_date(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    for col in columns:
        df[col] = pd.to_datetime(df[col]).dt.tz_convert("UTC").dt.tz_localize(None)
    return df


def convert_float_to_int(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    for col in columns:
        df[col] = df[col].astype("Int64").astype(str).replace("<NA>", np.nan)
    return df


def load_template_msg(file_name, templates_dir=os.path.join("bot", "templates")):
    file_path = os.path.join(templates_dir, file_name)
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def load_template_json(file_name, templates_dir=os.path.join("bot", "templates")):
    file_path = os.path.join(templates_dir, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    return json_data


# ┌─────────────────────┐
# │ Load & process data │
# └─────────────────────┘


# ┌──────────┐
# │ Programs │
# └──────────┘
