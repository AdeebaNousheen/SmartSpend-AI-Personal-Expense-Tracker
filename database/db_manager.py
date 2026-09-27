"""
SmartSpend - Database Manager
Handles SQLite database connection, table creation, migrations, and core SQL operations.
"""

import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import config


class DatabaseManager:
    """Manages SQLite database connections and table lifecycle."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_database()

    @contextmanager
    def get_connection(self):
        """Context manager for SQLite connection with dictionary row access."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_database(self) -> None:
        """Create all required tables, indexes, and initial configuration."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Settings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)

            # 2. Categories Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    icon TEXT NOT NULL,
                    color TEXT NOT NULL,
                    is_income INTEGER NOT NULL DEFAULT 0
                );
            """)

            # 3. Expenses Table (Includes is_demo flag for isolation)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    date TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    notes TEXT,
                    is_anomaly INTEGER NOT NULL DEFAULT 0,
                    anomaly_reason TEXT,
                    is_demo INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 4. Budgets Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT NOT NULL,
                    month_year TEXT NOT NULL,
                    limit_amount REAL NOT NULL,
                    is_demo INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(category_name, month_year, is_demo)
                );
            """)

            # 5. Savings Goals Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS savings_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    current_amount REAL NOT NULL DEFAULT 0.0,
                    target_date TEXT,
                    is_demo INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 6. Goal Contributions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goal_contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY(goal_id) REFERENCES savings_goals(id) ON DELETE CASCADE
                );
            """)

            # 7. Recurring Expenses Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recurring_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    next_due_date TEXT NOT NULL,
                    last_logged_date TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    is_demo INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Indexes for high query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_is_demo ON expenses(is_demo);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_month ON budgets(month_year);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_recurring_due ON recurring_expenses(next_due_date);")

            # Seed default settings if missing
            default_settings = [
                ("currency_symbol", config.DEFAULT_CURRENCY_SYMBOL),
                ("currency_code", config.DEFAULT_CURRENCY_CODE),
                ("appearance_mode", config.THEME_CONFIG["appearance_mode"]),
                ("color_theme", config.THEME_CONFIG["color_theme"]),
            ]
            for key, val in default_settings:
                cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", (key, val))

            # Seed default categories if missing
            for cat in config.DEFAULT_CATEGORIES:
                cursor.execute("""
                    INSERT OR IGNORE INTO categories (name, icon, color, is_income)
                    VALUES (?, ?, ?, ?);
                """, (cat["name"], cat["icon"], cat["color"], cat["is_income"]))

    # Generic Query Helpers
    def execute_query(self, query: str, params: Tuple[Any, ...] = ()) -> int:
        """Executes INSERT/UPDATE/DELETE and returns the lastrowid or affected rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid

    def execute_many(self, query: str, params_list: List[Tuple[Any, ...]]) -> int:
        """Executes batch operations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount

    def fetch_all(self, query: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        """Executes SELECT query and returns rows as dictionaries."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def fetch_one(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
        """Executes SELECT query and returns a single row as a dictionary or None."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
