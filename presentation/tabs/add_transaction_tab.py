from collections.abc import Callable
from datetime import date

import pandas as pd
import streamlit as st

from services.finance_service import FinanceService
from presentation.components import section_header


def render_add_transaction_tab(
    finance_service: FinanceService,
    df: pd.DataFrame,
    formatter: Callable[[float], str],
) -> None:
    section_header("Nova Transação")

    categories = finance_service.get_categorias_list()
    fontes = finance_service.get_fontes()
    if not categories:
        st.error("Cadastre pelo menos uma categoria para adicionar transações.")
        return

    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_date = st.date_input("Data", value=date.today())
            new_desc = st.text_input("Descrição")
            new_valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01, format="%.2f")
        with col2:
            new_tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
            auto_hint = finance_service.classify(new_desc) if new_desc else None
            default_cat_idx = (
                categories.index(auto_hint)
                if auto_hint and auto_hint in categories
                else 0
            )
            new_cat = st.selectbox(
                "Categoria",
                categories,
                index=default_cat_idx,
                help="A categoria é sugerida automaticamente pelas regras, mas você pode alterar.",
            )
            new_fonte = st.selectbox("Fonte", fontes)

        submitted = st.form_submit_button("✅ Adicionar Transação", use_container_width=True)
        if submitted:
            if not new_desc.strip():
                st.error("Preencha a descrição.")
            else:
                st.session_state.df = finance_service.add_manual_transaction(
                    df=df,
                    transaction_date=new_date,
                    description=new_desc,
                    value=new_valor,
                    tx_type=new_tipo,
                    category=new_cat,
                    source=new_fonte,
                )
                st.success(f"Transação adicionada: {new_desc} — {formatter(new_valor)}")
                st.rerun()

    st.divider()
    section_header("Remover Transação")
    st.caption("Selecione a transação a ser removida pelo índice da tabela abaixo.")

    if df.empty:
        st.info("Nenhuma transação cadastrada para remover.")
        return

    remove_df = df.copy()
    remove_df["Data_fmt"] = remove_df["Data"].dt.strftime("%d/%m/%Y")
    st.dataframe(
        remove_df[["Data_fmt", "Descrição", "Valor", "Categoria", "Fonte"]].rename(
            columns={"Data_fmt": "Data"}
        ),
        use_container_width=True,
        height=300,
    )
    col_del1, col_del2, _ = st.columns([1, 1, 3])
    with col_del1:
        idx_to_remove = st.number_input(
            "Índice",
            min_value=0,
            max_value=max(0, len(df) - 1),
            step=1,
        )
    with col_del2:
        if st.button("🗑️ Remover", use_container_width=True):
            index = int(idx_to_remove)
            description = df.iloc[index]["Descrição"]
            st.session_state.df = finance_service.delete_manual_transaction(df, index)
            st.success(f"Removida: {description}")
            st.rerun()
