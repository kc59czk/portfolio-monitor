import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import argparse
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()
# Configuration
# SQLite database file
# Ensure the SQLite DB file is set in the environment variable
SQLITE_DB = os.getenv('SQLITE_DB', 'stocks.db')
if not SQLITE_DB:
    raise ValueError("Please set the SQLITE_DB environment variable to your SQLite database file path.")   

POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password'),
    'dbname': os.getenv('POSTGRES_DBNAME', 'portfel_monitor')
}


TABLES = [
    'users',
    'tickers',
    'prices',
    'indicators',
    'trades',
    'alerts',
    'alert_log',
    'volume_spikes'
]

def get_pg_identity_columns(pg_cur, table):
    pg_cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s AND is_identity = 'YES'
    """, (table,))
    return [row[0] for row in pg_cur.fetchall()]

def migrate(dry_run=False, preview_rows=5):
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
    pg_cur = pg_conn.cursor()

    for table in TABLES:
        print(f"\n🔄 Migrating table: {table}")
        sqlite_rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
        if not sqlite_rows:
            print(f"⚠️  No data in {table}")
            continue

        # Get SQLite columns
        sqlite_columns = [desc[1] for desc in sqlite_conn.execute(f"PRAGMA table_info({table})")]

        # Get identity columns in Postgres
        identity_columns = get_pg_identity_columns(pg_cur, table)

        # Remove identity columns from insert
        insert_columns = [col for col in sqlite_columns if col not in identity_columns]
        col_str = ", ".join(insert_columns)
        rows = [tuple(row[col] for col in insert_columns) for row in sqlite_rows]

        if dry_run:
            print(f"🧪 Dry run: would insert {len(rows)} rows into '{table}' (skipping identity columns: {identity_columns})")
            for i, row in enumerate(rows[:preview_rows]):
                print(f"   → {row}")
            if len(rows) > preview_rows:
                print(f"   ...and {len(rows) - preview_rows} more rows.")
        else:
            try:
                insert_query = f'INSERT INTO {table} ({col_str}) VALUES %s'
                execute_values(pg_cur, insert_query, rows)
                pg_conn.commit()
                print(f"✅ Inserted {len(rows)} rows into {table}")
            except Exception as e:
                pg_conn.rollback()
                print(f"❌ Error inserting into {table}: {e}")

    pg_cur.close()
    pg_conn.close()
    sqlite_conn.close()

    print("\n🎉 Migration complete (dry-run)." if dry_run else "\n🎉 Migration complete.")

# --- CLI ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQLite → PostgreSQL Migrator with Identity Handling")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not insert")
    args = parser.parse_args()

    migrate(dry_run=args.dry_run)
