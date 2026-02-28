from collections.abc import Callable
from datetime import date

import pandas as pd
import streamlit as st

from core.models import SidebarState
from services.finance_service import FinanceService


def _coerce_date_range(value: date | tuple[date, date] | list[date]) -> tuple[date, date]:
    if isinstance(value, tuple):
        if len(value) == 2:
            return value[0], value[1]
        if len(value) == 1:
            return value[0], value[0]
    if isinstance(value, list):
        if len(value) >= 2:
            return value[0], value[1]
        if len(value) == 1:
            return value[0], value[0]
    return value, value


def _get_invested_total(finance_service: FinanceService) -> float:
    cache = finance_service.load_cached_investments()
    if not cache:
        return 0.0
    investments = cache.get("investments", [])
    return sum(
        item.get("saldo_atual", 0.0)
        for item in investments
        if item.get("saldo_atual") is not None
    )


def render_sidebar(
    df: pd.DataFrame,
    categories: list[str],
    fontes: list[str],
    finance_service: FinanceService,
    formatter: Callable[[float], str],
) -> SidebarState:
    with st.sidebar:
        st.markdown("## Controle Financeiro 📊")

        if "goal" not in st.session_state:
            st.session_state.goal = 15000.0
        travel_goal = st.number_input(
            "Meta de economia (R$)", min_value=0.0, step=500.0, key="goal"
        )

        if "goal_months" not in st.session_state:
            st.session_state.goal_months = 12
        months_left = st.number_input(
            "Prazo para atingir (meses)", min_value=1, step=1, key="goal_months"
        )

        saved_so_far = _get_invested_total(finance_service)
        pct = min(saved_so_far / travel_goal, 1.0) if travel_goal > 0 else 0

        st.markdown(
            f"""
        <div style="margin: 16px 0;">
            <div class="goal-bar-bg">
                <div class="goal-bar-fill" style="width: {pct*100:.0f}%">{pct*100:.1f}%</div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:currentColor; opacity:0.8;">
                <span>{formatter(saved_so_far)}</span>
                <span>{formatter(travel_goal)}</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        remaining = max(travel_goal - saved_so_far, 0.0)
        monthly_needed = remaining / months_left if months_left > 0 else 0
        st.markdown(f"**Investido:** {formatter(saved_so_far)}")
        st.markdown(f"**Falta:** {formatter(remaining)}")
        st.markdown(f"**Por mês:** {formatter(monthly_needed)} nos próximos {months_left} meses")

        st.divider()
        st.markdown("## 🔍 Filtros")
        if df.empty or pd.isna(df["Data"].min()):
            date_min = date.today()
            date_max = date.today()
        else:
            today = date.today()
            date_min = date(today.year, today.month, 1)
            date_max = today

        date_selection = st.date_input(
            "Período",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max,
        )
        date_range = _coerce_date_range(date_selection)
        filter_cats = st.multiselect("Categorias", options=categories, default=[])
        filter_fontes = st.multiselect("Fontes", options=fontes, default=[])

        st.divider()
        st.markdown("## 🔄 Sincronizar Pluggy")
        sync_cols = st.columns(2)
        with sync_cols[0]:
            sync_from = st.date_input("De", value=date(2026, 2, 1), key="sync_from")
        with sync_cols[1]:
            sync_to = st.date_input("Até", value=date.today(), key="sync_to")

        sync_requested = st.button("Sincronizar", use_container_width=True)

    return SidebarState(
        travel_goal=travel_goal,
        months_left=months_left,
        date_range=date_range,
        filter_cats=filter_cats,
        filter_fontes=filter_fontes,
        sync_from=sync_from,
        sync_to=sync_to,
        sync_requested=sync_requested,
    )
