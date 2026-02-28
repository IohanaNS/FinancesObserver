import pandas as pd

from core.constants import (
    CROSS_BANK_CATEGORIES,
    DATA_FILE,
    RULES_FILE,
    TRANSACTION_COLUMNS,
)
from domain.classification import (
    classify_description,
    classify_exact_description,
    normalize_text,
)
from repositories import ConfigRepository, TransactionsRepository

_config_repository = ConfigRepository(RULES_FILE)
_transactions_repository = TransactionsRepository(DATA_FILE, _config_repository)
COLUMNS = TRANSACTION_COLUMNS


# ─── Config File (categories + rules) ───


def _load_config() -> dict:
    return _config_repository.load_config()


def _save_config(config: dict):
    _config_repository.save_config(config)


def load_categorias() -> dict:
    """Returns {name: {icon, gasto_real}} dict."""
    return _config_repository.load_categories()


def get_categorias_list() -> list[str]:
    return _config_repository.get_categories_list()


def get_category_icons() -> dict[str, str]:
    return _config_repository.get_category_icons()


def get_real_expense_categories() -> set[str]:
    return _config_repository.get_real_expense_categories()


def add_categoria(name: str, icon: str = "📌", gasto_real: bool = True):
    _config_repository.add_category(name, icon, gasto_real)


def remove_categoria(name: str):
    _config_repository.remove_category(name)


# ─── Rules Engine ───


def load_rules() -> dict:
    return _config_repository.load_rules()


def _save_rules(rules: dict):
    _config_repository.save_rules(rules)


def add_rule(keyword: str, category: str) -> dict:
    return _config_repository.add_rule(keyword, category)


def remove_rule(keyword: str) -> dict:
    return _config_repository.remove_rule(keyword)


def _normalize(text: str) -> str:
    """Lowercase, strip accents and collapse whitespace."""
    return normalize_text(text)


def classify(description: str, rules: dict | None = None) -> str | None:
    active_rules = rules or load_rules()
    return classify_description(description, active_rules)


def _classify_exact(description: str, rules: dict) -> str | None:
    """Match only full-description rules (after normalization)."""
    return classify_exact_description(description, rules)


def reclassify_all(df: pd.DataFrame) -> pd.DataFrame:
    return _transactions_repository.reclassify_all(df)


# ─── Data Management ───


def _ensure_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure Data column is datetime even on empty DataFrames."""
    return _transactions_repository._ensure_dtypes(df)


def load_data() -> pd.DataFrame:
    return _transactions_repository.load_data()


def save_data(df: pd.DataFrame):
    _transactions_repository.save_data(df)


def add_transaction(
    df: pd.DataFrame,
    data: str,
    descricao: str,
    valor: float,
    tipo: str,
    categoria: str,
    fonte: str,
) -> pd.DataFrame:
    return _transactions_repository.add_transaction(df, data, descricao, valor, tipo, categoria, fonte)


def delete_transaction(df: pd.DataFrame, index: int) -> pd.DataFrame:
    return _transactions_repository.delete_transaction(df, index)


def get_real_expenses(df: pd.DataFrame) -> pd.DataFrame:
    return _transactions_repository.get_real_expenses(df)


def get_summary_by_category(df: pd.DataFrame) -> pd.DataFrame:
    return _transactions_repository.get_summary_by_category(df)


def get_summary_by_fonte(df: pd.DataFrame) -> pd.DataFrame:
    return _transactions_repository.get_summary_by_fonte(df)


def get_daily_expenses(df: pd.DataFrame) -> pd.DataFrame:
    return _transactions_repository.get_daily_expenses(df)


def add_synced_transactions(df: pd.DataFrame, transactions: list[dict]) -> tuple[pd.DataFrame, int]:
    return _transactions_repository.add_synced_transactions(df, transactions)


def deduplicate_cross_bank(df: pd.DataFrame) -> pd.DataFrame:
    return _transactions_repository.deduplicate_cross_bank(df)
