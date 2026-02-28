from collections.abc import Callable

import pandas as pd
import streamlit as st

from core.models import SidebarState
from services import BillsService, FinanceService

from presentation import render_app_header, render_kpi_cards, render_sidebar
from presentation.tabs.add_transaction_tab import render_add_transaction_tab
from presentation.tabs.analysis_tab import render_analysis_tab
from presentation.tabs.balances_tab import render_balances_tab
from presentation.tabs.bills_tab import render_bills_tab
from presentation.tabs.dashboard_tab import render_dashboard_tab
from presentation.tabs.rules_tab import render_rules_tab
from presentation.tabs.transactions_tab import render_transactions_tab


def _handle_sync_request(finance_service: FinanceService, sidebar_state: SidebarState) -> pd.DataFrame:
    if not sidebar_state.sync_requested:
        return st.session_state.df

    try:
        with st.spinner("Buscando transações no Pluggy..."):
            st.session_state.df, count = finance_service.sync_transactions(
                st.session_state.df,
                sidebar_state.sync_from,
                sidebar_state.sync_to,
            )
        if count > 0:
            st.success(f"{count} transações novas importadas!")
            st.rerun()
        else:
            st.info("Nenhuma transação nova encontrada.")
    except ValueError as exc:
        st.error(str(exc))
    except Exception as exc:  # noqa: BLE001 - erro exibido ao usuário
        st.error(f"Erro ao sincronizar: {exc}")
    return st.session_state.df


def _render_tabs(
    finance_service: FinanceService,
    bills_service: BillsService,
    filtered: pd.DataFrame,
    sidebar_state: SidebarState,
    formatter: Callable[[float], str],
) -> None:
    tab_dash, tab_transactions, tab_add, tab_rules, tab_analysis, tab_balances, tab_bills = st.tabs(
        [
            "📊 Dashboard",
            "📋 Transações",
            "➕ Adicionar",
            "⚙️ Regras",
            "🔎 Análise",
            "🏦 Saldos",
            "💳 Faturas",
        ]
    )

    category_icons = finance_service.get_category_icons()

    with tab_dash:
        render_dashboard_tab(
            filtered_df=filtered,
            finance_service=finance_service,
            category_icons=category_icons,
            formatter=formatter,
        )

    with tab_transactions:
        render_transactions_tab(
            filtered_df=filtered,
            finance_service=finance_service,
            category_icons=category_icons,
            formatter=formatter,
        )

    with tab_add:
        render_add_transaction_tab(
            finance_service=finance_service,
            df=st.session_state.df,
            formatter=formatter,
        )

    with tab_rules:
        render_rules_tab(finance_service=finance_service, df=st.session_state.df)

    with tab_analysis:
        render_analysis_tab(
            filtered_df=filtered,
            finance_service=finance_service,
            category_icons=category_icons,
            travel_goal=sidebar_state.travel_goal,
            saved_so_far=sidebar_state.saved_so_far,
            formatter=formatter,
        )

    with tab_balances:
        render_balances_tab(finance_service=finance_service, formatter=formatter)

    with tab_bills:
        render_bills_tab(bills_service=bills_service, formatter=formatter)


def render_main_screen(
    finance_service: FinanceService,
    bills_service: BillsService,
    df: pd.DataFrame,
    formatter: Callable[[float], str],
) -> None:
    sidebar_state = render_sidebar(
        df=df,
        categories=finance_service.get_categorias_list(),
        fontes=finance_service.get_fontes(),
        formatter=formatter,
    )

    df = _handle_sync_request(finance_service, sidebar_state)

    filtered = finance_service.apply_filters(
        df=df,
        date_range=sidebar_state.date_range,
        categories=sidebar_state.filter_cats,
        fontes=sidebar_state.filter_fontes,
    )

    render_app_header()
    render_kpi_cards(finance_service.calculate_kpis(filtered), formatter)
    st.markdown("<br>", unsafe_allow_html=True)

    _render_tabs(finance_service, bills_service, filtered, sidebar_state, formatter)
