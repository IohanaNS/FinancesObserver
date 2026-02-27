import pandas as pd
import streamlit as st

from services.finance_service import FinanceService
from presentation.components import section_header


def render_rules_tab(finance_service: FinanceService, df: pd.DataFrame) -> None:
    section_header("⚙️ Regras de Classificação Automática")
    st.markdown(
        "Quando a descrição de uma transação contém a **palavra-chave**, "
        "ela é classificada automaticamente na **categoria** definida. "
        "Regras mais específicas (palavras mais longas) têm prioridade."
    )

    rules = finance_service.load_rules()
    categories = finance_service.get_categorias_list()

    st.divider()

    st.markdown("**Adicionar nova regra:**")
    col_r1, col_r2, col_r3 = st.columns([2, 2, 1])
    with col_r1:
        new_keyword = st.text_input("Palavra-chave", placeholder="ex: padaria")
    with col_r2:
        if categories:
            new_rule_cat = st.selectbox("Categoria da regra", categories, key="rule_cat")
        else:
            st.selectbox(
                "Categoria da regra",
                options=[],
                index=None,
                placeholder="Cadastre uma categoria primeiro",
                key="rule_cat",
            )
            new_rule_cat = None
    with col_r3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Adicionar", use_container_width=True, key="add_rule"):
            if not new_keyword.strip():
                st.error("Digite uma palavra-chave.")
            elif not new_rule_cat:
                st.error("Cadastre uma categoria antes de criar regras.")
            else:
                finance_service.add_rule(new_keyword, new_rule_cat)
                st.success(f'Regra adicionada: "{new_keyword.lower().strip()}" → {new_rule_cat}')
                st.rerun()

    st.markdown("**Remover regra:**")
    col_rm1, col_rm2 = st.columns([3, 1])
    rule_options = list(rules.keys())
    with col_rm1:
        if rule_options:
            rule_to_remove = st.selectbox(
                "Selecione a regra",
                options=rule_options,
                format_func=lambda item: f'"{item}" → {rules[item]}',
                key="remove_rule_select",
            )
        else:
            st.selectbox(
                "Selecione a regra",
                options=[],
                index=None,
                placeholder="Nenhuma regra cadastrada",
                key="remove_rule_select",
            )
            rule_to_remove = None
    with col_rm2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            "🗑️ Remover regra",
            use_container_width=True,
            key="remove_rule_btn",
            disabled=not rule_options,
        ):
            if rule_to_remove is None:
                st.error("Selecione uma regra para remover.")
            else:
                finance_service.remove_rule(rule_to_remove)
                st.success(f'Regra removida: "{rule_to_remove}"')
                st.rerun()

    st.divider()
    st.markdown("**Reclassificar todas as transações:**")
    st.caption(
        "Aplica todas as regras atuais sobre as transações existentes. "
        "Movimentações internas (transferências, fatura e afins) tendem a ser preservadas, "
        "exceto quando existe uma regra exata para a descrição."
    )
    if st.button("🔄 Reclassificar tudo", use_container_width=True, key="reclassify"):
        st.session_state.df = finance_service.reclassify_all(df)
        st.success("Todas as transações foram reclassificadas!")
        st.rerun()

    st.divider()
    st.markdown("**Gerenciar categorias:**")
    cat_icons = finance_service.get_category_icons()
    cats_display = "  ".join(f"{cat_icons.get(c, '📌')} {c}" for c in categories)
    st.caption(cats_display)

    col_nc1, col_nc2, col_nc3, col_nc4 = st.columns([2, 1, 1, 1])
    with col_nc1:
        new_cat_name = st.text_input("Nome da categoria", placeholder="ex: Educação", key="new_cat_name")
    with col_nc2:
        new_cat_icon = st.text_input("Ícone", value="📌", key="new_cat_icon")
    with col_nc3:
        new_cat_gasto = st.checkbox("Gasto real?", value=True, key="new_cat_gasto")
    with col_nc4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Criar", use_container_width=True, key="add_cat"):
            if new_cat_name.strip():
                finance_service.add_categoria(
                    name=new_cat_name.strip(),
                    icon=new_cat_icon.strip() or "📌",
                    gasto_real=new_cat_gasto,
                )
                st.success(f"Categoria criada: {new_cat_icon} {new_cat_name}")
                st.rerun()
            else:
                st.error("Digite o nome da categoria.")

    st.divider()
    st.markdown("**Testar classificação:**")
    test_desc = st.text_input(
        "Digite uma descrição para testar",
        placeholder="ex: MP *Dirceu Lanches",
    )
    if test_desc:
        result = finance_service.classify(test_desc)
        if result:
            icon = finance_service.get_category_icons().get(result, "📌")
            st.success(f"{icon} Classificada como: **{result}**")
        else:
            st.warning("Nenhuma regra encontrada para essa descrição. Será classificada como **Outros**.")
