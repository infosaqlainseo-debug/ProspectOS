"""
Script: scripts/backup_manager.py
Description: CLI utility for PostgreSQL automated backup creation, health monitoring,
and non-destructive isolated restore verification.
"""

import argparse
import json
import sys
from pathlib import Path

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.backup.backup_manager import BackupManager


def main():
    parser = argparse.ArgumentParser(description="ProspectOS PostgreSQL Backup & Recovery Manager")
    parser.add_argument("--backup", action="store_true", help="Create a fresh database backup")
    parser.add_argument("--verify", type=str, default=None, help="Verify and restore backup file to isolated test database")
    parser.add_argument("--health", action="store_true", help="Check backup timeliness and integrity")
    parser.add_argument("--run-all", action="store_true", help="Create backup, verify isolated restore, and report health")
    parser.add_argument("--retention-days", type=int, default=14, help="Retention period in days (default: 14)")

    args = parser.parse_args()
    manager = BackupManager()

    if args.run_all or (not args.backup and not args.verify and not args.health):
        print("=" * 80)
        print("PROSPECTOS: AUTOMATED BACKUP, MONITORING & ISOLATED RESTORE AUDIT")
        print("=" * 80)

        # 1. Create fresh backup
        print("\n[1. Creating Daily Production Backup Archive]")
        entry = manager.create_backup(retention_days=args.retention_days)
        print(f"  ✓ Backup Archive Created: {entry['filename']}")
        print(f"  • Size: {entry['size_mb']} MB ({entry['size_bytes']} bytes)")
        print(f"  • Duration: {entry['duration_seconds']}s")
        print(f"  • SHA-256: {entry['sha256']}")
        print(f"  • Manifest Updated: {manager.manifest_path}")

        # 2. Check Health
        print("\n[2. Backup Health & Schedule Monitoring Check]")
        health = manager.check_health()
        print(f"  • Status: {health['status']}")
        print(f"  • Reason: {health['reason']}")

        # 3. Non-Destructive Isolated Restoration
        print("\n[3. Non-Destructive Isolated Restoration Verification]")
        restore_res = manager.restore_to_isolated_database(entry['filename'])
        print(f"  • Isolated Database: {restore_res['isolated_database']}")
        print(f"  • Production Tables: {restore_res['production_table_count']}")
        print(f"  • Recovered Tables: {restore_res['recovered_table_count']}")
        print(f"  • Tables Matched: {restore_res['tables_matched']}")
        print(f"  • Critical Table Match: {restore_res['all_critical_tables_matched']}")
        print("\n  [Detailed Table Comparison (Production vs Restored Isolated DB)]")
        for tbl, comp in restore_res['table_comparison'].items():
            status_symbol = "✓" if comp['match'] else "✗"
            print(f"    {status_symbol} {tbl:30s}: Primary={comp['production_count']:5d} | Restored={comp['recovered_count']:5d}")

        print(f"\n  Final Restoration Verdict: {restore_res['verification_status']}")
        print("=" * 80)

        if restore_res['verification_status'] != "PASS":
            sys.exit(1)
        return

    if args.backup:
        entry = manager.create_backup(retention_days=args.retention_days)
        print(json.dumps(entry, indent=2))

    if args.health:
        health = manager.check_health()
        print(json.dumps(health, indent=2))

    if args.verify:
        res = manager.restore_to_isolated_database(args.verify)
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
