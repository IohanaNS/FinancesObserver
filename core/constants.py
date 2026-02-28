DATA_FILE = "dados_financeiros.csv"
RULES_FILE = "regras_classificacao.json"
BILLS_CACHE_FILE = "faturas_cache.json"
BALANCES_CACHE_FILE = "saldos_cache.json"
INVESTMENTS_CACHE_FILE = "investimentos_cache.json"

ACCOUNTS_FILE = "contas.json"
FONTES_SINTETICAS = ["Outro"]
TRANSACTION_COLUMNS = ["Data", "Descrição", "Valor", "Tipo", "Categoria", "Fonte", "pluggy_id"]

# Categories that represent internal movements (not real expenses)
CROSS_BANK_CATEGORIES = {
    "Fatura",
    "Pagamento Cartão",
    "Transferência Entre Contas",
    "Investimento",
    "Resgate Investimento",
    "Investimentos",
}

CATEGORY_SALARY = "Salário"
CATEGORY_INVESTMENTS = "Investimentos"
CATEGORY_SUBSCRIPTIONS = "Assinatura/Digital"
