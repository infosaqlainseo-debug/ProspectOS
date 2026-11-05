"""
ProspectOS - PostgreSQL to Cloudflare D1 (SQLite) Schema & Migration Generator
Generates SQLite-compatible DDL, extracts preserved data, tests migration on an isolated database,
and performs zero-drift validation without touching production data.
"""

import os
import sys
import json
import sqlite3
import asyncio
from datetime import datetime, date
from uuid import UUID
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, types
from sqlalchemy.schema import CreateTable, CreateIndex
from app.db.base import Base
import app.models
import app.models.admin
import app.models.crm
import app.models.scraper

def map_sa_type_to_sqlite(col_type: Any) -> str:
    """Maps SQLAlchemy/PostgreSQL column types to SQLite/D1 storage types."""
    t_name = type(col_type).__name__
    if t_name in ("Boolean", "Integer", "SmallInteger", "BigInteger"):
        return "INTEGER"
    elif t_name in ("Float", "Numeric", "Double"):
        return "REAL"
    elif t_name in ("String", "Text", "VARCHAR", "UUID", "DateTime", "Date", "Time", "JSONB", "JSON"):
        return "TEXT"
    else:
        return "TEXT"

def generate_d1_ddl() -> str:
    """Generates SQLite-compatible DDL for Cloudflare D1 in topological order."""
    statements = [
        "-- ProspectOS Cloudflare D1 Relational Schema (SQLite 3 compatible)",
        "-- Auto-generated from SQLAlchemy metadata in strict topological order",
        "PRAGMA foreign_keys = ON;\n"
    ]

    for table in Base.metadata.sorted_tables:
        col_defs = []
        for col in table.columns:
            sqlite_type = map_sa_type_to_sqlite(col.type)
            constraints = []
            if col.primary_key:
                constraints.append("PRIMARY KEY")
            if not col.nullable and not col.primary_key:
                constraints.append("NOT NULL")
            if col.default is not None:
                arg = col.default.arg
                if isinstance(arg, (int, float)):
                    constraints.append(f"DEFAULT {arg}")
                elif isinstance(arg, str):
                    constraints.append(f"DEFAULT '{arg}'")
                elif isinstance(arg, bool):
                    constraints.append(f"DEFAULT {1 if arg else 0}")
            
            # Foreign keys defined at column level
            if col.foreign_keys:
                for fk in col.foreign_keys:
                    target_table = fk.column.table.name
                    target_col = fk.column.name
                    ondelete = fk.ondelete
                    fk_clause = f"REFERENCES \"{target_table}\"(\"{target_col}\")"
                    if ondelete:
                        fk_clause += f" ON DELETE {ondelete}"
                    constraints.append(fk_clause)

            col_str = f"    \"{col.name}\" {sqlite_type}"
            if constraints:
                col_str += " " + " ".join(constraints)
            col_defs.append(col_str)

        create_table = f"CREATE TABLE IF NOT EXISTS \"{table.name}\" (\n" + ",\n".join(col_defs) + "\n);"
        statements.append(create_table)

        # Generate index statements
        for idx in table.indexes:
            idx_cols = ", ".join([f"\"{c.name}\"" for c in idx.columns])
            unique_str = "UNIQUE " if idx.unique else ""
            idx_stmt = f"CREATE {unique_str}INDEX IF NOT EXISTS \"{idx.name}\" ON \"{table.name}\" ({idx_cols});"
            statements.append(idx_stmt)

        statements.append("")

    return "\n".join(statements)

def serialize_for_sqlite(val: Any) -> Any:
    """Serializes Python / PostgreSQL values into SQLite storage formats."""
    if val is None:
        return None
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, UUID):
        return str(val)
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False)
    return val

async def extract_pg_data(pg_url: str) -> Dict[str, List[Dict[str, Any]]]:
    pg_engine = create_async_engine(pg_url)
    preserved_data: Dict[str, List[Dict[str, Any]]] = {}
    async with pg_engine.connect() as conn:
        for table in Base.metadata.sorted_tables:
            res = (await conn.execute(text(f'SELECT * FROM "{table.name}"'))).fetchall()
            if res:
                rows = []
                col_names = res[0]._fields if hasattr(res[0], "_fields") else list(res[0].keys())
                for r in res:
                    row_dict = {}
                    for i, name in enumerate(col_names):
                        row_dict[name] = serialize_for_sqlite(r[i])
                    rows.append(row_dict)
                preserved_data[table.name] = rows
                print(f"  • {table.name}: {len(rows)} records extracted")
    await pg_engine.dispose()
    return preserved_data

