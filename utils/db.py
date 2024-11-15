# -*- coding: utf-8 -*-
"""
Created
@author:
@links:
@description: Database operations.
"""
# ┌─────────┐
# │ Imports │
# └─────────┘

import io
import os
import warnings
from typing import Any, List, Mapping, Optional, Union

import numpy as np
import pandas as pd
from decouple import config
from mysql.connector import Error as MySQLError
from mysql.connector import MySQLConnection
from mysql.connector import OperationalError as MySQLOperationalError
from mysql.connector import connect
from mysql.connector.connection_cext import CMySQLConnection
from pypika import Query, Table
from pypika import functions as fn
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, OperationalError

# ┌────────────────┐
# │ Initialization │
# └────────────────┘

_engine: Optional[Engine] = None
_connection: Optional[MySQLConnection] = None

# ┌───────────────────┐
# │ Engine Management │
# └───────────────────┘


def create_sql_engine(env: Optional[str] = None, database: Optional[str] = None) -> Engine:
    """
    Create a SQLAlchemy engine for MySQL connection.
    :param env: DEV | PROD
    :param database: DATABASE
    :return: Engine: A SQLAlchemy Engine object for the MySQL database.
    """
    env = config("ENV")
    database_user = config("DB_USER")
    database_pw = config("DB_PW")
    database_host = config(f"DB_HOST_{env}")
    database_port = config(f"DB_PORT_{env}")
    database = config("DATABASE")

    db_engine = create_engine(
        f"mysql+mysqlconnector://{database_user}:{database_pw}@{database_host}:{database_port}/{database}?charset=utf8mb4",
        connect_args={"allow_local_infile": True},
    )

    return db_engine


