from collections.abc import Callable

from core.settings import PluggySettings, load_pluggy_settings
from pluggy_integration import (
    fetch_account_balances,
    fetch_credit_card_info,
    fetch_investments,
    load_balances_cache,
    load_bills_cache,
    load_investments_cache,
    save_investments_goal,
    sync_all,
)


class PluggyBankingAdapter:
    def __init__(self, settings: PluggySettings | None = None):
        self._settings = settings or load_pluggy_settings()

    def sync_all(
        self,
        date_from: str,
        date_to: str,
        categorize: Callable[[str], str | None],
    ) -> list[dict]:
        return sync_all(
            date_from=date_from,
            date_to=date_to,
            categorize=categorize,
            settings=self._settings,
        )

    def fetch_credit_card_info(self) -> list[dict]:
        return fetch_credit_card_info(settings=self._settings)

    def fetch_account_balances(self) -> list[dict]:
        return fetch_account_balances(settings=self._settings)

    def fetch_investments(self) -> list[dict]:
        return fetch_investments(settings=self._settings)

    def load_bills_cache(self) -> dict | None:
        return load_bills_cache(cache_file=self._settings.bills_cache_file)

    def load_balances_cache(self) -> dict | None:
        return load_balances_cache(cache_file=self._settings.balances_cache_file)

    def load_investments_cache(self) -> dict | None:
        return load_investments_cache(cache_file=self._settings.investments_cache_file)

    def save_investments_goal(self, goal: float, months: int | None = None) -> None:
        save_investments_goal(goal=goal, months=months, cache_file=self._settings.investments_cache_file)

    def get_fontes(self) -> list[str]:
        return self._settings.get_configured_fontes()
