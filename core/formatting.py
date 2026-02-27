def fmt_brl(value: float) -> str:
    if value < 0:
        return f"-R$ {abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
