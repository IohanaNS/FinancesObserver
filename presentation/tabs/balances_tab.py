from collections.abc import Callable
from datetime import datetime

import pandas as pd
import streamlit as st

from presentation.components import section_header
from services.finance_service import FinanceService


def _format_optional_amount(value: float | None, formatter: Callable[[float], str]) -> str:
    if value is None or pd.isna(value):
        return "—"
    return formatter(float(value))


def _format_updated_at(value: str) -> str:
    try:
        return pd.to_datetime(value).strftime("%d/%m/%Y %H:%M")
    except Exception:  # noqa: BLE001 - fallback display
        return value


def render_balances_tab(
    finance_service: FinanceService,
    formatter: Callable[[float], str],
) -> None:
    section_header("🏦 Saldos das Contas")
    st.caption("Consulta os saldos das contas bancárias conectadas no Pluggy.")

    if "bank_balances" not in st.session_state:
        cache = finance_service.load_cached_balances()
        if cache:
            st.session_state.bank_balances = cache.get("balances", [])
            st.session_state.bank_balances_updated = cache.get("updated_at")

    if st.button("🔄 Atualizar Saldos", use_container_width=True, key="fetch_balances"):
        try:
            with st.spinner("Consultando saldos no Pluggy..."):
                balances = finance_service.fetch_account_balances()
            st.session_state.bank_balances = balances
            st.session_state.bank_balances_updated = datetime.now().isoformat()

            if not balances:
                st.warning("Nenhuma conta bancária com saldo disponível foi encontrada.")
            else:
                st.success("Saldos atualizados!")
                st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001 - errors are surfaced in UI
            st.error(f"Erro ao buscar saldos: {exc}")

    if "bank_balances_updated" in st.session_state:
        st.caption(f"Última atualização: {_format_updated_at(st.session_state.bank_balances_updated)}")

    balances = st.session_state.get("bank_balances", [])
    if not balances:
        st.info("Clique em **Atualizar Saldos** para carregar os saldos das contas.")
        return

    total_balance = sum(item["saldo"] for item in balances if item.get("saldo") is not None)
    st.markdown(
        '<div class="metric-card"><div class="metric-label">💵 Saldo Consolidado</div>'
        f'<div class="metric-value metric-blue">{formatter(total_balance)}</div></div>',
        unsafe_allow_html=True,
    )

    display = pd.DataFrame(balances).rename(
        columns={
            "banco": "Banco",
            "conta": "Conta",
            "tipo": "Tipo",
            "subtipo": "Subtipo",
            "saldo": "Saldo",
            "saldo_disponivel": "Saldo Disponível",
            "moeda": "Moeda",
        }
    )
    display["Saldo"] = display["Saldo"].apply(lambda value: _format_optional_amount(value, formatter))
    display["Saldo Disponível"] = display["Saldo Disponível"].apply(
        lambda value: _format_optional_amount(value, formatter)
    )

    columns = ["Banco", "Conta", "Tipo", "Subtipo", "Saldo", "Saldo Disponível", "Moeda"]
    if (display["Subtipo"].fillna("") == "").all():
        columns.remove("Subtipo")
    if (display["Saldo Disponível"] == "—").all():
        columns.remove("Saldo Disponível")

    st.dataframe(display[columns], use_container_width=True, hide_index=True)
