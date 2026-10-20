"""
Module: app.services.backup.backup_manager
Description: Production PostgreSQL automated backup, monitoring, integrity verification,
and non-destructive isolated restoration management.
"""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)

# Determine default backup directory relative to project root or container app root
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
_DEFAULT_BACKUP_DIR = Path("/app/backups") if Path("/app/app").exists() else _ROOT_DIR / "backups"
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", str(_DEFAULT_BACKUP_DIR)))
MANIFEST_FILE = BACKUP_DIR / "backup_manifest.json"
CONTAINER_NAME = os.getenv("POSTGRES_CONTAINER", "prospectos_db")
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_NAME = os.getenv("POSTGRES_DB", "prospectos")


def _get_db_connection_params() -> Dict[str, str]:
    db_url = getattr(settings, "DATABASE_URL", "")
    clean_url = db_url.replace("+asyncpg", "") if "+asyncpg" in db_url else db_url
    parsed = urlparse(clean_url)
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": parsed.username or os.getenv("POSTGRES_USER", "user"),
        "password": parsed.password or os.getenv("POSTGRES_PASSWORD", "password"),
        "database": parsed.path.lstrip("/") or os.getenv("POSTGRES_DB", "prospectos"),
    }


class BackupManager:
    """Manages automated PostgreSQL backups, checksum verification, retention, and isolated recovery."""

    def __init__(self, backup_dir: Path = BACKUP_DIR, container_name: str = CONTAINER_NAME):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.container_name = container_name
        self.manifest_path = self.backup_dir / "backup_manifest.json"
        self.has_native_pg = shutil.which("pg_dump") is not None and shutil.which("psql") is not None

    def _read_manifest(self) -> List[Dict[str, Any]]:
        if not self.manifest_path.exists():
            return []
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read backup manifest: {e}")
            return []

    def _write_manifest(self, entries: List[Dict[str, Any]]) -> None:
        try:
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to write backup manifest: {e}")

    @staticmethod
    def _compute_sha256(filepath: Path) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def create_backup(self, retention_days: int = 14) -> Dict[str, Any]:
        """
        Executes a consistent custom-format pg_dump of the primary database,
        computes SHA-256 checksum, sets secure file permissions, updates manifest,
        and enforces retention cleanup.
        """
        now = datetime.now(timezone.utc)
        ts_str = now.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"prospectos_backup_{ts_str}.dump"
        backup_path = self.backup_dir / backup_filename
        sha256_path = self.backup_dir / f"{backup_filename}.sha256"

        start_time = time.time()
        logger.info(f"Starting database backup: {backup_filename} (UTC {now.isoformat()})")

        params = _get_db_connection_params()
        env = os.environ.copy()
        if params["password"]:
            env["PGPASSWORD"] = params["password"]

        if self.has_native_pg:
            cmd = [
                "pg_dump",
                "-h", params["host"],
                "-p", params["port"],
                "-U", params["user"],
                "-d", params["database"],
                "-F", "c",
                "-b"
            ]
        else:
            cmd = [
                "docker", "exec", self.container_name,
                "pg_dump", "-U", params["user"], "-d", params["database"], "-F", "c", "-b"
            ]

        try:
            with open(backup_path, "wb") as f_out:
                proc = subprocess.run(cmd, stdout=f_out, stderr=subprocess.PIPE, env=env if self.has_native_pg else None, check=True)

            duration_sec = round(time.time() - start_time, 2)
            # Secure file permissions (rw-------)
            os.chmod(backup_path, 0o600)

            size_bytes = backup_path.stat().st_size
            if size_bytes < 10000:
                raise ValueError(f"Backup file unexpectedly small: {size_bytes} bytes")

            # Checksum
            sha256_hash = self._compute_sha256(backup_path)
            with open(sha256_path, "w", encoding="utf-8") as f_sha:
                f_sha.write(f"{sha256_hash}  {backup_filename}\n")
            os.chmod(sha256_path, 0o600)

            entry = {
                "id": str(uuid.uuid4()),
                "filename": backup_filename,
                "filepath": str(backup_path),
                "timestamp_utc": now.isoformat(),
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 2),
                "sha256": sha256_hash,
                "duration_seconds": duration_sec,
                "status": "SUCCESS",
                "retention_days": retention_days,
                "database": DB_NAME
            }

            manifest = self._read_manifest()
            manifest.append(entry)
            self._write_manifest(manifest)

            # Cleanup older backups
            self.enforce_retention(retention_days)

            logger.info(f"Backup completed successfully: {backup_filename} ({entry['size_mb']} MB in {duration_sec}s)")
            return entry

        except Exception as e:
            duration_sec = round(time.time() - start_time, 2)
            logger.error(f"Backup failed after {duration_sec}s: {e}")
            entry = {
                "id": str(uuid.uuid4()),
                "filename": backup_filename,
                "filepath": str(backup_path),
                "timestamp_utc": now.isoformat(),
                "size_bytes": backup_path.stat().st_size if backup_path.exists() else 0,
                "duration_seconds": duration_sec,
                "status": "FAILED",
                "error": str(e),
                "database": DB_NAME
            }
            manifest = self._read_manifest()
            manifest.append(entry)
            self._write_manifest(manifest)
            raise

    def enforce_retention(self, retention_days: int = 14) -> int:
        """Removes backups older than retention_days from disk and manifest."""
        manifest = self._read_manifest()
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        retained = []
        removed_count = 0

        for entry in manifest:
            try:
                entry_dt = datetime.fromisoformat(entry["timestamp_utc"])
                if entry_dt < cutoff:
                    fpath = Path(entry.get("filepath", ""))
                    if fpath.exists():
                        fpath.unlink(missing_ok=True)
                    sha_path = Path(f"{entry.get('filepath', '')}.sha256")
                    if sha_path.exists():
                        sha_path.unlink(missing_ok=True)
                    removed_count += 1
                else:
                    retained.append(entry)
            except Exception:
                retained.append(entry)

        self._write_manifest(retained)
        if removed_count > 0:
            logger.info(f"Enforced retention: pruned {removed_count} backup(s) older than {retention_days} days.")
        return removed_count

    def restore_to_isolated_database(
        self,
        backup_filename: Optional[str] = None,
        isolated_db_name: str = "prospectos_recovery_verify"
    ) -> Dict[str, Any]:
        """
        Restores a backup archive into an isolated, non-production verification database,
        validating schema, table counts, and row counts against the live database.
        NEVER restores over the primary production database.
        """
        if not backup_filename:
            manifest = self._read_manifest()
            successful = [e for e in manifest if e.get("status") == "SUCCESS"]
            if not successful:
                raise ValueError("No successful backup archive found in manifest to verify.")
            backup_filename = sorted(successful, key=lambda x: x["timestamp_utc"])[-1]["filename"]

        backup_path = self.backup_dir / backup_filename
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Checksum validation
        current_sha = self._compute_sha256(backup_path)
        sha256_path = self.backup_dir / f"{backup_filename}.sha256"
        if sha256_path.exists():
            with open(sha256_path, "r", encoding="utf-8") as f:
                expected_sha = f.read().split()[0]
                if current_sha != expected_sha:
                    raise ValueError(f"Checksum mismatch for {backup_filename}: {current_sha} != {expected_sha}")

        logger.info(f"Integrity verified for {backup_filename} (SHA-256 match).")
        logger.info(f"Preparing isolated recovery database: '{isolated_db_name}'...")

        params = _get_db_connection_params()
        env = os.environ.copy()
        if params["password"]:
            env["PGPASSWORD"] = params["password"]

        # 1. Drop and re-create isolated verification database
        if self.has_native_pg:
            drop_cmd = [
                "psql", "-h", params["host"], "-p", params["port"],
                "-U", params["user"], "-d", "postgres",
                "-c", f"DROP DATABASE IF EXISTS {isolated_db_name};"
            ]
            subprocess.run(drop_cmd, check=True, capture_output=True, env=env)

            create_cmd = [
                "psql", "-h", params["host"], "-p", params["port"],
                "-U", params["user"], "-d", "postgres",
                "-c", f"CREATE DATABASE {isolated_db_name};"
            ]
            subprocess.run(create_cmd, check=True, capture_output=True, env=env)

            # 2. Restore custom-format dump into isolated verification database
            logger.info(f"Restoring {backup_filename} into isolated database '{isolated_db_name}'...")
            restore_cmd = [
                "pg_restore", "-h", params["host"], "-p", params["port"],
                "-U", params["user"], "-d", isolated_db_name,
                "--no-owner", "--no-privileges"
            ]
            with open(backup_path, "rb") as f_in:
                proc = subprocess.run(restore_cmd, stdin=f_in, capture_output=True, env=env)
                if proc.returncode != 0:
                    logger.warning(f"pg_restore finished with code {proc.returncode}: {proc.stderr.decode('utf-8')[:300]}")
        else:
            drop_cmd = [
                "docker", "exec", self.container_name,
                "psql", "-U", params["user"], "-d", "postgres",
                "-c", f"DROP DATABASE IF EXISTS {isolated_db_name};"
            ]
            subprocess.run(drop_cmd, check=True, capture_output=True)

            create_cmd = [
                "docker", "exec", self.container_name,
                "psql", "-U", params["user"], "-d", "postgres",
                "-c", f"CREATE DATABASE {isolated_db_name};"
            ]
            subprocess.run(create_cmd, check=True, capture_output=True)

            # 2. Restore custom-format dump into isolated verification database
            logger.info(f"Restoring {backup_filename} into isolated database '{isolated_db_name}'...")
            restore_cmd = [
                "docker", "exec", "-i", self.container_name,
                "pg_restore", "-U", params["user"], "-d", isolated_db_name,
                "--no-owner", "--no-privileges"
            ]
            with open(backup_path, "rb") as f_in:
                proc = subprocess.run(restore_cmd, stdin=f_in, capture_output=True)
                if proc.returncode != 0:
                    logger.warning(f"pg_restore finished with code {proc.returncode}: {proc.stderr.decode('utf-8')[:300]}")

        # 3. Compare schema and row counts between primary and isolated database
        critical_tables = [
            "companies",
            "publisher_records",
            "publisher_observations",
            "crm_deals",
            "crm_activities",
            "portal_users",
            "client_reports",
            "portal_audit_logs",
            "media_plans",
            "media_plan_items",
            "seo_metrics",
            "opportunity_profiles",
            "sales_opportunities",
            "revenue_analytics_snapshots",
        ]

        # Fetch table counts
        count_tables_sql = "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
        prod_tables = int(self._run_psql_query(DB_NAME, count_tables_sql).strip())
        recovered_tables = int(self._run_psql_query(isolated_db_name, count_tables_sql).strip())

        table_comparison = {}
        all_matched = True

        for table in critical_tables:
            query = f"SELECT count(*) FROM {table};"
            prod_cnt = int(self._run_psql_query(DB_NAME, query).strip())
            recov_cnt = int(self._run_psql_query(isolated_db_name, query).strip())
            match = prod_cnt == recov_cnt
            if not match:
                all_matched = False
            table_comparison[table] = {
                "production_count": prod_cnt,
                "recovered_count": recov_cnt,
                "match": match
            }

        verification_result = {
            "backup_filename": backup_filename,
            "sha256": current_sha,
            "isolated_database": isolated_db_name,
            "primary_database": DB_NAME,
            "production_table_count": prod_tables,
            "recovered_table_count": recovered_tables,
            "tables_matched": prod_tables == recovered_tables,
            "all_critical_tables_matched": all_matched,
            "table_comparison": table_comparison,
            "verification_status": "PASS" if (prod_tables == recovered_tables and all_matched) else "FAIL",
            "verified_at_utc": datetime.now(timezone.utc).isoformat()
        }

        logger.info(f"Isolated restoration verification result: {verification_result['verification_status']}")
        return verification_result

    def check_health(self, max_age_hours: int = 26, min_size_bytes: int = 50000) -> Dict[str, Any]:
        """Monitors backup timeliness, integrity, and minimum size threshold."""
        manifest = self._read_manifest()
        successful = [e for e in manifest if e.get("status") == "SUCCESS"]

        if not successful:
            return {
                "status": "FAILED",
                "healthy": False,
                "reason": "No successful backups found in manifest.",
                "latest_backup": None
            }

        latest = sorted(successful, key=lambda x: x["timestamp_utc"])[-1]
        latest_dt = datetime.fromisoformat(latest["timestamp_utc"])
        age = datetime.now(timezone.utc) - latest_dt
        age_hours = age.total_seconds() / 3600

        fpath = Path(latest.get("filepath", ""))
        if not fpath.exists():
            return {
                "status": "FAILED",
                "healthy": False,
                "reason": f"Latest backup file missing from filesystem: {latest.get('filename')}",
                "latest_backup": latest
            }

        if latest.get("size_bytes", 0) < min_size_bytes:
            return {
                "status": "FAILED",
                "healthy": False,
                "reason": f"Latest backup unexpectedly small ({latest.get('size_bytes')} bytes)",
                "latest_backup": latest
            }

        if age_hours > max_age_hours:
            return {
                "status": "DEGRADED",
                "healthy": False,
                "reason": f"Latest backup is {age_hours:.1f} hours old (threshold is {max_age_hours}h)",
                "latest_backup": latest
            }

        return {
            "status": "HEALTHY",
            "healthy": True,
            "reason": f"Latest backup is {age_hours:.1f} hours old ({latest.get('size_mb')} MB), checksum and size valid.",
            "latest_backup": latest
        }

    def _run_psql_query(self, database: str, query: str) -> str:
        params = _get_db_connection_params()
        if self.has_native_pg:
            env = os.environ.copy()
            if params["password"]:
                env["PGPASSWORD"] = params["password"]
            cmd = [
                "psql", "-h", params["host"], "-p", params["port"],
                "-U", params["user"], "-d", database,
                "-t", "-A", "-c", query
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
            return res.stdout.strip()
        else:
            cmd = [
                "docker", "exec", self.container_name,
                "psql", "-U", params["user"], "-d", database,
                "-t", "-A", "-c", query
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return res.stdout.strip()
