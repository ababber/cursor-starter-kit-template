#!/usr/bin/env python3
"""
Cursor Usage Tracker

Track and analyze Cursor AI usage over time.

Usage:
    python scripts/cursor_usage.py import [file.csv]  # Import CSV (or all in cursor-usage/)
    python scripts/cursor_usage.py report             # Show usage report
    python scripts/cursor_usage.py report --days 7    # Last 7 days
    python scripts/cursor_usage.py report --model     # By model breakdown
    python scripts/cursor_usage.py report --daily     # Daily breakdown
    python scripts/cursor_usage.py report --weekly    # Weekly breakdown
    python scripts/cursor_usage.py quota              # Check quota usage vs limits
    python scripts/cursor_usage.py budget             # Daily budget for rest of cycle
    python scripts/cursor_usage.py alerts             # Exit non-zero on thresholds
    python scripts/cursor_usage.py reminder           # Remind to export yesterday's CSV
    python scripts/cursor_usage.py reminder --once    # Only once per day
    python scripts/cursor_usage.py reminder --date YYYY-DD-MM --no-stamp  # Test run
    python scripts/cursor_usage.py export             # Export all data to CSV
"""

import argparse
import csv
import json
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
USAGE_DIR = REPO_ROOT / "cursor-usage"
DB_PATH = USAGE_DIR / "usage.db"
REMINDER_STATE_PATH = USAGE_DIR / ".reminder_last_date"
DATE_FMT_INPUT = "%Y-%d-%m"
DATE_FMT_DISPLAY = "%Y-%d-%m"


def get_db():
    """Get database connection, creating tables if needed."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("""
        CREATE TABLE IF NOT EXISTS usage_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT UNIQUE,
            kind TEXT,
            model TEXT,
            max_mode TEXT,
            input_cache_write INTEGER,
            input_no_cache INTEGER,
            cache_read INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            cost REAL,
            imported_at TEXT
        )
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_events(timestamp)
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_model ON usage_events(model)
    """)
    db.commit()
    return db


def import_csv(csv_path: Path, db: sqlite3.Connection) -> tuple[int, int]:
    """Import a CSV file into the database. Returns (imported, skipped) counts."""
    imported = 0
    skipped = 0
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                db.execute("""
                    INSERT INTO usage_events (
                        timestamp, kind, model, max_mode,
                        input_cache_write, input_no_cache, cache_read,
                        output_tokens, total_tokens, cost, imported_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['Date'],
                    row['Kind'],
                    row['Model'],
                    row['Max Mode'],
                    int(row['Input (w/ Cache Write)']),
                    int(row['Input (w/o Cache Write)']),
                    int(row['Cache Read']),
                    int(row['Output Tokens']),
                    int(row['Total Tokens']),
                    float(row['Cost']),
                    datetime.now().isoformat()
                ))
                imported += 1
            except sqlite3.IntegrityError:
                # Duplicate timestamp - skip
                skipped += 1
    
    db.commit()
    return imported, skipped


def import_all(specific_file: str = None):
    """Import CSV files from cursor-usage/ directory."""
    db = get_db()
    
    if specific_file:
        files = [Path(specific_file)]
    else:
        files = sorted(USAGE_DIR.glob("*.csv"))
    
    if not files:
        print("No CSV files found in cursor-usage/")
        return
    
    total_imported = 0
    total_skipped = 0
    
    for csv_path in files:
        imported, skipped = import_csv(csv_path, db)
        total_imported += imported
        total_skipped += skipped
        print(f"  {csv_path.name}: {imported} imported, {skipped} skipped (duplicates)")
    
    print(f"\nTotal: {total_imported} imported, {total_skipped} skipped")
    
    # Show total records
    count = db.execute("SELECT COUNT(*) FROM usage_events").fetchone()[0]
    print(f"Database now has {count} records")
    
    db.close()


