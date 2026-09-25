"""
Export script to dump legal database into standard SQL files with explicit column names and PostgreSQL compatibility.
"""

import sqlite3
import os
import sys

def format_sql_value(val) -> str:
    """Format Python values into standard SQL literals."""
    if val is None:
        return "NULL"
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    else:
        # Standard SQL string escaping (replace single quotes with double single quotes)
        escaped = str(val).replace("'", "''")
        return f"'{escaped}'"


def export_all_sql_formats(db_path: str = "legal_db.sqlite") -> None:
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' does not exist.")
        sys.exit(1)

    print(f"Connecting to database: {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Get list of tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [r[0] for r in cur.fetchall()]

    # 1. Export Standard ANSI SQL dump with explicit column names (legal_db_dump.sql)
    ansi_sql_path = "legal_db_dump.sql"
    print(f"Exporting explicit column ANSI SQL dump to '{ansi_sql_path}'...")
    
    with open(ansi_sql_path, "w", encoding="utf-8") as f:
        f.write("-- ========================================================\n")
        f.write("-- Task A Legal Database Standard ANSI SQL Dump\n")
        f.write("-- Includes Explicit Column Names & Table Schemas\n")
        f.write("-- ========================================================\n\n")
        f.write("BEGIN TRANSACTION;\n\n")

        for table in tables:
            # Table DDL
            cur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
            ddl_res = cur.fetchone()
            if ddl_res and ddl_res[0]:
                f.write(f"-- Table Schema: {table}\n")
                f.write(f"{ddl_res[0]};\n\n")

            # Column Names
            cur.execute(f"PRAGMA table_info({table});")
            col_info = cur.fetchall()
            col_names = [c[1] for c in col_info]
            cols_str = ", ".join([f'"{c}"' for c in col_names])

            # Rows
            cur.execute(f"SELECT * FROM {table};")
            rows = cur.fetchall()
            if rows:
                f.write(f"-- Data Records: {table} ({len(rows)} rows)\n")
                for r in rows:
                    vals_str = ", ".join([format_sql_value(v) for v in r])
                    f.write(f"INSERT INTO \"{table}\" ({cols_str}) VALUES ({vals_str});\n")
                f.write("\n")

        f.write("COMMIT;\n")

    # 2. Export PostgreSQL Native SQL script (legal_db_postgres.sql)
    pg_sql_path = "legal_db_postgres.sql"
    schema_sql_path = "schema.sql"
    print(f"Exporting PostgreSQL Native SQL dump to '{pg_sql_path}'...")

    with open(pg_sql_path, "w", encoding="utf-8") as f:
        f.write("-- ========================================================\n")
        f.write("-- Task A Legal Database PostgreSQL Native Dump\n")
        f.write("-- Includes schema.sql DDL + Explicit Column INSERT Statements\n")
        f.write("-- ========================================================\n\n")
        
        if os.path.exists(schema_sql_path):
            with open(schema_sql_path, "r", encoding="utf-8") as sf:
                f.write(sf.read())
                f.write("\n\n-- ========================================================\n")
                f.write("-- DATA INSERTS FOR POSTGRESQL\n")
                f.write("-- ========================================================\n\n")

        f.write("BEGIN;\n\n")
        
        # PostgreSQL table insertion order to satisfy Foreign Key constraints
        pg_table_order = [
            "canonical_entities",
            "documents",
            "entities",
            "document_entities",
            "relationships",
            "knowledge_chunks",
            "low_confidence_queue",
        ]

        for table in pg_table_order:
            if table not in tables:
                continue
            cur.execute(f"PRAGMA table_info({table});")
            col_info = cur.fetchall()
            col_names = [c[1] for c in col_info]
            cols_str = ", ".join([f'"{c}"' for c in col_names])

            cur.execute(f"SELECT * FROM {table};")
            rows = cur.fetchall()
            if rows:
                f.write(f"-- Data Records: {table} ({len(rows)} rows)\n")
                for r in rows:
                    vals_str = ", ".join([format_sql_value(v) for v in r])
                    f.write(f"INSERT INTO \"{table}\" ({cols_str}) VALUES ({vals_str});\n")
                f.write("\n")

        f.write("COMMIT;\n")

    conn.close()

    size_ansi = os.path.getsize(ansi_sql_path) / (1024 * 1024)
    size_pg = os.path.getsize(pg_sql_path) / (1024 * 1024)
    print(f"Successfully generated '{ansi_sql_path}' ({size_ansi:.2f} MB)")
    print(f"Successfully generated '{pg_sql_path}' ({size_pg:.2f} MB)")


if __name__ == "__main__":
    export_all_sql_formats()
