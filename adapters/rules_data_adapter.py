import pandas as pd

from core.constants import DATA_FILE, RULES_FILE
from repositories import ConfigRepository, TransactionsRepository


class RulesDataAdapter:
    def __init__(
        self,
        data_file: str = DATA_FILE,
        rules_file: str = RULES_FILE,
        config_repository: ConfigRepository | None = None,
        transactions_repository: TransactionsRepository | None = None,
    ):
        self._config_repository = config_repository or ConfigRepository(rules_file)
        self._transactions_repository = transactions_repository or TransactionsRepository(
            data_file,
            self._config_repository,
        )

    def get_categorias_list(self) -> list[str]:
        return self._config_repository.get_categories_list()

    def get_category_icons(self) -> dict[str, str]:
        return self._config_repository.get_category_icons()

    def load_rules(self) -> dict:
        return self._config_repository.load_rules()

    def add_rule(self, keyword: str, category: str) -> dict:
        return self._config_repository.add_rule(keyword, category)

    def remove_rule(self, keyword: str) -> dict:
        return self._config_repository.remove_rule(keyword)

    def reclassify_all(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._transactions_repository.reclassify_all(df)

    def classify(self, description: str, rules: dict | None = None) -> str | None:
        return self._transactions_repository.classify(description, rules)

    def add_categoria(self, name: str, icon: str, gasto_real: bool) -> None:
        self._config_repository.add_category(name, icon, gasto_real)
