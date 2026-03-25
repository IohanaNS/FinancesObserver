import calendar
from datetime import date

import pandas as pd
import streamlit as st

from core.models import SidebarState
from ports.accounts_port import AccountsPort


def _coerce_date_range(value: date | tuple[date, ...] | list[date]) -> tuple[date, date]:
    if isinstance(value, (tuple, list)):
        if len(value) >= 2:
            return value[0], value[1]
        if len(value) == 1:
            return value[0], value[0]
        return date.today(), date.today()
    return value, value


def render_sidebar(
    df: pd.DataFrame,
    categories: list[str],
    fontes: list[str],
    accounts_adapter: AccountsPort | None = None,
) -> SidebarState:
    with st.sidebar:
        st.markdown("## Controle Financeiro 📊")

        st.markdown("## 🔍 Filtros")
        if df.empty or pd.isna(df["Data"].min()):
            date_min = date.today()
            date_max = date.today()
            default_start = date_min
            default_end = date_max
        else:
            date_min = df["Data"].dt.date.min()
            data_max = df["Data"].dt.date.max()
            today = date.today()
            date_max = max(data_max, today)
            # Default to the most recent month with data
            default_start = date(data_max.year, data_max.month, 1)
            default_end = data_max

        date_selection = st.date_input(
            "Período",
            value=(default_start, default_end),
            min_value=date_min,
            max_value=date_max,
        )
        date_range = _coerce_date_range(date_selection)
        filter_cats = st.multiselect("Categorias", options=categories, default=[])
        filter_fontes = st.multiselect("Fontes", options=fontes, default=[])

        st.divider()
        st.markdown("## 🔄 Sincronizar Pluggy")
        sync_cols = st.columns(2)
        today = date.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        with sync_cols[0]:
            sync_from = st.date_input("De", value=date(today.year, today.month, 1), key="sync_from")
        with sync_cols[1]:
            sync_to = st.date_input("Até", value=date(today.year, today.month, last_day), key="sync_to")

        sync_requested = st.button("Sincronizar", use_container_width=True)

        if accounts_adapter is not None:
            st.divider()
            with st.expander("🏦 Gerenciar Contas"):
                contas = accounts_adapter.list_accounts()
                if contas:
                    for conta in contas:
                        col_name, col_btn = st.columns([3, 1])
                        with col_name:
                            st.text(conta.get("nome", ""))
                        with col_btn:
                            if st.button(
                                "✕",
                                key=f"rm_{conta.get('pluggy_item_id')}",
                                help="Remover conta",
                            ):
                                accounts_adapter.remove_account(conta["pluggy_item_id"])
                                st.rerun()
                else:
                    st.caption("Nenhuma conta cadastrada.")

                st.markdown("---")
                new_id = st.text_input("Pluggy Item ID", key="new_account_id")
                new_nome = st.text_input("Nome da conta", key="new_account_nome")
                if st.button("Adicionar", key="add_account", use_container_width=True):
                    if new_id and new_nome:
                        try:
                            accounts_adapter.add_account(new_id, new_nome)
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                    else:
                        st.warning("Preencha ambos os campos.")

    return SidebarState(
        date_range=date_range,
        filter_cats=filter_cats,
        filter_fontes=filter_fontes,
        sync_from=sync_from,
        sync_to=sync_to,
        sync_requested=sync_requested,
    )
