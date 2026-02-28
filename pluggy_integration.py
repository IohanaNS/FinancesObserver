from collections.abc import Callable
from datetime import datetime, timedelta
import json
import os

import pandas as pd
import requests

from core.settings import PluggySettings, load_pluggy_settings


def _get_api_key(settings: PluggySettings) -> str:
    response = requests.post(
        f"{settings.base_url}/auth",
        json={
            "clientId": settings.client_id,
            "clientSecret": settings.client_secret,
        },
    )
    response.raise_for_status()
    return response.json()["apiKey"]


def _headers(settings: PluggySettings) -> dict:
    return {"X-API-KEY": _get_api_key(settings)}


def _to_float_or_none(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _map_investment(investment: dict, bank: str) -> dict:
    balance = _to_float_or_none(investment.get("balance"))
    withdrawal = _to_float_or_none(investment.get("amountWithdrawal"))
    original = _to_float_or_none(investment.get("amountOriginal"))
    profit = _to_float_or_none(investment.get("amountProfit"))
    return {
        "banco": bank,
        "investimento": investment.get("name", "Investimento"),
        "investment_id": investment.get("id"),
        "tipo": investment.get("type", "UNKNOWN"),
        "subtipo": investment.get("subtype", ""),
        "saldo_atual": balance,
        "saldo_disponivel": withdrawal,
        "aporte_original": original,
        "lucro_prejuizo": profit,
        "status": investment.get("status"),
        "moeda": investment.get("currencyCode", "BRL"),
    }


def fetch_accounts(headers: dict, item_id: str, base_url: str) -> list:
    response = requests.get(f"{base_url}/accounts", params={"itemId": item_id}, headers=headers)
    response.raise_for_status()
    return response.json()["results"]


def fetch_transactions(
    headers: dict,
    account_id: str,
    date_from: str,
    date_to: str,
    base_url: str,
) -> list:
    """Fetch all transactions for an account, handling pagination."""
    all_transactions = []
    page = 1

    while True:
        response = requests.get(
            f"{base_url}/transactions",
            params={
                "accountId": account_id,
                "from": date_from,
                "to": date_to,
                "pageSize": 500,
                "page": page,
            },
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        all_transactions.extend(data.get("results", []))
        if len(all_transactions) >= data.get("total", 0):
            break
        page += 1

    return all_transactions


def fetch_investments_for_item(
    headers: dict,
    item_id: str,
    base_url: str,
) -> list[dict]:
    """Fetch all investments for one item, handling pagination."""
    all_investments: list[dict] = []
    page = 1

    while True:
        response = requests.get(
            f"{base_url}/investments",
            params={
                "itemId": item_id,
                "pageSize": 500,
                "page": page,
            },
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        page_results = data.get("results", [])
        all_investments.extend(page_results)
        total = data.get("total")
        if total is not None and len(all_investments) >= int(total):
            break
        if total is None and not page_results:
            break
        page += 1

    return all_investments


def _map_transaction(
    tx: dict,
    fonte: str,
    is_credit_card: bool,
    categorize: Callable[[str], str | None],
) -> dict:
    """Convert a Pluggy transaction (raw dict) to the app's format."""
    amount = tx["amount"]

    # Credit card: Pluggy uses positive=charge, negative=payment -> invert
    if is_credit_card:
        amount = -amount

    tx_type = "Saída" if amount < 0 else "Entrada"
    description = tx.get("description", "")
    category = categorize(description) or "Outros"

    tx_date = pd.to_datetime(tx["date"])
    if getattr(tx_date, "tz", None) is not None:
        tx_date = tx_date.tz_localize(None)

    return {
        "Data": tx_date,
        "Descrição": description,
        "Valor": amount,
        "Tipo": tx_type,
        "Categoria": category,
        "Fonte": fonte,
        "pluggy_id": tx["id"],
    }


def save_bills_cache(cc_info: list[dict], cache_file: str):
    """Save credit card info to local JSON cache."""
    data = {
        "updated_at": datetime.now().isoformat(),
        "cards": cc_info,
    }
    with open(cache_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, default=str)


def save_balances_cache(balances: list[dict], cache_file: str):
    """Save bank balances to local JSON cache."""
    data = {
        "updated_at": datetime.now().isoformat(),
        "balances": balances,
    }
    with open(cache_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, default=str)


def save_investments_cache(
    investments: list[dict],
    cache_file: str,
    goal: float | None = None,
    goal_months: int | None = None,
):
    """Save investments snapshot to local JSON cache."""
    existing = load_investments_cache(cache_file) or {}
    preserved_goal = goal if goal is not None else _to_float_or_none(existing.get("goal"))
    preserved_months = goal_months if goal_months is not None else existing.get("goal_months")
    data: dict = {
        "updated_at": datetime.now().isoformat(),
        "investments": investments,
    }
    if preserved_goal is not None:
        data["goal"] = preserved_goal
    if preserved_months is not None:
        data["goal_months"] = int(preserved_months)
    with open(cache_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, default=str)


def save_investments_goal(
    goal: float,
    months: int | None = None,
    cache_file: str = "investimentos_cache.json",
) -> None:
    """Persist the financial goal and optional timeline in the investments cache JSON."""
    cached = load_investments_cache(cache_file) or {}
    cached_investments = cached.get("investments", [])
    save_investments_cache(
        investments=cached_investments if isinstance(cached_investments, list) else [],
        cache_file=cache_file,
        goal=float(goal),
        goal_months=months,
    )


def load_bills_cache(cache_file: str = "faturas_cache.json") -> dict | None:
    """Load cached credit card info. Returns None if no cache exists."""
    if not os.path.exists(cache_file):
        return None
    with open(cache_file, "r", encoding="utf-8") as file:
        return json.load(file)


def load_balances_cache(cache_file: str = "saldos_cache.json") -> dict | None:
    """Load cached balances. Returns None if no cache exists."""
    if not os.path.exists(cache_file):
        return None
    with open(cache_file, "r", encoding="utf-8") as file:
        return json.load(file)


def load_investments_cache(cache_file: str = "investimentos_cache.json") -> dict | None:
    """Load cached investments. Returns None if no cache exists."""
    if not os.path.exists(cache_file):
        return None
    with open(cache_file, "r", encoding="utf-8") as file:
        return json.load(file)


def fetch_bills(headers: dict, account_id: str, base_url: str) -> list:
    """Fetch credit card bills for an account. Returns empty list if not supported."""
    try:
        response = requests.get(f"{base_url}/bills", params={"accountId": account_id}, headers=headers)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.HTTPError:
        return []


def fetch_credit_card_info(settings: PluggySettings | None = None) -> list[dict]:
    """
    Fetch credit card bills and account info for all connected credit card accounts.
    Returns list of dicts with account info + bills.
    """
    settings = settings or load_pluggy_settings()
    if not settings.has_credentials:
        raise ValueError("Credenciais do Pluggy não configuradas no .env")

    headers = _headers(settings)
    results = []

    for item_id, bank in settings.item_map.items():
        accounts = fetch_accounts(headers, item_id, settings.base_url)
        for account in accounts:
            if account["type"] != "CREDIT":
                continue

            bills = fetch_bills(headers, account["id"], settings.base_url)
            credit_data = account.get("creditData", {})

            results.append(
                {
                    "banco": bank,
                    "account_name": account.get("name", "Cartão"),
                    "credit_limit": credit_data.get("creditLimit"),
                    "available_limit": credit_data.get("availableCreditLimit"),
                    "closing_date": credit_data.get("balanceCloseDate"),
                    "due_date": credit_data.get("balanceDueDate"),
                    "bills": bills,
                }
            )

    save_bills_cache(results, settings.bills_cache_file)
    return results


def fetch_account_balances(settings: PluggySettings | None = None) -> list[dict]:
    """
    Fetch non-credit account balances from all connected items.
    Returns a normalized list ready to display in the UI.
    """
    settings = settings or load_pluggy_settings()
    if not settings.has_credentials:
        raise ValueError("Credenciais do Pluggy não configuradas no .env")

    headers = _headers(settings)
    results: list[dict] = []

    for item_id, bank in settings.item_map.items():
        accounts = fetch_accounts(headers, item_id, settings.base_url)
        for account in accounts:
            if account.get("type") == "CREDIT":
                continue

            balance = _to_float_or_none(account.get("balance"))
            available = _to_float_or_none(account.get("availableBalance"))
            if balance is None and available is None:
                continue

            results.append(
                {
                    "banco": bank,
                    "conta": account.get("name", "Conta"),
                    "tipo": account.get("type", "UNKNOWN"),
                    "subtipo": account.get("subtype", ""),
                    "saldo": balance,
                    "saldo_disponivel": available,
                    "moeda": account.get("currencyCode", "BRL"),
                }
            )

    balances = sorted(results, key=lambda item: (item["banco"], item["conta"]))
    save_balances_cache(balances, settings.balances_cache_file)
    return balances


def fetch_investments(settings: PluggySettings | None = None) -> list[dict]:
    """
    Fetch investments from all connected items using Pluggy's Investment endpoint.
    Returns normalized rows for the investments tab.
    """
    settings = settings or load_pluggy_settings()
    if not settings.has_credentials:
        raise ValueError("Credenciais do Pluggy não configuradas no .env")

    headers = _headers(settings)
    results: list[dict] = []

    for item_id, bank in settings.item_map.items():
        investments = fetch_investments_for_item(
            headers=headers,
            item_id=item_id,
            base_url=settings.base_url,
        )
        for investment in investments:
            results.append(_map_investment(investment, bank))

    investments = sorted(results, key=lambda item: (item["banco"], item["investimento"]))
    save_investments_cache(investments, settings.investments_cache_file)
    return investments


def sync_all(
    date_from: str | None = None,
    date_to: str | None = None,
    categorize: Callable[[str], str | None] | None = None,
    settings: PluggySettings | None = None,
) -> list[dict]:
    """
    Fetch transactions from all connected items/accounts.
    Returns list of dicts ready to merge into the app DataFrame.
    """
    settings = settings or load_pluggy_settings()
    if not settings.has_credentials:
        raise ValueError("Credenciais do Pluggy não configuradas no .env")

    if date_from is None:
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if date_to is None:
        date_to = datetime.now().strftime("%Y-%m-%d")

    categorize = categorize or (lambda _description: "Outros")
    headers = _headers(settings)
    all_transactions = []

    for item_id, bank in settings.item_map.items():
        accounts = fetch_accounts(headers, item_id, settings.base_url)
        for account in accounts:
            is_credit_card = account["type"] == "CREDIT"
            fonte = f"Cartão Crédito {bank}" if is_credit_card else bank

            transactions = fetch_transactions(
                headers=headers,
                account_id=account["id"],
                date_from=date_from,
                date_to=date_to,
                base_url=settings.base_url,
            )
            for tx in transactions:
                mapped = _map_transaction(
                    tx=tx,
                    fonte=fonte,
                    is_credit_card=is_credit_card,
                    categorize=categorize,
                )
                all_transactions.append(mapped)

    return all_transactions
