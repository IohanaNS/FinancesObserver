from collections.abc import Callable
from datetime import date

import pandas as pd
import streamlit as st

from core.models import SidebarState


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


def render_sidebar(
    df: pd.DataFrame,
    categories: list[str],
    fontes: list[str],
    formatter: Callable[[float], str],
    months_left: int = 10,
) -> SidebarState:
    with st.sidebar:
        st.markdown("## ✈️ Controle Financeiro 2026")
        travel_goal = st.number_input("Meta de economia (R$)", value=15000, step=500, key="goal")
        saved_so_far = st.number_input("Já economizado (R$)", value=1500, step=100, key="saved")
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

        remaining = travel_goal - saved_so_far
        monthly_needed = remaining / months_left if months_left > 0 else 0
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
        saved_so_far=saved_so_far,
        months_left=months_left,
        date_range=date_range,
        filter_cats=filter_cats,
        filter_fontes=filter_fontes,
        sync_from=sync_from,
        sync_to=sync_to,
        sync_requested=sync_requested,
    )
