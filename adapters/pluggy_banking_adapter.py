from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from repositories.mongo_cache_repository import MongoCacheRepository


class PluggyBankingAdapter:
    def __init__(
        self,
        settings: PluggySettings | None = None,
        cache_repository: MongoCacheRepository | None = None,
    ):
        self._settings = settings or load_pluggy_settings()
        self._cache = cache_repository

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
        result = fetch_credit_card_info(settings=self._settings)
        if self._cache:
            self._cache.save_bills(result)
        return result

    def fetch_account_balances(self) -> list[dict]:
        result = fetch_account_balances(settings=self._settings)
        if self._cache:
            self._cache.save_balances(result)
        return result

    def fetch_investments(self) -> list[dict]:
        result = fetch_investments(settings=self._settings)
        if self._cache:
            self._cache.save_investments(result)
        return result

    def load_bills_cache(self) -> dict | None:
        if self._cache:
            return self._cache.load_bills()
        return load_bills_cache(cache_file=self._settings.bills_cache_file)

    def load_balances_cache(self) -> dict | None:
        if self._cache:
            return self._cache.load_balances()
        return load_balances_cache(cache_file=self._settings.balances_cache_file)

    def load_investments_cache(self) -> dict | None:
        if self._cache:
            return self._cache.load_investments()
        return load_investments_cache(cache_file=self._settings.investments_cache_file)

    def save_investments_goal(self, goal: float, months: int | None = None) -> None:
        if self._cache:
            self._cache.save_investments_goal(goal, months)
        else:
            save_investments_goal(goal=goal, months=months, cache_file=self._settings.investments_cache_file)

    def get_fontes(self) -> list[str]:
        return self._settings.get_configured_fontes()