def report_summary(days: int = None):
    """Generate summary report."""
    db = get_db()
    
    where_clause = ""
    params = []
    if days:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        where_clause = "WHERE timestamp >= ?"
        params = [cutoff]
    
    # Overall stats
    row = db.execute(f"""
        SELECT 
            COUNT(*) as count,
            SUM(cost) as total_cost,
            SUM(total_tokens) as total_tokens,
            AVG(cost) as avg_cost,
            SUM(cache_read) as cache_read,
            SUM(input_cache_write + input_no_cache) as input_tokens
        FROM usage_events {where_clause}
    """, params).fetchone()
    
    period = f"Last {days} days" if days else "All time"
    
    print("=" * 60)
    print(f"CURSOR USAGE REPORT ({period})")
    print("=" * 60)
    print(f"\nTotal Interactions: {row['count']:,}")
    print(f"Total Cost: ${row['total_cost']:.2f}")
    print(f"Total Tokens: {row['total_tokens']:,}")
    print(f"Avg Cost/Interaction: ${row['avg_cost']:.3f}")
    
    if row['cache_read'] and row['input_tokens']:
        cache_ratio = row['cache_read'] / (row['cache_read'] + row['input_tokens']) * 100
        print(f"Cache Hit Ratio: {cache_ratio:.1f}%")
    
    # Errors
    if where_clause:
        error_count = db.execute(f"""
            SELECT COUNT(*) FROM usage_events 
            {where_clause} AND kind LIKE '%Error%'
        """, params).fetchone()[0]
    else:
        error_count = db.execute(
            "SELECT COUNT(*) FROM usage_events WHERE kind LIKE '%Error%'"
        ).fetchone()[0]
    print(f"Errors: {error_count}")
    
    db.close()


def report_by_model(days: int = None):
    """Generate report broken down by model."""
    db = get_db()
    
    where_clause = ""
    params = []
    if days:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        where_clause = "WHERE timestamp >= ?"
        params = [cutoff]
    
    rows = db.execute(f"""
        SELECT 
            model,
            COUNT(*) as count,
            SUM(cost) as total_cost,
            SUM(total_tokens) as total_tokens,
            AVG(cost) as avg_cost
        FROM usage_events {where_clause}
        GROUP BY model
        ORDER BY total_cost DESC
    """, params).fetchall()
    
    period = f"Last {days} days" if days else "All time"
    
    print("\n" + "-" * 60)
    print(f"BY MODEL ({period})")
    print("-" * 60)
    print(f"{'Model':<40} | {'Calls':>5} | {'Cost':>8} | {'Avg':>6}")
    print("-" * 60)
    for row in rows:
        print(f"{row['model']:<40} | {row['count']:>5} | ${row['total_cost']:>6.2f} | ${row['avg_cost']:.3f}")
    
    db.close()


def report_daily(days: int = 30):
    """Generate daily breakdown report."""
    db = get_db()
    
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    
    rows = db.execute("""
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as count,
            SUM(cost) as total_cost,
            SUM(total_tokens) as total_tokens
        FROM usage_events
        WHERE timestamp >= ?
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    """, [cutoff]).fetchall()
    
    print("\n" + "-" * 60)
    print(f"DAILY BREAKDOWN (Last {days} days)")
    print("-" * 60)
    print(f"{'Date':<12} | {'Calls':>5} | {'Cost':>8} | {'Tokens':>12}")
    print("-" * 60)
    
    total_cost = 0
    for row in rows:
        total_cost += row['total_cost']
        print(f"{row['date']:<12} | {row['count']:>5} | ${row['total_cost']:>6.2f} | {row['total_tokens']:>12,}")
    
    print("-" * 60)
    print(f"{'TOTAL':<12} | {sum(r['count'] for r in rows):>5} | ${total_cost:>6.2f}")
    
    db.close()


def report_weekly(weeks: int = 8):
    """Generate weekly breakdown report."""
    db = get_db()
    
    cutoff = (datetime.now() - timedelta(weeks=weeks)).isoformat()
    
    rows = db.execute("""
        SELECT 
            strftime('%Y-W%W', timestamp) as week,
            COUNT(*) as count,
            SUM(cost) as total_cost,
            SUM(total_tokens) as total_tokens
        FROM usage_events
        WHERE timestamp >= ?
        GROUP BY strftime('%Y-W%W', timestamp)
        ORDER BY week DESC
    """, [cutoff]).fetchall()
    
    print("\n" + "-" * 60)
    print(f"WEEKLY BREAKDOWN (Last {weeks} weeks)")
    print("-" * 60)
    print(f"{'Week':<12} | {'Calls':>5} | {'Cost':>8} | {'Tokens':>12}")
    print("-" * 60)
    
    for row in rows:
        print(f"{row['week']:<12} | {row['count']:>5} | ${row['total_cost']:>6.2f} | {row['total_tokens']:>12,}")
    
    db.close()


