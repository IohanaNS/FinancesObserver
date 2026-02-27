from collections.abc import Callable

import pandas as pd
import streamlit as st

from services.finance_service import FinanceService
from presentation.components import section_header


@st.dialog("Alterar Categoria")
def _category_change_dialog(finance_service: FinanceService) -> None:
    change = st.session_state.pending_cat_change
    desc = change["description"]
    old_cat = change["old_category"]
    new_cat = change["new_category"]
    idx = change["index"]

    st.markdown(f"**Descrição:** {desc}")
    st.markdown(f"**{old_cat}** → **{new_cat}**")

    total_same = int((st.session_state.df["Descrição"] == desc).sum())

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Apenas esta", use_container_width=True):
            st.session_state.df.at[idx, "Categoria"] = new_cat
            finance_service.save_dataframe(st.session_state.df)
            del st.session_state.pending_cat_change
            st.session_state.tx_editor_v = st.session_state.get("tx_editor_v", 0) + 1
            st.rerun()
    with col2:
        label = f"Todas com esta descrição ({total_same})"
        if st.button(label, use_container_width=True):
            mask = st.session_state.df["Descrição"] == desc
            st.session_state.df.loc[mask, "Categoria"] = new_cat
            finance_service.add_rule(desc, new_cat)
            finance_service.save_dataframe(st.session_state.df)
            del st.session_state.pending_cat_change
            st.session_state.tx_editor_v = st.session_state.get("tx_editor_v", 0) + 1
            st.rerun()


def render_transactions_tab(
    filtered_df: pd.DataFrame,
    finance_service: FinanceService,
    category_icons: dict[str, str],
    formatter: Callable[[float], str],
) -> None:
    section_header("Todas as Transações")

    if filtered_df.empty:
        st.info("Nenhuma transação encontrada.")
        return

    categories = finance_service.get_categorias_list()

    # Show dialog if there's a pending category change
    if "pending_cat_change" in st.session_state:
        _category_change_dialog(finance_service)

    # Build display DataFrame preserving original index for mapping back
    display_df = filtered_df[["Data", "Descrição", "Valor", "Categoria", "Fonte"]].copy()
    display_df["Data"] = display_df["Data"].dt.strftime("%d/%m/%Y")
    display_df["Valor"] = display_df["Valor"].apply(formatter)

    editor_key = f"tx_editor_{st.session_state.get('tx_editor_v', 0)}"

    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        height=600,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Data": st.column_config.TextColumn("Data", disabled=True),
            "Descrição": st.column_config.TextColumn("Descrição", disabled=True),
            "Valor": st.column_config.TextColumn("Valor", disabled=True),
            "Categoria": st.column_config.SelectboxColumn(
                "Categoria",
                options=categories,
                required=True,
            ),
            "Fonte": st.column_config.TextColumn("Fonte", disabled=True),
        },
        key=editor_key,
    )

    # Detect category change (only if no pending dialog)
    if "pending_cat_change" not in st.session_state:
        changed_indices = edited_df.index[edited_df["Categoria"] != display_df["Categoria"]]
        if len(changed_indices) > 0:
            idx = changed_indices[0]
            st.session_state.pending_cat_change = {
                "index": idx,
                "description": filtered_df.at[idx, "Descrição"],
                "old_category": display_df.at[idx, "Categoria"],
                "new_category": edited_df.at[idx, "Categoria"],
            }
            st.rerun()

    st.markdown(f"**{len(display_df)} transações** exibidas")

    st.divider()
    col_exp1, col_exp2, _ = st.columns([1, 1, 3])
    with col_exp1:
        csv = finance_service.build_csv_export(filtered_df)
        st.download_button("📥 Exportar CSV", csv, "transacoes.csv", "text/csv")
    with col_exp2:
        excel = finance_service.build_excel_export(filtered_df)
        st.download_button(
            "📥 Exportar Excel",
            excel,
            "transacoes.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
