from repositories.config_repository import ConfigRepository
from repositories.transactions_repository import TransactionsRepository

__all__ = [
    "ConfigRepository",
    "MongoConfigRepository",
    "MongoTransactionsRepository",
    "TransactionsRepository",
]


def __getattr__(name: str):
    """Lazy-import MongoDB repositories so pymongo is only loaded when needed."""
    if name == "MongoConfigRepository":
        from repositories.mongo_config_repository import MongoConfigRepository

        return MongoConfigRepository
    if name == "MongoTransactionsRepository":
        from repositories.mongo_transactions_repository import MongoTransactionsRepository

        return MongoTransactionsRepository
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
