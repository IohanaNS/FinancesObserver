from collections.abc import Callable

import streamlit as st

from core.models import FinanceKpis


def section_header(title: str) -> None:
    st.markdown(f'<p class="section-header">{title}</p>', unsafe_allow_html=True)


def render_app_header() -> None:
    st.markdown('<p class="main-title">Controle Financeiro</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Organizando suas finanças — cada real conta!</p>',
        unsafe_allow_html=True,
    )


def render_kpi_cards(metrics: FinanceKpis, formatter: Callable[[float], str]) -> None:
    cols = st.columns(4)
    with cols[0]:
        st.markdown(
            '<div class="metric-card"><div class="metric-label">💰 Salário</div>'
            f'<div class="metric-value metric-green">{formatter(metrics.total_income)}</div></div>',
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            '<div class="metric-card"><div class="metric-label">🔻 Gastos Reais</div>'
            f'<div class="metric-value metric-red">{formatter(abs(metrics.total_real_expenses))}</div></div>',
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            '<div class="metric-card"><div class="metric-label">📊 % do Salário Gasto</div>'
            f'<div class="metric-value metric-amber">{metrics.pct_salary:.1f}%</div></div>',
            unsafe_allow_html=True,
        )
    with cols[3]:
        st.markdown(
            '<div class="metric-card"><div class="metric-label">📈 Investido no Mês</div>'
            f'<div class="metric-value metric-blue">{formatter(abs(metrics.total_invested))}</div></div>',
            unsafe_allow_html=True,
        )
