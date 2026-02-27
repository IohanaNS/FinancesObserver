import streamlit as st

from adapters import PluggyBankingAdapter, RulesDataAdapter, TransactionsDataAdapter
from core.constants import DATA_FILE, RULES_FILE
from repositories import ConfigRepository, TransactionsRepository
from services import BillsService, FinanceService


def build_services() -> tuple[FinanceService, BillsService]:
    banking_adapter = PluggyBankingAdapter()
    config_repository = ConfigRepository(RULES_FILE)
    transactions_repository = TransactionsRepository(DATA_FILE, config_repository)
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
    )


def initialize_session_dataframe(finance_service: FinanceService):
    if "df" not in st.session_state:
        st.session_state.df = finance_service.load_dataframe()
    return st.session_state.df
