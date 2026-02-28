from collections.abc import Callable
import math
from numbers import Real

import pandas as pd
import streamlit as st

from services.finance_service import FinanceService
from presentation.components import section_header

SORT_OPTIONS = [
    "Data (mais recente)",
    "Data (mais antiga)",
    "Maior valor absoluto",
    "Menor valor absoluto",
    "Maior valor",
    "Menor valor",
    "Descrição (A-Z)",
    "Descrição (Z-A)",
]

UNCATEGORIZED_ALIASES = {"", "outros", "sem categoria"}


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


def _normalize_tipo_column(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    derived_tipo = normalized["Valor"].apply(
        lambda value: "Entrada" if float(value) >= 0 else "Saída"
    )
    if "Tipo" not in normalized.columns:
        normalized["Tipo"] = derived_tipo
        return normalized

    current_tipo = normalized["Tipo"].fillna("").astype(str).str.strip()
    invalid_mask = ~current_tipo.isin(["Entrada", "Saída"])
    normalized["Tipo"] = current_tipo.where(~invalid_mask, derived_tipo)
    return normalized


def _apply_local_filters(
    df: pd.DataFrame,
    *,
    query: str,
    types: list[str],
    categories: list[str],
    sources: list[str],
    min_abs_value: float,
    max_abs_value: float,
    uncategorized_only: bool,
    sort_option: str,
) -> pd.DataFrame:
    scoped = df.copy()
    if query.strip():
        scoped = scoped[
            scoped["Descrição"]
            .fillna("")
            .astype(str)
            .str.contains(query.strip(), case=False, regex=False)
        ]

    if types:
        scoped = scoped[scoped["Tipo"].isin(types)]
    else:
        scoped = scoped.iloc[0:0]

    if categories:
        scoped = scoped[scoped["Categoria"].map(_format_category).isin(categories)]
    else:
        scoped = scoped.iloc[0:0]

    if sources:
        scoped = scoped[scoped["Fonte"].isin(sources)]
    else:
        scoped = scoped.iloc[0:0]

    scoped = scoped[
        (scoped["Valor"].abs() >= min_abs_value)
        & (scoped["Valor"].abs() <= max_abs_value)
    ]

    if uncategorized_only:
        normalized_categories = (
            scoped["Categoria"].map(_format_category).str.casefold()
        )
        scoped = scoped[normalized_categories.isin(UNCATEGORIZED_ALIASES)]

    if sort_option == "Data (mais recente)":
        return scoped.sort_values("Data", ascending=False)
    if sort_option == "Data (mais antiga)":
        return scoped.sort_values("Data", ascending=True)
    if sort_option == "Maior valor absoluto":
        return scoped.sort_values("Valor", key=lambda values: values.abs(), ascending=False)
    if sort_option == "Menor valor absoluto":
        return scoped.sort_values("Valor", key=lambda values: values.abs(), ascending=True)
    if sort_option == "Maior valor":
        return scoped.sort_values("Valor", ascending=False)
    if sort_option == "Menor valor":
        return scoped.sort_values("Valor", ascending=True)
    if sort_option == "Descrição (Z-A)":
        return scoped.sort_values(
            "Descrição",
            key=lambda values: values.fillna("").astype(str).str.casefold(),
            ascending=False,
        )
    return scoped.sort_values(
        "Descrição",
        key=lambda values: values.fillna("").astype(str).str.casefold(),
        ascending=True,
    )


def _format_category(value: object) -> str:
    if value is None or value is pd.NA or value is pd.NaT:
        return "Sem categoria"
    if isinstance(value, Real) and math.isnan(float(value)):
        return "Sem categoria"
    text = str(value).strip()
    return text or "Sem categoria"


def _top_expense_line(
    df: pd.DataFrame,
    category_icons: dict[str, str],
    formatter: Callable[[float], str],
) -> str:
    expenses = df[df["Valor"] < 0]
    if expenses.empty:
        return "Sem saídas no recorte selecionado."

    by_category = (
        expenses.groupby("Categoria", dropna=False)["Valor"]
        .sum()
        .abs()
        .sort_values(ascending=False)
        .head(3)
    )
    parts: list[str] = []
    for category, total in by_category.items():
        category_name = _format_category(category)
        icon = category_icons.get(category_name, "📌")
        parts.append(f"{icon} {category_name}: {formatter(float(total))}")
    return "  •  ".join(parts)


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

    working_df = filtered_df.copy()
    working_df["Data"] = pd.to_datetime(working_df["Data"], errors="coerce")
    working_df["Valor"] = pd.to_numeric(working_df["Valor"], errors="coerce").fillna(0.0)
    working_df = _normalize_tipo_column(working_df)

    st.caption("Filtros locais desta aba para investigar padrões sem alterar os filtros globais.")

    abs_values = working_df["Valor"].abs()
    min_abs = float(abs_values.min()) if not abs_values.empty else 0.0
    max_abs = float(abs_values.max()) if not abs_values.empty else 0.0

    type_options = ["Saída", "Entrada"]
    category_options = sorted(working_df["Categoria"].map(_format_category).unique().tolist())
    source_options = sorted(working_df["Fonte"].dropna().astype(str).unique().tolist())

    col_filter1, col_filter2 = st.columns([2, 1])
    with col_filter1:
        query = st.text_input(
            "Buscar na descrição",
            placeholder="Ex.: ifood, aluguel, uber...",
        )
    with col_filter2:
        sort_option = st.selectbox("Ordenar por", SORT_OPTIONS, index=0)

    col_filter3, col_filter4, col_filter5 = st.columns(3)
    with col_filter3:
        selected_types = st.multiselect("Tipo", type_options, default=type_options)
    with col_filter4:
        selected_categories = st.multiselect(
            "Categoria",
            category_options,
            default=category_options,
        )
    with col_filter5:
        selected_sources = st.multiselect("Fonte", source_options, default=source_options)

    col_filter6, col_filter7 = st.columns([3, 1])
    with col_filter6:
        if max_abs > min_abs:
            slider_step = max((max_abs - min_abs) / 200, 0.01)
            min_value, max_value = st.slider(
                "Faixa de valor absoluto (R$)",
                min_value=min_abs,
                max_value=max_abs,
                value=(min_abs, max_abs),
                step=slider_step,
            )
        else:
            st.caption(f"Valor absoluto único no recorte: {formatter(max_abs)}")
            min_value, max_value = min_abs, max_abs
    with col_filter7:
        uncategorized_only = st.checkbox("Só não categorizadas", value=False)

    observed_df = _apply_local_filters(
        working_df,
        query=query,
        types=selected_types,
        categories=selected_categories,
        sources=selected_sources,
        min_abs_value=min_value,
        max_abs_value=max_value,
        uncategorized_only=uncategorized_only,
        sort_option=sort_option,
    )

    total_count = len(working_df)
    displayed_count = len(observed_df)
    entries = observed_df[observed_df["Valor"] >= 0]["Valor"]
    exits = observed_df[observed_df["Valor"] < 0]["Valor"]
    net = float(observed_df["Valor"].sum()) if displayed_count else 0.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        ratio = (displayed_count / total_count) if total_count else 0.0
        st.metric("Registros exibidos", displayed_count, delta=f"{ratio:.0%} do recorte")
    with kpi2:
        st.metric("Entradas", formatter(float(entries.sum())), delta=f"{len(entries)} lanç.")
    with kpi3:
        st.metric("Saídas", formatter(abs(float(exits.sum()))), delta=f"{len(exits)} lanç.")
    with kpi4:
        st.metric("Saldo final estimado", formatter(net))

    st.caption(
        "Top categorias de saída: "
        + _top_expense_line(observed_df, category_icons, formatter)
    )

    if observed_df.empty:
        st.warning("Nenhuma transação atende aos filtros locais atuais.")
        return

    # Build display DataFrame preserving original index for mapping back
    display_df = observed_df[["Data", "Descrição", "Tipo", "Valor", "Categoria", "Fonte"]].copy()

    editor_key = f"tx_editor_{st.session_state.get('tx_editor_v', 0)}"

    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        height=600,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", disabled=True),
            "Descrição": st.column_config.TextColumn("Descrição", disabled=True, width="large"),
            "Tipo": st.column_config.TextColumn("Tipo", disabled=True, width="small"),
            "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f", disabled=True),
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
        changed_indices = edited_df.index[
            edited_df["Categoria"].fillna("") != display_df["Categoria"].fillna("")
        ]
        if len(changed_indices) > 0:
            idx = changed_indices[0]
            st.session_state.pending_cat_change = {
                "index": idx,
                "description": observed_df.at[idx, "Descrição"],
                "old_category": _format_category(display_df.at[idx, "Categoria"]),
                "new_category": _format_category(edited_df.at[idx, "Categoria"]),
            }
            st.rerun()

    st.markdown(f"**{len(display_df)} transações** exibidas")

    st.divider()
    col_exp1, col_exp2, _ = st.columns([1, 1, 3])
    with col_exp1:
        csv = finance_service.build_csv_export(observed_df)
        st.download_button("📥 Exportar CSV", csv, "transacoes.csv", "text/csv")
    with col_exp2:
        excel = finance_service.build_excel_export(observed_df)
        st.download_button(
            "📥 Exportar Excel",
            excel,
            "transacoes.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
