import unicodedata

import pandas as pd


DEFAULT_RECLASSIFY_SKIP = {
    "transferencia pessoal",
    "transferencia entre contas",
    "pagamento cartao",
    "investimento",
    "investimentos",
    "salario",
    "rendimento",
    "resgate investimento",
    "fatura",
}


def normalize_text(text: str) -> str:
    """Lowercase, strip accents and collapse whitespace."""
    value = text.lower().strip()
    value = unicodedata.normalize("NFD", value)
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    return " ".join(value.split())


def classify_description(description: str, rules: dict[str, str]) -> str | None:
    """
    Auto-classify a description based on keyword rules.
    Matches longest keyword first so specific rules take priority.
    Ignores case, accents, and extra whitespace.
    """
    desc_norm = normalize_text(description)
    sorted_rules = sorted(rules.items(), key=lambda item: len(item[0]), reverse=True)
    for keyword, category in sorted_rules:
        if normalize_text(keyword) in desc_norm:
            return category
    return None


def classify_exact_description(description: str, rules: dict[str, str]) -> str | None:
    """Match only full-description rules (after normalization)."""
    desc_norm = normalize_text(description)
    for keyword, category in rules.items():
        if normalize_text(keyword) == desc_norm:
            return category
    return None


def reclassify_dataframe(
    df: pd.DataFrame,
    rules: dict[str, str],
    skip_categories: set[str] | None = None,
) -> pd.DataFrame:
    """
    Re-apply all rules to the dataframe.
    Keeps internal-movement categories stable, except when an exact rule exists.
    """
    skip = skip_categories or DEFAULT_RECLASSIFY_SKIP
    for idx, row in df.iterrows():
        exact_cat = classify_exact_description(str(row["Descrição"]), rules)
        if exact_cat:
            df.at[idx, "Categoria"] = exact_cat
            continue

        if normalize_text(str(row["Categoria"])) not in skip:
            new_cat = classify_description(str(row["Descrição"]), rules)
            if new_cat:
                df.at[idx, "Categoria"] = new_cat
    return df
