"""Build the DuckDB database from the raw files by running every SQL file in transform/ in order.

Usage:
    python pipeline.py
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "turbo.duckdb"
SQL_DIR = ROOT / "transform"


def main():
    con = duckdb.connect(str(DB_PATH))
    # The SQL refers to data/raw/... so run it from the project folder.
    con.execute(f"SET file_search_path = '{ROOT.as_posix()}'")

    for sql_file in sorted(SQL_DIR.glob("[0-9][0-9]_*.sql")):
        print(f"Running {sql_file.name}")
        con.execute(sql_file.read_text(encoding="utf-8"))

    for (table,) in con.execute("SHOW TABLES").fetchall():
        rows = con.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
        print(f"  {table}: {rows:,} rows")

    con.close()


if __name__ == "__main__":
    main()