def get_billing_cycle(now: datetime, billing_day: int) -> tuple[datetime, datetime]:
    """Return billing cycle start/end based on the billing day."""
    if now.day >= billing_day:
        billing_start = now.replace(day=billing_day, hour=0, minute=0, second=0, microsecond=0)
    else:
        if now.month == 1:
            billing_start = datetime(now.year - 1, 12, billing_day, 0, 0, 0)
        else:
            billing_start = datetime(now.year, now.month - 1, billing_day, 0, 0, 0)

    if billing_start.month == 12:
        billing_end = datetime(billing_start.year + 1, 1, billing_day, 0, 0, 0)
    else:
        billing_end = datetime(billing_start.year, billing_start.month + 1, billing_day, 0, 0, 0)

    return billing_start, billing_end


def get_cycle_usage(db: sqlite3.Connection, billing_day: int):
    """Fetch usage rows and metadata for the current billing cycle."""
    now = datetime.now()
    billing_start, billing_end = get_billing_cycle(now, billing_day)

    rows = db.execute("""
        SELECT * FROM usage_events
        WHERE timestamp >= ? AND timestamp < ?
        ORDER BY timestamp DESC
    """, [billing_start.isoformat(), billing_end.isoformat()]).fetchall()

    return now, billing_start, billing_end, rows


def summarize_rows(rows):
    total_cost = sum(float(r['cost']) for r in rows)
    total_requests = len(rows)
    model_costs = defaultdict(lambda: {'cost': 0, 'count': 0})
    for r in rows:
        model_costs[r['model']]['cost'] += float(r['cost'])
        model_costs[r['model']]['count'] += 1
    return total_cost, total_requests, model_costs


