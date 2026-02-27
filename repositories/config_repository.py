import json
import os


class ConfigRepository:
    def __init__(self, rules_file: str):
        self._rules_file = rules_file

    def load_config(self) -> dict:
        if os.path.exists(self._rules_file):
            with open(self._rules_file, "r", encoding="utf-8") as file:
                return json.load(file)
        return {"categorias": {}, "regras": {}}

    def save_config(self, config: dict) -> None:
        with open(self._rules_file, "w", encoding="utf-8") as file:
            json.dump(config, file, ensure_ascii=False, indent=2)

    def load_categories(self) -> dict:
        return self.load_config().get("categorias", {})

    def get_categories_list(self) -> list[str]:
        return list(self.load_categories().keys())

    def get_category_icons(self) -> dict[str, str]:
        return {
            name: category["icon"]
            for name, category in self.load_categories().items()
        }

    def get_real_expense_categories(self) -> set[str]:
        return {
            name
            for name, category in self.load_categories().items()
            if category.get("gasto_real", False)
        }

    def add_category(self, name: str, icon: str = "📌", gasto_real: bool = True) -> None:
        config = self.load_config()
        config["categorias"][name] = {"icon": icon, "gasto_real": gasto_real}
        self.save_config(config)

    def remove_category(self, name: str) -> None:
        config = self.load_config()
        config["categorias"].pop(name, None)
        self.save_config(config)

    def load_rules(self) -> dict:
        return self.load_config().get("regras", {})

    def save_rules(self, rules: dict) -> None:
        config = self.load_config()
        config["regras"] = rules
        self.save_config(config)

    def add_rule(self, keyword: str, category: str) -> dict:
        rules = self.load_rules()
        rules[keyword.lower().strip()] = category
        self.save_rules(rules)
        return rules

    def remove_rule(self, keyword: str) -> dict:
        rules = self.load_rules()
        rules.pop(keyword.lower().strip(), None)
        self.save_rules(rules)
        return rules
