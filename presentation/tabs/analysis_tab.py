from collections.abc import Callable

import pandas as pd
import streamlit as st

from services.finance_service import FinanceService
from presentation.components import section_header


def render_analysis_tab(
    filtered_df: pd.DataFrame,
    finance_service: FinanceService,
    category_icons: dict[str, str],
    travel_goal: float,
    saved_so_far: float,
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
        st.info(
            "💡 Revise se todas essas assinaturas estão sendo usadas. "
            "Cancelar as desnecessárias pode liberar dinheiro para a viagem!"
        )
    else:
        st.info("Nenhuma assinatura encontrada no período.")

    st.divider()
    section_header("🎯 Simulador de Economia")
    st.markdown("Selecione categorias onde você acha que pode reduzir gastos:")

    savings_cats = st.multiselect(
        "Categorias para reduzir",
        options=[c for c in cat_summary["Categoria"].tolist()] if not cat_summary.empty else [],
        default=[],
        key="savings_sim",
    )
    cut_pct = st.slider("Percentual de redução", 10, 80, 30, 5, format="%d%%")

    simulation = finance_service.calculate_savings_simulation(
        summary_by_category=cat_summary,
        selected_categories=savings_cats,
        cut_pct=cut_pct,
        travel_goal=travel_goal,
        saved_so_far=saved_so_far,
    )
    if simulation is not None:
        st.success(
            f"Cortando **{cut_pct}%** nessas categorias, você economizaria "
            f"**{formatter(simulation.monthly_saving)}/mês** → "
            f"**{formatter(simulation.yearly_saving)}/ano**"
        )
        if simulation.months_to_goal is not None:
            if simulation.months_to_goal <= 12:
                st.markdown(
                    f"🎉 Você atingiria a meta da viagem em **{simulation.months_to_goal:.1f} meses** "
                    "só com essa economia!"
                )
            else:
                st.markdown(
                    f"⏳ Seriam **{simulation.months_to_goal:.1f} meses** só com essa economia — "
                    "considere combinar com outras estratégias."
                )
