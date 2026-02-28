import json
import os

import streamlit as st

from adapters import AccountsFileAdapter, PluggyBankingAdapter, RulesDataAdapter, TransactionsDataAdapter
from core.constants import (
    ACCOUNTS_FILE,
    BALANCES_CACHE_FILE,
    BILLS_CACHE_FILE,
    DATA_FILE,
    INVESTMENTS_CACHE_FILE,
    RULES_FILE,
)
from core.settings import load_mongo_settings
from ports.accounts_port import AccountsPort
from repositories import ConfigRepository, TransactionsRepository
from services import BillsService, FinanceService


def _seed_mongo_config_from_json(mongo_config_repo, json_path: str) -> None:
    """Seed MongoDB config from local JSON file, merging any missing sections."""
    if not os.path.exists(json_path):
        return

    file_config_repo = ConfigRepository(json_path)
    file_config = file_config_repo.load_config()
    file_categorias = file_config.get("categorias", {})
    file_regras = file_config.get("regras", {})
    if not file_categorias and not file_regras:
        return

    current = mongo_config_repo.load_config()
    mongo_categorias = current.get("categorias", {})
    mongo_regras = current.get("regras", {})

    needs_update = False
    if file_categorias and not mongo_categorias:
        current["categorias"] = file_categorias
        needs_update = True
    if file_regras and not mongo_regras:
        current["regras"] = file_regras
        needs_update = True

    if needs_update:
        mongo_config_repo.save_config(current)


def _seed_mongo_caches_from_json(cache_repository) -> None:
    """Seed MongoDB caches from local JSON files if MongoDB caches are empty."""
    if cache_repository.load_bills() is None and os.path.exists(BILLS_CACHE_FILE):
        with open(BILLS_CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        cache_repository.save_bills(data.get("cards", []))

    if cache_repository.load_balances() is None and os.path.exists(BALANCES_CACHE_FILE):
        with open(BALANCES_CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        cache_repository.save_balances(data.get("balances", []))

    if cache_repository.load_investments() is None and os.path.exists(INVESTMENTS_CACHE_FILE):
        with open(INVESTMENTS_CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        cache_repository.save_investments(
            investments=data.get("investments", []),
            goal=data.get("goal"),
            goal_months=data.get("goal_months"),
        )


def _seed_mongo_accounts(accounts_adapter, json_path: str) -> None:
    """Seed MongoDB accounts from local JSON file if MongoDB has no accounts."""
    if accounts_adapter.list_accounts():
        return

    if not os.path.exists(json_path):
        return

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    for conta in data.get("contas", []):
        item_id = conta.get("pluggy_item_id", "").strip()
        nome = conta.get("nome", "").strip()
        if item_id and nome:
            accounts_adapter.add_account(item_id, nome)


def build_services() -> tuple[FinanceService, BillsService, AccountsPort]:
    mongo_settings = load_mongo_settings()

    if mongo_settings.is_configured:
        from pymongo import MongoClient

        from adapters.accounts_mongo_adapter import AccountsMongoAdapter
        from repositories.mongo_cache_repository import MongoCacheRepository
        from repositories.mongo_config_repository import MongoConfigRepository
        from repositories.mongo_transactions_repository import MongoTransactionsRepository

        client = MongoClient(mongo_settings.uri)
        db = client[mongo_settings.database]

        config_repository = MongoConfigRepository(db)
        _seed_mongo_config_from_json(config_repository, RULES_FILE)
        transactions_repository = MongoTransactionsRepository(db, config_repository)

        cache_repository = MongoCacheRepository(db)
        _seed_mongo_caches_from_json(cache_repository)

        accounts_adapter: AccountsPort = AccountsMongoAdapter(db)
        _seed_mongo_accounts(accounts_adapter, ACCOUNTS_FILE)

        banking_adapter = PluggyBankingAdapter(cache_repository=cache_repository)
    else:
        config_repository = ConfigRepository(RULES_FILE)
        transactions_repository = TransactionsRepository(DATA_FILE, config_repository)
        accounts_adapter = AccountsFileAdapter()
        banking_adapter = PluggyBankingAdapter()

    rules_adapter = RulesDataAdapter(
        config_repository=config_repository,
        transactions_repository=transactions_repository,
    )
    transactions_adapter = TransactionsDataAdapter(
        config_repository=config_repository,
        transactions_repository=transactions_repository,
    )
    return (
        FinanceService(
            transactions=transactions_adapter,
            rules=rules_adapter,
            banking=banking_adapter,
        ),
        BillsService(banking=banking_adapter),
        accounts_adapter,
    )


def initialize_session_dataframe(finance_service: FinanceService):
    if "df" not in st.session_state:
        st.session_state.df = finance_service.load_dataframe()
    return st.session_state.df
