from pymongo.database import Database


class MongoConfigRepository:
    """MongoDB-backed replacement for ConfigRepository (JSON file)."""

    COLLECTION = "config"
    DOC_ID = "regras_classificacao"

    def __init__(self, db: Database):
        self._col = db[self.COLLECTION]
        self._ensure_document()

    def _ensure_document(self) -> None:
        if self._col.find_one({"_id": self.DOC_ID}) is None:
            self._col.insert_one(
                {"_id": self.DOC_ID, "categorias": {}, "regras": {}}
            )

    def load_config(self) -> dict:
        doc = self._col.find_one({"_id": self.DOC_ID})
        if doc is None:
            return {"categorias": {}, "regras": {}}
        doc.pop("_id", None)
        return doc

    def save_config(self, config: dict) -> None:
        self._col.replace_one(
            {"_id": self.DOC_ID},
            {"_id": self.DOC_ID, **config},
            upsert=True,
        )

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
