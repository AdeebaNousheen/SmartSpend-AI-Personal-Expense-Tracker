"""
SmartSpend - Settings Service
Manages application configuration, currency preferences, theme mode, and demo data state.
"""

from typing import Optional
from database.db_manager import DatabaseManager
from database.seed_data import SeedDataManager
import config


class SettingsService:
    """Provides high-level methods to manage user settings and demo state."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self.seed_mgr = SeedDataManager(self.db)

    def get_setting(self, key: str, default: str = "") -> str:
        """Fetch setting value by key."""
        row = self.db.fetch_one("SELECT value FROM settings WHERE key = ?;", (key,))
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Insert or update a setting value."""
        self.db.execute_query("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value;
        """, (key, str(value)))

    def get_currency_symbol(self) -> str:
        """Returns the configured currency symbol (default ₹)."""
        return self.get_setting("currency_symbol", config.DEFAULT_CURRENCY_SYMBOL)

    def get_currency_code(self) -> str:
        """Returns the configured currency code (default INR)."""
        return self.get_setting("currency_code", config.DEFAULT_CURRENCY_CODE)

    def set_currency(self, currency_code: str) -> None:
        """Sets both currency symbol and code."""
        symbol = config.SUPPORTED_CURRENCIES.get(currency_code, config.DEFAULT_CURRENCY_SYMBOL)
        self.set_setting("currency_code", currency_code)
        self.set_setting("currency_symbol", symbol)

    def format_currency(self, amount: float) -> str:
        """
        Formats float into localized currency format, e.g. ₹1,450.50.
        Uses Indian numbering format for INR if symbol is ₹.
        """
        sym = self.get_currency_symbol()
        if sym == "₹":
            # Indian numbering format (lakhs/crores)
            return f"{sym}{self._format_indian_number(amount)}"
        else:
            return f"{sym}{amount:,.2f}"

    def _format_indian_number(self, amount: float) -> str:
        """Formats number according to Indian system: e.g. 1,50,000.00"""
        sign = "-" if amount < 0 else ""
        abs_amt = abs(amount)
        parts = f"{abs_amt:.2f}".split(".")
        int_part = parts[0]
        dec_part = parts[1]

        if len(int_part) <= 3:
            return f"{sign}{int_part}.{dec_part}"

        last_three = int_part[-3:]
        remaining = int_part[:-3]
        
        # Group remaining digits in twos
        groups = []
        while remaining:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]

        formatted = ",".join(groups) + "," + last_three
        return f"{sign}{formatted}.{dec_part}"

    def get_appearance_mode(self) -> str:
        """Returns appearance mode ('dark' or 'light')."""
        return self.get_setting("appearance_mode", config.THEME_CONFIG["appearance_mode"])

    def set_appearance_mode(self, mode: str) -> None:
        """Sets appearance mode."""
        self.set_setting("appearance_mode", mode.lower())

    # Demo data management
    def has_demo_data(self) -> bool:
        """Checks if demo records currently exist in database."""
        return self.seed_mgr.has_demo_data()

    def get_demo_count(self) -> int:
        """Returns number of demo expense records."""
        return self.seed_mgr.count_demo_data()

    def load_demo_data(self) -> int:
        """Populates database with realistic 6-month Indian demo data."""
        return self.seed_mgr.load_demo_data()

    def clear_demo_data(self) -> int:
        """Deletes only demo data; real user records are completely preserved."""
        return self.seed_mgr.clear_demo_data()

    def clear_all_data(self) -> None:
        """Clears all records completely."""
        self.seed_mgr.clear_all_data()
