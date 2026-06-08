# **GS → PN Intercompany Invoice Synchronization & VAT Reconciliation**  
### **Python ETL Pipeline | SQL Server | NAV/Business Central**

This project is a full Python replication of a real intercompany business case originally implemented in Power BI. It rebuilds the entire logic as a modular ETL pipeline that compares, validates, and reconciles invoice and credit memo data between two NAV/Business Central companies:

- GS (source)  
- PN (destination)

The pipeline mirrors the production workflow used to ensure that transferred documents are complete, consistent, and compliant with VAT rules. All SQL tables and sample data are masked and synthetic, while the logic reflects real operational processes.

---

# **Features**
- Line‑level comparison of GS and PN invoices & credit memos  
- Detection of missing PN documents (import orders)  
- VAT reconciliation with Match / Mismatch / Import Order flags  
- Automatic credit memo normalization (amounts → negative)  
- Unified master dataset combining all document types  
- Config‑driven SQL extraction (config.yaml)  
- Sensitive field masking for safe sharing  
- Structured Excel output (masked + unmasked)  
- Full logging to console and logs/etl.log  

---

# **Project Structure**

├── extract.py  
├── transform.py  
├── load.py  
├── mappings.py  
├── main.py  
├── config.yaml  
├── output/               # ignored in Git  
├── output_masked/          
└── logs/

---

# **Module & Function Documentation**

## **mappings.py — Centralized Field Mapping**
Defines all mapping dictionaries used to standardize GS and PN data into a unified schema.

Includes:  
- Mappings.CM — credit memo amount fields  
- Mappings.MASTER — unified master dataset fields  
- Mappings.VAT — VAT reconciliation fields  
- Mappings.IMPORT — import order fields  
- Mappings.mask_cols — sensitive fields to mask  

---

## **extract.py — SQL Extraction Layer**
Handles database connections and raw data extraction.

Key functions:  
- get_connection(prefix) — builds a SQL Server connection using environment variables  
- create_df(prefix, query) — executes SQL and returns a DataFrame  
- extract_data() — loads all GS/PN datasets defined in config.yaml  

---

## **transform.py — Core Business Logic**
Implements the full transformation pipeline.

Key functions:  
- merge_doc_types(gs_df, pn_df, doc_type) — merges GS/PN invoices or credit memos using NAV keys  
- cm_amount_to_negative(cm_df) — converts credit memo amounts to negative  
- concat_documents(inv_df, cm_df) — builds the unified master dataset  
- vat_reconciliation(master_df) — computes VAT differences and assigns control flags  
- import_orders(master_df) — identifies GS documents missing in PN  
- mask_sensitive_fields(df) — masks all sensitive business fields  
- transform() — orchestrates the entire transformation and returns all final DataFrames  

---

## **load.py — Output Layer**
Exports all final datasets to Excel.

Key function:  
- load_data(load_dfs) — dynamically writes each DataFrame to output/ or output_masked/  

---

## **main.py — Pipeline Orchestrator**
Entry point for the ETL process.

- Initializes logging  
- Runs the full ETL pipeline  
- Saves all output files  
- Computes summary statistics (VAT matches, import orders)  
- Logs final completion message  

Run with:  
python main.py

---

# **Output Files**

Unmasked (output/):  
- master.xlsx  
- vat_reconciliation.xlsx  
- import_orders.xlsx  

Masked (output_masked/):  
- master_masked.xlsx  
- vat_reconciliation_masked.xlsx  
- import_orders_masked.xlsx  

---

# **Technologies**
- Python 
- SQL Server  
- Excel output  
- Environment variables (.env)  
- YAML configuration  

---

# **Business Purpose**
GS posts financial entries. PN must:

- Rebuild GS invoices  
- Apply Norwegian VAT  
- Detect mismatches  
- Identify missing documents  
- Maintain accurate intercompany reporting  

---

# **Data Privacy**
- All data is masked  
- All SQL tables are synthetic  
- No personal or sensitive company data is included  



## How to Run Locally

1. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

2. **Create local SQL Server database**
   ```
   CREATE DATABASE IntercompanyDemo;
   ```

3. **Create tables**
   Run the script in:
   ```
   sql/create_tables.sql
   ```

4. **Import sample data**
   Import the Excel files from:
   ```
   sample_data/
   ```
   into tables: `gs_inv`, `pn_inv`, `gs_cm`, `pn_cm`.

5. **Create `.env` file**
   ```
   GS_DRIVER=ODBC Driver 17 for SQL Server
   GS_SERVER=localhost
   GS_DB=IntercompanyDemo
   PN_DRIVER=ODBC Driver 17 for SQL Server
   PN_SERVER=localhost
   PN_DB=IntercompanyDemo
   ```

6. **Update `config.yaml`**
   ```
   gs:
     QUERIES:
       gs_inv: "SELECT * FROM gs_inv"
       gs_cm:  "SELECT * FROM gs_cm"
   pn:
     QUERIES:
       pn_inv: "SELECT * FROM pn_inv"
       pn_cm:  "SELECT * FROM pn_cm"
   ```

7. **Run the ETL pipeline**
   ```
   python main.py
   ```

8. **Output files**
   Unmasked:
   ```
   output/master.xlsx
   output/vat_reconciliation.xlsx
   output/import_orders.xlsx
   ```
   Masked:
   ```
   output_masked/master_masked.xlsx
   output_masked/vat_reconciliation_masked.xlsx
   output_masked/import_orders_masked.xlsx
   ```

9. **Logs**
   ```
   logs/etl.log
   ```
