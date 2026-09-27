"""
SmartSpend - Main Entry Point
Launches the AI-Powered Personal Expense Tracker desktop application.
"""

import sys
import argparse
from pathlib import Path

# Ensure application root directory is on Python system path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import config
from database.db_manager import DatabaseManager
from database.seed_data import SeedDataManager
from ui.app import SmartSpendApp


def parse_args():
    parser = argparse.ArgumentParser(description=f"{config.APP_NAME} - {config.APP_SUBTITLE}")
    parser.add_argument("--test-launch", action="store_true", help="Launch and close application after 1 second for CI verification.")
    parser.add_argument("--load-demo", action="store_true", help="Populate database with Indian demo records.")
    parser.add_argument("--clear-demo", action="store_true", help="Delete all demo records while preserving real user expenses.")
    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Initialize SQLite Database
    db = DatabaseManager()

    # Handle CLI flags
    if args.load_demo:
        seed_mgr = SeedDataManager(db)
        count = seed_mgr.load_demo_data()
        print(f"[SmartSpend] Successfully loaded {count} Indian market demo financial records.")
        return

    if args.clear_demo:
        seed_mgr = SeedDataManager(db)
        count = seed_mgr.clear_demo_data()
        print(f"[SmartSpend] Successfully cleared {count} demo records. Real user expenses preserved.")
        return

    # 2. Launch GUI Application
    app = SmartSpendApp(db)

    if args.test_launch:
        # Automated headless/CI verification: check that main window and all views render properly
        print("[SmartSpend] Running GUI smoke test...")
        for view_name in ["Dashboard", "Expenses", "Analytics", "Budgets", "Goals", "Recurring", "AI Insights", "Reports", "Settings"]:
            app.navigate_to(view_name)
            app.update()
            print(f"  [OK] Mounted view: {view_name}")
        print("[SmartSpend] All UI views mounted successfully without errors.")
        app.destroy()
        sys.exit(0)

    # Normal user launch
    app.mainloop()


if __name__ == "__main__":
    main()
