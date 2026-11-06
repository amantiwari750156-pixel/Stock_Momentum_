import sqlite3, json
from pathlib import Path
import pandas as pd
from datetime import datetime

def connect(db_path="data/scans.db"):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)

def init_db(db_path="data/scans.db"):
    with connect(db_path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
            config_json TEXT NOT NULL, result_count INTEGER NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS scan_results (
            scan_id INTEGER PRIMARY KEY, results_json TEXT NOT NULL)""")

def save_scan(results: pd.DataFrame, config: dict, db_path="data/scans.db") -> int:
    rows = results.copy()
    # Convert timestamps and NumPy scalars into JSON-safe Python values.
    payload = json.loads(rows.to_json(orient="records", date_format="iso"))
    with connect(db_path) as con:
        cur = con.execute("INSERT INTO scans (created_at, config_json, result_count) VALUES (?, ?, ?)",
                          (datetime.now().isoformat(timespec="seconds"), json.dumps(config, default=str), len(results)))
        scan_id = cur.lastrowid
        con.execute("INSERT INTO scan_results (scan_id, results_json) VALUES (?, ?)",
                    (scan_id, json.dumps(payload, allow_nan=True)))
        return scan_id

def list_scans(db_path="data/scans.db"):
    with connect(db_path) as con:
        return pd.read_sql_query("SELECT * FROM scans ORDER BY id DESC", con)

def get_scan_results(scan_id: int, db_path="data/scans.db"):
    with connect(db_path) as con:
        row = con.execute("SELECT results_json FROM scan_results WHERE scan_id = ?", (scan_id,)).fetchone()
    if not row:
        return pd.DataFrame()
    return pd.DataFrame(json.loads(row[0]))
