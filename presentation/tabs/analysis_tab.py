from collections.abc import Callable

import pandas as pd
import streamlit as st

from services.finance_service import FinanceService
from presentation.components import section_header


def render_analysis_tab(
    filtered_df: pd.DataFrame,
    finance_service: FinanceService,
    category_icons: dict[str, str],
    formatter: Callable[[float], str],
) -> None:
    section_header("🔎 Onde Cortar Gastos?")

    cat_summary = finance_service.get_summary_by_category(filtered_df)

    if not cat_summary.empty:
        st.markdown("**Top 5 maiores categorias de gasto:**")
        for _, row in cat_summary.head(5).iterrows():
            icon = category_icons.get(row["Categoria"], "📌")
            pct = row["Percentual"] * 100
            st.markdown(f"**{icon} {row['Categoria']}** — {formatter(row['Total'])} ({pct:.1f}%)")

    st.divider()
    section_header("💡 Assinaturas Recorrentes")
    subs = finance_service.get_subscription_expenses(filtered_df)
    if not subs.empty:
        subs_display = subs[["Data", "Descrição", "Valor"]].copy()
        subs_display["Data"] = subs_display["Data"].dt.strftime("%d/%m/%Y")
        subs_display["Valor"] = subs_display["Valor"].apply(formatter)
        st.dataframe(subs_display, use_container_width=True, hide_index=True)
        total_subs = subs["Valor"].sum()
        st.markdown(f"**Total em assinaturas:** {formatter(abs(total_subs))} por mês")
        st.markdown(f"**Projeção anual:** {formatter(abs(total_subs) * 12)}")
    else:
        st.info("Nenhuma assinatura encontrada no período.")
