import logging
import os
from transform import transform
from load import load_data

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "etl.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    # Start the ETL pipeline
    logging.info("Starting ETL pipeline")

    load_dfs = transform()

    load_data(load_dfs)

    vat_df = load_dfs["output"]["vat_reconciliation"]
    import_df = load_dfs["output"]["import_orders"]

    vat_count = len(vat_df[vat_df["_merge"] == "both"])
    import_count = len(import_df)

    logging.info(f"ETL pipeline completed successfully | VAT reconciled: {vat_count} | Import orders: {import_count}")
