import logging
import yaml
import pyodbc 
from dotenv import load_dotenv
import os
import pandas as pd

with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

load_dotenv()

def get_connection(prefix):
    gs_driver = os.getenv(f"{prefix}_DRIVER")
    gs_server = os.getenv(f"{prefix}_SERVER")
    gs_database = os.getenv(f"{prefix}_DB")
    conn = pyodbc.connect(
        f'DRIVER={gs_driver};'
        f'SERVER={gs_server};'
        f'DATABASE={gs_database};'
        f'Trusted_Connection=yes;'
        )
    return conn

def create_df(connection_prefix, db):
    # Establish connection and execute query to create DataFrame
    conn = get_connection(connection_prefix)
    raw_dfs = pd.read_sql_query(db, conn)
    logging.info(f"DataFrame created for {connection_prefix}")
    return raw_dfs       

def extract_data():
    logging.info("Starting data extraction")

    raw_dfs = {}

    # SQL queries are defined in the config file, loop through each entity and query to extract data
    # Create DataFrames for each query and store in a dictionary
    for prefix, settings in CONFIG.items():
        for key, query in settings["QUERIES"].items():
            logging.info(f"Extracting {key} from {prefix}")
            raw_dfs[key] = create_df(prefix, query)


    logging.info(f"Extraction complete: {len(raw_dfs)} datasets loaded")
    return raw_dfs