def quota_check(billing_day: int = 1, json_output: bool = False, output_path: str = None):
    """Check quota usage against Pro+ plan limits.

    Args:
        billing_day: Day of month when billing cycle resets (default: 1)
        json_output: Print JSON to stdout
        output_path: Write JSON to a file (prints path only)
    """
    db = get_db()
    now, billing_start, billing_end, rows = get_cycle_usage(db, billing_day)

    # Plan limits (Pro+ with $100 on-demand)
    pro_plus_base = 70.00
    pro_plus_on_demand = 100.00
    total_quota = pro_plus_base + pro_plus_on_demand

    total_cost, total_requests, model_costs = summarize_rows(rows)
    days_used = (now - billing_start).days + 1
    days_remaining = (billing_end - now).days
    pct_used = (total_cost / total_quota * 100) if total_quota > 0 else 0
    daily_avg = total_cost / days_used if days_used > 0 else 0
    projected_cycle = total_cost + (daily_avg * days_remaining)

    data = {
        "plan": {
            "name": "Pro+",
            "base_included": pro_plus_base,
            "on_demand": pro_plus_on_demand,
            "total_quota": total_quota,
        },
        "billing_cycle": {
            "start": billing_start.isoformat(),
            "end": billing_end.isoformat(),
            "days_used": days_used,
            "days_remaining": days_remaining,
        },
        "usage": {
            "total_cost": round(total_cost, 2),
            "total_requests": total_requests,
            "pct_used": round(pct_used, 1),
            "remaining_quota": round(max(0, total_quota - total_cost), 2),
            "daily_avg": round(daily_avg, 2),
            "projected_cycle": round(projected_cycle, 2),
        },
        "models": [
            {
                "model": model,
                "cost": round(stats["cost"], 2),
                "count": stats["count"],
                "pct": round((stats["cost"] / total_cost * 100) if total_cost > 0 else 0, 1),
            }
            for model, stats in sorted(model_costs.items(), key=lambda x: -x[1]["cost"])
        ],
    }

    if output_path:
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote quota JSON to {output_path}")
        db.close()
        return

    if json_output:
        print(json.dumps(data, indent=2))
        db.close()
        return

    print("=" * 70)
    print("CURSOR PRO+ QUOTA STATUS")
    print("=" * 70)
    print("\nPlan: Pro+ ($60/mo) + $100 On-Demand Credits")
    print(f"Total Quota: ${total_quota:.2f}/month")
    print(f"  - Base included: ${pro_plus_base:.2f}")
    print(f"  - On-demand: ${pro_plus_on_demand:.2f}")

    print(f"\n{'─' * 70}")
    print("BILLING CYCLE")
    print(f"{'─' * 70}")
    print(f"Cycle: {billing_start.strftime('%Y-%m-%d')} to {billing_end.strftime('%Y-%m-%d')}")
    print(f"Days used: {days_used}")
    print(f"Days remaining: {days_remaining}")

    print(f"\n{'─' * 70}")
    print("USAGE THIS CYCLE")
    print(f"{'─' * 70}")
    print(f"Total Requests: {total_requests:,}")
    print(f"Total Cost: ${total_cost:.2f}")
    print(f"Remaining Quota: ${max(0, total_quota - total_cost):.2f}")

    bar_length = 50
    filled = int(min(pct_used, 100) / 2)
    print(f"\n{'█' * filled}{'░' * (bar_length - filled)} {pct_used:.1f}%")

    if total_cost > total_quota:
        overage = total_cost - total_quota
        print(f"\n⚠️  OVER QUOTA by ${overage:.2f}")
        print("    You'll be charged for overage or need to add more credits")
    elif pct_used > 80:
        print(f"\n⚠️  WARNING: {pct_used:.1f}% used - approaching limit")

    print(f"\n{'─' * 70}")
    print("PROJECTIONS")
    print(f"{'─' * 70}")
    print(f"Daily average: ${daily_avg:.2f}")
    print(f"Projected cycle total: ${projected_cycle:.2f}")

    if projected_cycle > total_quota:
        overage_proj = projected_cycle - total_quota
        print(f"\n⚠️  At current pace, you'll exceed quota by ${overage_proj:.2f}")
        print("    Consider reducing usage or adding more on-demand credits")
    elif projected_cycle > total_quota * 0.9:
        print(f"\n⚠️  At current pace, you'll use ~{projected_cycle/total_quota*100:.1f}% of quota")

    print(f"\n{'─' * 70}")
    print("COST BY MODEL (this cycle)")
    print(f"{'─' * 70}")

    print(f"{'Model':<45} | {'Cost':>8} | {'Calls':>6} | {'%':>5}")
    print(f"{'─' * 70}")
    for model, stats in sorted(model_costs.items(), key=lambda x: -x[1]['cost']):
        pct = (stats['cost'] / total_cost * 100) if total_cost > 0 else 0
        print(f"{model:<45} | ${stats['cost']:>6.2f} | {stats['count']:>6} | {pct:>4.1f}%")

    if total_cost > 0:
        top_model = max(model_costs.items(), key=lambda x: x[1]['cost'])
        if top_model[1]['cost'] / total_cost > 0.5:
            print(f"\n{'─' * 70}")
            print("OPTIMIZATION TIP")
            print(f"{'─' * 70}")
            print(f"'{top_model[0]}' accounts for {top_model[1]['cost']/total_cost*100:.1f}% of spend")
            print("Consider using 'auto' mode when possible (unlimited for individuals)")

    db.close()


def budget_check(limit: float = 170.0, billing_day: int = 1, json_output: bool = False, output_path: str = None):
    """Calculate daily budget for the remainder of the cycle."""
    db = get_db()
    now, billing_start, billing_end, rows = get_cycle_usage(db, billing_day)
    total_cost, _, _ = summarize_rows(rows)

    days_remaining = (billing_end - now).days
    remaining = max(0, limit - total_cost)
    daily_budget = (remaining / days_remaining) if days_remaining > 0 else 0

    data = {
        "limit": round(limit, 2),
        "total_cost": round(total_cost, 2),
        "remaining": round(remaining, 2),
        "days_remaining": days_remaining,
        "daily_budget": round(daily_budget, 2),
        "billing_cycle": {
            "start": billing_start.isoformat(),
            "end": billing_end.isoformat(),
        },
    }

    if output_path:
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote budget JSON to {output_path}")
        db.close()
        return

    if json_output:
        print(json.dumps(data, indent=2))
        db.close()
        return

    print("=" * 70)
    print("CURSOR BUDGET CHECK")
    print("=" * 70)
    print(f"\nLimit: ${limit:.2f}")
    print(f"Spent: ${total_cost:.2f}")
    print(f"Remaining: ${remaining:.2f}")
    print(f"Days remaining: {days_remaining}")
    print(f"Safe daily budget: ${daily_budget:.2f}")

    db.close()


