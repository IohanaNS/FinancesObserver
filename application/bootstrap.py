import streamlit as st

from adapters import AccountsFileAdapter, PluggyBankingAdapter, RulesDataAdapter, TransactionsDataAdapter
from core.constants import DATA_FILE, RULES_FILE
from core.settings import load_mongo_settings
from repositories import ConfigRepository, TransactionsRepository
from services import BillsService, FinanceService


def _build_repositories() -> tuple:
    """Build config and transactions repositories based on MONGO_URI availability."""
    mongo_settings = load_mongo_settings()
    if mongo_settings.is_configured:
        from pymongo import MongoClient

        from repositories.mongo_config_repository import MongoConfigRepository
        from repositories.mongo_transactions_repository import MongoTransactionsRepository

        client = MongoClient(mongo_settings.uri)
        db = client[mongo_settings.database]
        config_repository = MongoConfigRepository(db)
        transactions_repository = MongoTransactionsRepository(db, config_repository)
    else:
        config_repository = ConfigRepository(RULES_FILE)
        transactions_repository = TransactionsRepository(DATA_FILE, config_repository)
    return config_repository, transactions_repository


def build_services() -> tuple[FinanceService, BillsService, AccountsFileAdapter]:
    banking_adapter = PluggyBankingAdapter()
    accounts_adapter = AccountsFileAdapter()
    config_repository, transactions_repository = _build_repositories()
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