def create_sql_connection(db_engine: Engine) -> Optional[CMySQLConnection]:
    """
    Create a MySQL connection using the provided SQLAlchemy engine.

    :param db_engine: SQLAlchemy Engine object.
    :return: MySQL connection object or None if the connection fails.
    """
    try:
        db_params = db_engine.url.translate_connect_args()
        connection = connect(allow_local_infile=True, **db_params)

        if connection.is_connected():
            return connection
        else:
            print("Failed to establish connection despite no errors.")
            return None

    except MySQLError as e:
        print(f"MySQL-specific error occurred: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def get_engine() -> Engine:
    """
    Get the current SQLAlchemy engine, creating it if it doesn't exist.

    Returns:
        Engine: The SQLAlchemy Engine object.
    """
    global _engine
    if _engine is None:
        _engine = create_sql_engine()  # Create engine once
    return _engine


def get_connection() -> CMySQLConnection:
    """
    Get the current database connection, creating it if it doesn't already exist.

    Returns:
        Connection: The MySQLConnection object.
    """
    global _connection
    try:
        # Check if the connection is None or not connected, and create a new one if needed
        if _connection is None or not _connection.is_connected():
            _connection = create_sql_connection(db_engine=get_engine())
            if _connection is None:
                raise ConnectionError("Failed to establish a database connection.")

        return _connection

    except Exception as e:
        print(f"Error in get_connection: {e}")
        raise


def reset_engine_and_connection():
    """
    Reset the engine and connection, forcing a recreation with updated credentials.
    """
    global _engine, _connection
    _engine = create_sql_engine()  # Recreate the engine with updated credentials
    _connection = create_sql_connection(db_engine=_engine)  # Recreate the connection


# ┌─────────────────────┐
# │ Query Execution     │
# └─────────────────────┘


def db_query(
    query: str, params: Optional[Mapping[str, Union[str, int, float]]] = None
) -> pd.DataFrame:
    """
    Query the database.

    Args:
        query (str): The SQL query string to execute.
        params (Optional[Dict[str, Union[str, int, float]]]): Dictionary of parameters to bind to the query.

    Returns:
        pd.DataFrame: A DataFrame containing the query results.
    """
    try:
        table = pd.read_sql_query(text(query), con=get_engine(), params=params)
        # Use the shared connection for the query
        return table

    except OperationalError as e:
        # Handle SQLAlchemy's OperationalError, particularly from MySQL
        if isinstance(e.orig, MySQLOperationalError):
            error_code = e.orig.errno
            if error_code in [1045, 2006, 2013]:  # Common MySQL connection errors
                print("Database connection issue detected. Recreating the engine and connection.")
                reset_engine_and_connection()

                # Retry with the updated connection
                return pd.read_sql_query(text(query), con=get_engine(), params=params)
        else:
            raise e

    except DBAPIError as e:
        # Handle SQLAlchemy's DBAPIError
        if e.connection_invalidated:
            print("Connection invalidated. Reconnecting.")
            reset_engine_and_connection()
            return pd.read_sql_query(text(query), con=get_engine(), params=params)
        else:
            raise e

    except Exception as e:
        # General exception handling for all other errors (e.g., pandas, numpy)
        print(f"An unexpected error occurred: {e}")
        raise


def db_execute(query: str, params: Optional[Mapping[str, Union[str, int, float]]] = None) -> None:
    """
    Execute a non-select SQL query (e.g., CREATE, INSERT, UPDATE) using the shared engine and connection,
    with automatic retries if authentication fails or the connection becomes unavailable.

    Args:
        query (str): The SQL query string to execute.
        params (Optional[Mapping[str, Union[str, int, float]]]): Dictionary of parameters to bind to the query.
    """
    try:
        # Use the engine to execute the non-select query
        with get_engine().connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(text(query), params)
                transaction.commit()
            except Exception as e:
                transaction.rollback()  # Rollback in case of errors
                raise e

    except OperationalError as e:
        # Handle SQLAlchemy's OperationalError, particularly from MySQL
        if isinstance(e.orig, MySQLOperationalError):
            error_code = e.orig.errno
            if error_code in [1045, 2006, 2013]:  # Common MySQL connection errors
                print("Database connection issue detected. Recreating the engine and connection.")
                reset_engine_and_connection()

                # Retry the query with the updated connection
                with get_engine().connect() as connection:
                    transaction = connection.begin()
                    try:
                        connection.execute(text(query), params)
                        transaction.commit()  # Commit after retry
                    except Exception as retry_error:
                        transaction.rollback()
                        raise retry_error
            else:
                raise e

    except DBAPIError as e:
        # Handle SQLAlchemy's DBAPIError
        if e.connection_invalidated:
            print("Connection invalidated. Reconnecting.")
            reset_engine_and_connection()

            # Retry the query after reconnecting
            with get_engine().connect() as connection:
                transaction = connection.begin()
                try:
                    connection.execute(text(query), params)
                    transaction.commit()
                except Exception as retry_error:
                    transaction.rollback()
                    raise retry_error
        else:
            raise e

    except Exception as e:
        # General exception handling for all other errors
        print(f"An unexpected error occurred: {e}")
        raise


def create_database_table(table_name: str):
    """
    Create database table if it doesn't exist.'

    Args:
        table_name (str): The table name.

    """

    # Mapping table names to their respective SQL creation queries
    table_creation_queries = {
        "table_xyz": """
            CREATE TABLE table_xyz (
            id INT AUTO_INCREMENT PRIMARY KEY,
            time DATETIME
            );
        """,
    }

    # Query to check if the table exists
    q = """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = :database_name
            AND table_name = :table_name
        ) AS table_exists;
    """

    database_name = get_engine().url.database

    # Ensure database_name is not None
    if database_name is None:
        raise ValueError("Database name cannot be None")

    params = {"database_name": database_name, "table_name": table_name}

    # Check if the table exists
    exists = bool(db_query(q, params).iloc[0]["table_exists"])

    # Create the table if it doesn't exist
    if not exists:
        create_query = table_creation_queries.get(table_name)
        if create_query:
            db_execute(create_query)


def replace_special_characters_with_placeholders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces tab and newline characters in all text fields of the DataFrame with placeholders.

    :param df: The DataFrame to process.
    :return: A new DataFrame with tab and newline characters replaced by placeholders in text fields.
    """

    # Define a function to replace tab and newline characters with placeholders
    def replace_placeholders(value):
        if isinstance(value, str):
            return value.replace("\t", "[TAB]").replace("\n", "[NEWLINE]")
        return value

    # Apply the replace function to all text columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(replace_placeholders)

    return df


def replace_placeholders_with_special_characters(text: str) -> str:
    """
    Replaces tab and newline placeholders in text fields with special characters.

    :param text: Text to process.
    :return: Cleaned text.
    """
    return text.replace("[TAB]", "\t").replace("[NEWLINE]", "\n")


def pop(data: pd.DataFrame, table_name: str) -> None:
    """
    Import data into a MySQL table using the LOAD DATA LOCAL INFILE method.

    :param data: DataFrame containing the data to be inserted into the database.
    :param table_name: Name of the table where the data will be inserted.
    :return: None
    """

    if "id" in data.columns:
        # Set 'id' column to None (NULL)
        data["id"] = "NULL"

    temp_file_path = "temp_data.tsv"

    try:

        data = data.replace({np.nan: r"\N", None: r"\N"})
        data = data.infer_objects(copy=False)
        data = replace_special_characters_with_placeholders(data)
        output = io.StringIO()
        data.to_csv(output, sep="\t", header=False, index=False, lineterminator="\n")
        output.seek(0)
        contents = output.getvalue()

        # Write the data to a temporary file

        with open(temp_file_path, "w", newline="", encoding="utf-8") as f:
            f.write(contents)

        load_query = (
            f"LOAD DATA LOCAL INFILE '{temp_file_path}' INTO TABLE {table_name} "
            f"CHARACTER SET 'utf8mb4' FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n';"
        )

        try:

            db_execute(load_query)

        except MySQLError as err:
            print(f"MySQL Error: {err}")
        except (IOError, OSError) as err:
            print(f"File Error: {err}")
        finally:

            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def db_query_statement(
    table_name: str,
    columns: Optional[List[Any]] = None,
    identifier: Optional[List[Any]] = None,
    time_start: Optional[str] = None,
    time_end: Optional[str] = None,
    most_recent: Optional[bool] = None,
    filter_col: Optional[str] = None,
    filter_col_vals: Optional[List[Any]] = None,
) -> str:
    """
    Generates MySQL query string programmatically.
    :param table_name: Identify table name.
    :param columns: Identify column names.
    :param identifier: Identify identifiers.
    :param time_start: Identify start time.
    :param time_end: Identify end time.
    :param most_recent: Filter only most recent.
    :param filter_col: Filter a column.
    :param filter_col_vals: Filter a pair of column and values.
    :return: MySQL Query String.
    """
    table = Table(table_name)

    # SELECT COLUMNS ELSE *
    if columns:
        columns_str = '","'.join(columns)  # Create a new variable to hold the joined string
        q = Query.from_(table).select(columns_str)
    else:
        q = Query.from_(table_name).select("*")

    if identifier:
        q = q.where(table.uid.isin(identifier))
    if time_start:
        q = q.where(table.time >= time_start)
    if time_end:
        q = q.where(table.time <= time_end)
    if most_recent:
        q_max_time = Query.from_(table_name).select(fn.Max(table.time))
        q = q.where(table.time == q_max_time)

    # ORDER ACCORDINGLY
    if identifier:
        q = q.orderby("identifier", "time")
    else:
        q = q.orderby("time")

    if filter_col:
        q = q.where(table.field(name="feature").isin(filter_col_vals))

    sql_statement = str(q)

    return sql_statement


def map_dtype_to_sql(column_dtype: str) -> str:
    """
    Map pandas data types to MySQL data types.

    :param column_dtype: pandas datatype
    :return: MySQL equivalent datatype
    """
    dtype_str = str(column_dtype)

    # Dictionary mapping pandas dtypes to MySQL types
    dtype_mapping = {
        "int": "INT",
        "Int": "INT",
        "float": "DOUBLE",
        "bool": "BOOLEAN",
        "datetime": "DATETIME",
        "timedelta": "TIME",
        "category": "TEXT",
        "object": "TEXT",
        "complex": "TEXT",
        "period": "TEXT",
    }

    # Find the first matching type in the dictionary
    for key, sql_type in dtype_mapping.items():
        if key in dtype_str:
            return sql_type

    # Default case
    return "TEXT"


def generate_create_table_command(df: pd.DataFrame, table_name: str = "my_table") -> str:
    """
    Generate MySQL CREATE TABLE command based on DataFrame's dtypes.
    :param df: The dataframe to identify the MySQL table structure.
    :param table_name: The table name.
    :return: Create table MySQL Command.
    """
    column_definitions = ["id INT AUTO_INCREMENT PRIMARY KEY"]
    for column, dtype in df.dtypes.items():
        sql_type = map_dtype_to_sql(dtype)
        column_definitions.append(f"{column} {sql_type}")

    columns_str = ",\n".join(column_definitions)
    create_table_command = f"CREATE TABLE {table_name} (\n{columns_str}\n);"

    print(create_table_command)

    return create_table_command


def generate_create_index_command(
    table_name: str, columns: Optional[List[Any]] = None, unique: bool = False
) -> str:
    """
    Generate MySQL CREATE INDEX command based on DataFrame's dtypes.
    :param table_name: MySQL table name.
    :param columns: Columns to be included in the index.
    :param unique: For unique Index.
    :return: Create Index MySQL Command.
    """
    unique_str = "UNIQUE " if unique else ""
    columns_str = ", ".join(columns) if columns is not None else ""

    create_index_command = (
        f"CREATE {unique_str}INDEX {table_name}_index ON {table_name} ({columns_str});"
    )

    return create_index_command


def infer_column_dtype(column: pd.Series) -> str:
    """
    Infer the datatype of a pandas Series.

    :param column: A pandas Series representing a column of data.
    :return: A string representing the inferred data type.
    """
    column = column.dropna()
    if column.empty:
        return "object"

    datetime_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
    ]

    # Check for datetime
    for fmt in datetime_formats:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            try:
                datetime_column = pd.to_datetime(column, format=fmt, errors="coerce")
                if datetime_column.notna().all():
                    return "datetime64[ns]"
            except (ValueError, TypeError):
                pass

    # Check for int
    try:
        int_column = pd.to_numeric(column, errors="coerce")
        if all(int_column == int_column.astype(int)):
            return "Int64"
    except (ValueError, TypeError):
        pass

    # Check for float
    try:
        float_column = pd.to_numeric(column, errors="coerce")
        if float_column.notna().all():
            return "float64"
    except (ValueError, TypeError):
        pass

    return "object"


def mysql_query_generator(table_name):
    q = "select * from table_name"
    return q