def alerts_check(
    limit: float = 170.0,
    warn: float = 80.0,
    fail: float = 100.0,
    billing_day: int = 1,
    json_output: bool = False,
    output_path: str = None,
):
    """Return non-zero exit code if usage crosses thresholds."""
    db = get_db()
    now, billing_start, billing_end, rows = get_cycle_usage(db, billing_day)
    total_cost, _, _ = summarize_rows(rows)
    pct_used = (total_cost / limit * 100) if limit > 0 else 0

    if pct_used >= fail:
        status = "fail"
        exit_code = 2
    elif pct_used >= warn:
        status = "warn"
        exit_code = 1
    else:
        status = "ok"
        exit_code = 0

    data = {
        "status": status,
        "exit_code": exit_code,
        "pct_used": round(pct_used, 1),
        "total_cost": round(total_cost, 2),
        "limit": round(limit, 2),
        "thresholds": {"warn": warn, "fail": fail},
        "billing_cycle": {
            "start": billing_start.isoformat(),
            "end": billing_end.isoformat(),
        },
    }

    if output_path:
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote alerts JSON to {output_path}")
        db.close()
        return exit_code

    if json_output:
        print(json.dumps(data, indent=2))
        db.close()
        return exit_code

    print(f"Status: {status.upper()} ({pct_used:.1f}% used of ${limit:.2f})")
    db.close()
    return exit_code


def export_all():
    """Export all data to a CSV file."""
    db = get_db()
    
    output_path = USAGE_DIR / f"export_{datetime.now().strftime('%Y-%m-%d')}.csv"
    
    rows = db.execute("""
        SELECT timestamp, kind, model, max_mode,
               input_cache_write, input_no_cache, cache_read,
               output_tokens, total_tokens, cost
        FROM usage_events
        ORDER BY timestamp DESC
    """).fetchall()
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Date', 'Kind', 'Model', 'Max Mode',
            'Input (w/ Cache Write)', 'Input (w/o Cache Write)', 'Cache Read',
            'Output Tokens', 'Total Tokens', 'Cost'
        ])
        for row in rows:
            writer.writerow(list(row))
    
    print(f"Exported {len(rows)} records to {output_path}")
    db.close()


def reminder_check(
    once_per_day: bool = False,
    today_override: str = None,
    no_stamp: bool = False,
):
    """Remind to export yesterday's usage CSV if missing."""
    if today_override:
        try:
            today = datetime.strptime(today_override, DATE_FMT_INPUT).date()
        except ValueError:
            print("Invalid --date. Use YYYY-DD-MM.")
            return
    else:
        today = datetime.now().date()

    if once_per_day and not no_stamp and REMINDER_STATE_PATH.exists():
        last = REMINDER_STATE_PATH.read_text().strip()
        if last == today.isoformat():
            return

    yesterday = today - timedelta(days=1)
    pattern = re.compile(r"usage-events-(\d{4}-\d{2}-\d{2})")
    csv_dates = set()

    for csv_path in USAGE_DIR.glob("usage-events-*.csv"):
        match = pattern.search(csv_path.name)
        if match:
            try:
                csv_dates.add(datetime.strptime(match.group(1), "%Y-%m-%d").date())
            except ValueError:
                continue

    if not csv_dates:
        print("No CSV exports found in cursor-usage/.")
        print(f"Please export yesterday's usage CSV: {yesterday.strftime(DATE_FMT_DISPLAY)}")
        if once_per_day and not no_stamp:
            REMINDER_STATE_PATH.write_text(today.isoformat())
        return

    latest_date = max(csv_dates)
    if yesterday in csv_dates:
        print(f"OK: Found CSV for yesterday ({yesterday.strftime(DATE_FMT_DISPLAY)}).")
    else:
        print(f"Missing CSV for yesterday: {yesterday.strftime(DATE_FMT_DISPLAY)}")
        print(f"Latest CSV date: {latest_date.strftime(DATE_FMT_DISPLAY)}")
        print("Please export yesterday's usage CSV from Cursor.")
    if once_per_day and not no_stamp:
        REMINDER_STATE_PATH.write_text(today.isoformat())


