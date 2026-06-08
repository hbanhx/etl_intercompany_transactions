import logging
from extract import extract_data 
import pandas as pd
from mappings import Mappings


def merge_doc_types(gs_df, pn_df, doc_type):
    # Merge invoices or credit memos from both company codes based on document type

    logging.info(f"Merging {doc_type} invoices and credit memos from entities")

    # Add document type column to identify whether the record is an invoice or credit memo
    gs_df["doc_type"] = doc_type
    pn_df["doc_type"] = doc_type

    # prefix columns to avoid naming conflicts during merges
    gs = gs_df.add_prefix(f"{doc_type}_gs_")
    pn = pn_df.add_prefix(f"{doc_type}_pn_")

    # Merge keys for invoices and credit memos
    if doc_type == "invoice":
        left_keys  = ['invoice_gs_No_', 'invoice_gs_Sales Invoice Line#Line No_']
        right_keys = ['invoice_pn_Order No_', 'invoice_pn_Sales Invoice Line#Line No_']

    elif doc_type == "credit_memo":
        left_keys  = ['credit_memo_gs_No_', 'credit_memo_gs_Sales Cr_Memo Line#Line No_']
        right_keys = ['credit_memo_pn_Pre-Assigned No_', 'credit_memo_pn_Sales Cr_Memo Line#Line No_']

    # Merge GS + PN
    merged_doc_type_df = pd.merge(
        gs,
        pn,
        left_on=left_keys,
        right_on=right_keys,
        how="outer",
        indicator=True
    )
    logging.info(f"{doc_type.capitalize()} merge complete: {len(merged_doc_type_df)} rows")
    return merged_doc_type_df

def cm_amount_to_negative(cm_df):
    # Convert credit memo amounts to negative for reconciliation

    for column in Mappings.CM.keys():
        if column in cm_df.columns:
            cm_df[column] = cm_df[column] * -1

    return cm_df


def concat_documents(inv_df, cm_df):
    # Concatenate invoices and credit memos into a single DataFrame

    logging.info("Concatenating invoice and credit memo documents")

     # Ensure both DataFrames have the same columns before concatenation
    inv_df = inv_df.rename(columns=Mappings.MASTER)
    cm_df = cm_df.rename(columns=Mappings.MASTER)

    master_columns = []
    for column in Mappings.MASTER.values():
        if column in inv_df.columns or column in cm_df.columns:
            if column not in master_columns:
                master_columns.append(column)

    if "_merge" in inv_df.columns or "_merge" in cm_df.columns:
        master_columns.append("_merge")
    
    # Reindex both DataFrames to have the same columns
    inv_df = inv_df.reindex(columns=master_columns)
    cm_df = cm_df.reindex(columns=master_columns)

    # Concatenate invoices and credit memos into a single master DataFrame
    master_df = pd.concat([inv_df, cm_df], ignore_index=True)

    logging.info(f"Concatenation complete: {len(master_df)} rows")
    return master_df


def vat_reconciliation(master_df):
    # Rename columns and create a unified set of columns for both DataFrames
    logging.info("Performing VAT reconciliation")

    master_df = master_df.rename(columns=Mappings.VAT)

    vat_columns = []
    for column in Mappings.VAT.values():
        if column in master_df.columns:
            if column not in vat_columns:
                vat_columns.append(column)

    if "_merge" in master_df.columns:
        vat_columns.append("_merge")

    # Reindex master_df to create vat_df with the same columns
    vat_df = master_df.reindex(columns=vat_columns)

    # Calculate VAT differences and control flags
    vat_df['Difference in Amount'] = vat_df['Amount GS'] - vat_df['Amount PN']
    vat_df['VAT Amount PN'] = vat_df['Amount Including VAT PN'] - vat_df['Amount PN']
    same_doc = vat_df["Document No. GS"] == vat_df["Order No. PN"]
    same_amount = vat_df["Amount GS"] == vat_df["Amount PN"]

    vat_df["Control"] = "Import Order"
    vat_df.loc[same_doc & same_amount, "Control"] = "Match"
    vat_df.loc[same_doc & ~same_amount, "Control"] = "Mismatch"

    logging.info(f"VAT reconciliation complete: {len(vat_df)} rows")
    return vat_df.sort_values(by=['Posting Date GS', 'Order No. GS'], ascending=True)


def import_orders(master_df):
    # Rename columns and create a unified set of columns for both DataFrames
    
    logging.info("Preparing import orders")

    master_df = master_df.rename(columns=Mappings.IMPORT)

    import_columns = []
    for column in Mappings.IMPORT.values():
        if column in master_df.columns:
            if column not in import_columns:
                import_columns.append(column)
    
    if "_merge" in master_df.columns:
        import_columns.append("_merge")

    # Reindex master_df to create import_df with the same columns
    import_df = master_df.reindex(columns=import_columns)

     # Find documents for import in PN
    import_orders = master_df.loc[master_df["_merge"] == "left_only", ["Document No. GS"]].drop_duplicates()

    # Filter import_df by matching keys
    import_df = pd.merge(import_df, import_orders, on=["Document No. GS"], how="inner")
    
    logging.info(f"Import orders complete: {len(import_df)} records")
    return import_df

def mask_sensitive_fields(dataframe):
    # Mask business data 
    data_mask = dataframe.copy()
    mask_value = "*" * 10 
    for col in Mappings.mask_cols:
        if col in data_mask.columns:
            data_mask[col] = mask_value

    return data_mask


def transform():
    # Transformation pipeline
    logging.info("Starting data transformation")
    
    # Extract data using the extract module
    raw_dfs = extract_data()
    logging.info("Raw data extraction complete")

    # Merge invoices and credit memos from both company codes
    inv_df = merge_doc_types(raw_dfs['gs_inv'], raw_dfs['pn_inv'], 'invoice')
    cm_df = merge_doc_types(raw_dfs['gs_cm'], raw_dfs['pn_cm'], 'credit_memo')
    
    # Convert credit memo amounts to negative for reconciliation
    cm_df = cm_amount_to_negative(cm_df)

    # Concatenate invoices and credit memos into a single DataFrame
    master_df = concat_documents(inv_df, cm_df)

    # Perform VAT reconciliation
    vat_df = vat_reconciliation(master_df)

    # Perform import order
    import_pn_df = import_orders(master_df)

    # Mask sensitive data
    master_df_masked = mask_sensitive_fields(master_df)
    vat_df_masked = mask_sensitive_fields(vat_df)
    import_pn_df_masked = mask_sensitive_fields(import_pn_df)


    load_dfs = {
        "output": {
            "master": master_df,
            "vat_reconciliation": vat_df,
            "import_orders": import_pn_df
        },
        "output_masked": {
            "master_masked": master_df_masked,
            "vat_reconciliation_masked": vat_df_masked,
            "import_orders_masked": import_pn_df_masked
        }
    }

    logging.info("Data transformation complete")
    return load_dfs