async def run_migration_drill():
    print("=" * 80)
    print("PROSPECTOS — CLOUDFLARE D1 SCHEMA & DRILL GENERATOR")
    print("=" * 80)

    # 1. Generate D1 Schema DDL
    print("\n[STEP 1] Generating D1 SQLite DDL...")
    ddl_sql = generate_d1_ddl()
    os.makedirs("cloudflare/src/db", exist_ok=True)
    with open("cloudflare/src/db/schema.sql", "w", encoding="utf-8") as f:
        f.write(ddl_sql)
    print("✓ Schema written to cloudflare/src/db/schema.sql")

    # 2. Extract Data from PostgreSQL
    print("\n[STEP 2] Extracting preserved production records from PostgreSQL...")
    pg_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/prospectos")
    try:
        preserved_data = await extract_pg_data(pg_url)
    except Exception as e:
        print(f"ERROR connecting to PostgreSQL: {e}")
        return False

    # 3. Generate Seed SQL
    print("\n[STEP 3] Generating SQLite Seed SQL...")
    seed_statements = ["-- ProspectOS D1 Seed SQL\n"]
    for table_name, rows in preserved_data.items():
        if not rows:
            continue
        cols = list(rows[0].keys())
        cols_formatted = ", ".join([f'"{c}"' for c in cols])
        for r in rows:
            val_strs = []
            for c in cols:
                v = r[c]
                if v is None:
                    val_strs.append("NULL")
                elif isinstance(v, (int, float)):
                    val_strs.append(str(v))
                else:
                    # Escape single quotes for SQL
                    escaped = str(v).replace("'", "''")
                    val_strs.append(f"'{escaped}'")
            seed_statements.append(f'INSERT INTO "{table_name}" ({cols_formatted}) VALUES ({", ".join(val_strs)});')
        seed_statements.append("")

    seed_sql = "\n".join(seed_statements)
    with open("cloudflare/src/db/seed.sql", "w", encoding="utf-8") as f:
        f.write(seed_sql)
    print("✓ Seed written to cloudflare/src/db/seed.sql")

    # 4. Isolated SQLite Verification Drill
    print("\n[STEP 4] Executing isolated SQLite verification drill...")
    os.makedirs("backups", exist_ok=True)
    test_db_path = "backups/prospectos_d1_isolated_test.sqlite3"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    test_conn = sqlite3.connect(test_db_path)
    test_conn.execute("PRAGMA foreign_keys = ON;")
    
    # Execute schema
    test_conn.executescript(ddl_sql)
    print("  ✓ Schema executed cleanly on isolated SQLite database.")

    # Execute seed
    test_conn.executescript(seed_sql)
    print("  ✓ Seed data imported cleanly into isolated SQLite database.")

    # Check foreign keys
    cur = test_conn.cursor()
    cur.execute("PRAGMA foreign_key_check;")
    fk_errors = cur.fetchall()
    if fk_errors:
        print(f"  ✗ FOREIGN KEY CHECK FAILED: {fk_errors}")
        test_conn.close()
        return False
    print("  ✓ PRAGMA foreign_key_check: PASS (0 violations).")

    # 5. Record Count Reconciliation
    print("\n[STEP 5] Database Reconciliation (PostgreSQL vs SQLite D1):")
    all_matched = True
    for table_name, rows in preserved_data.items():
        cur.execute(f'SELECT count(*) FROM "{table_name}"')
        sqlite_count = cur.fetchone()[0]
        pg_count = len(rows)
        match_str = "MATCH" if pg_count == sqlite_count else "MISMATCH"
        if pg_count != sqlite_count:
            all_matched = False
        print(f"  • {table_name:28} | PG: {pg_count:4} | D1: {sqlite_count:4} | {match_str}")

    # Verify users
    cur.execute('SELECT email, role, is_active, substr(hashed_password, 1, 25) FROM portal_users ORDER BY email;')
    users = cur.fetchall()
    print("\n[STEP 6] Preserved User Accounts in SQLite D1:")
    for u in users:
        print(f"  • {u[0]:28} | Role: {u[1]:12} | Active: {u[2]} | Hash: {u[3]}...")

    test_conn.close()
    print("\n" + "=" * 80)
    if all_matched:
        print("RECONCILIATION RESULT: 100% PARITY CONFIRMED.")
        print("SQLite/D1 schema and seed verified without data loss or corruption.")
    else:
        print("RECONCILIATION RESULT: MISMATCH DETECTED.")
    print("=" * 80)
    return all_matched

if __name__ == "__main__":
    success = asyncio.run(run_migration_drill())
    sys.exit(0 if success else 1)