def main():
    parser = argparse.ArgumentParser(description="Cursor Usage Tracker")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import CSV files')
    import_parser.add_argument('file', nargs='?', help='Specific CSV file to import')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate usage report')
    report_parser.add_argument('--days', type=int, help='Limit to last N days')
    report_parser.add_argument('--model', action='store_true', help='Show by-model breakdown')
    report_parser.add_argument('--daily', action='store_true', help='Show daily breakdown')
    report_parser.add_argument('--weekly', action='store_true', help='Show weekly breakdown')
    
    # Quota command
    quota_parser = subparsers.add_parser('quota', help='Check quota usage vs plan limits')
    quota_parser.add_argument('--billing-day', type=int, default=1, 
                             help='Day of month when billing cycle resets (default: 1)')
    quota_parser.add_argument('--json', action='store_true', help='Print JSON to stdout')
    quota_parser.add_argument('--out', help='Write JSON output to a file')

    # Budget command
    budget_parser = subparsers.add_parser('budget', help='Daily budget for the rest of cycle')
    budget_parser.add_argument('--limit', type=float, default=170.0,
                               help='Monthly quota limit (default: 170)')
    budget_parser.add_argument('--billing-day', type=int, default=1,
                               help='Day of month when billing cycle resets (default: 1)')
    budget_parser.add_argument('--json', action='store_true', help='Print JSON to stdout')
    budget_parser.add_argument('--out', help='Write JSON output to a file')

    # Alerts command
    alerts_parser = subparsers.add_parser('alerts', help='Exit non-zero on thresholds')
    alerts_parser.add_argument('--limit', type=float, default=170.0,
                               help='Monthly quota limit (default: 170)')
    alerts_parser.add_argument('--warn', type=float, default=80.0,
                               help='Warn threshold percent (default: 80)')
    alerts_parser.add_argument('--fail', type=float, default=100.0,
                               help='Fail threshold percent (default: 100)')
    alerts_parser.add_argument('--billing-day', type=int, default=1,
                               help='Day of month when billing cycle resets (default: 1)')
    alerts_parser.add_argument('--json', action='store_true', help='Print JSON to stdout')
    alerts_parser.add_argument('--out', help='Write JSON output to a file')
    
    # Reminder command
    reminder_parser = subparsers.add_parser('reminder', help="Remind to export yesterday's CSV")
    reminder_parser.add_argument('--once', action='store_true', help='Only once per day')
    reminder_parser.add_argument('--date', help='Override today (YYYY-DD-MM) for testing')
    reminder_parser.add_argument('--no-stamp', action='store_true',
                                 help='Do not write reminder stamp (testing)')

    # Export command
    subparsers.add_parser('export', help='Export all data to CSV')
    
    args = parser.parse_args()
    
    # Ensure usage directory exists
    USAGE_DIR.mkdir(exist_ok=True)
    
    if args.command == 'import':
        import_all(args.file)
    elif args.command == 'report':
        report_summary(args.days)
        if args.model:
            report_by_model(args.days)
        if args.daily:
            report_daily(args.days or 30)
        if args.weekly:
            report_weekly()
        if not args.model and not args.daily and not args.weekly:
            # Default: show model breakdown
            report_by_model(args.days)
    elif args.command == 'quota':
        quota_check(args.billing_day, args.json, args.out)
    elif args.command == 'budget':
        budget_check(args.limit, args.billing_day, args.json, args.out)
    elif args.command == 'alerts':
        exit_code = alerts_check(
            args.limit, args.warn, args.fail, args.billing_day, args.json, args.out
        )
        sys.exit(exit_code)
    elif args.command == 'reminder':
        reminder_check(args.once, args.date, args.no_stamp)
    elif args.command == 'export':
        export_all()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
