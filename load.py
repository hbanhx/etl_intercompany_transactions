import logging
import os


def load_data(load_dfs):
    logging.info(f"Starting loading data")
    load_data = load_dfs

    base = os.path.dirname(os.path.abspath(__file__))

    for dir, dfs in load_data.items():
        dir_path = os.path.join(base, f"{dir}")
        os.makedirs(dir_path, exist_ok=True)
        for name, df in dfs.items():
            path = os.path.join(dir_path, f"{name}.xlsx")
            df.to_excel(path, index=False)
            logging.info(f"Saved {name} file: {os.path.relpath(path)}")

    logging.info("Data loaded into Excel files successfully")