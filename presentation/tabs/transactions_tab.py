from collections.abc import Callable
import math
from numbers import Real
from typing import cast

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
ALL_CATEGORIES_OPTION = "__ALL_CATEGORIES__"


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
            st.session_state.df.at[idx, "categoria_manual"] = True
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
    category_counts = cast(
        dict[str, int],
        working_df["Categoria"]
        .map(_format_category)
        .value_counts()
        .to_dict(),
    )
    category_options = sorted(
        category_counts.keys(),
        key=lambda name: (-category_counts.get(name, 0), name.casefold()),
    )
    source_options = sorted(working_df["Fonte"].dropna().astype(str).unique().tolist())

    category_filter_key = "tx_filter_categories"
    category_widget_options = [ALL_CATEGORIES_OPTION, *category_options]
    previous_selected_categories = st.session_state.get(category_filter_key)
    if previous_selected_categories is None:
        st.session_state[category_filter_key] = [ALL_CATEGORIES_OPTION]
    else:
        selected = [
            category
            for category in previous_selected_categories
            if category in category_widget_options
        ]
        if not selected:
            selected = [ALL_CATEGORIES_OPTION]
        st.session_state[category_filter_key] = selected

    col_filter1, col_filter2 = st.columns([2, 1])
    with col_filter1:
        query = st.text_input(
            "Buscar na descrição",
            placeholder="Ex.: ifood, aluguel, uber...",
        )
    with col_filter2:
        sort_option = st.selectbox("Ordenar por", SORT_OPTIONS, index=0)

    col_filter3, col_filter4, col_filter5 = st.columns([1, 2, 1])
    with col_filter3:
        selected_types = st.multiselect("Tipo", type_options, default=type_options)
    with col_filter4:
        category_selection_raw = st.multiselect(
            "Categoria",
            category_widget_options,
            key=category_filter_key,
            placeholder="Digite para buscar categorias...",
            format_func=lambda category: (
                "Todas as categorias"
                if category == ALL_CATEGORIES_OPTION
                else (
                    f"{category_icons.get(category, '📌')} "
                    f"{category} ({category_counts.get(category, 0)})"
                )
            ),
            help=(
                "Use a busca do seletor para encontrar categorias rapidamente. "
                "O número entre parênteses mostra quantas transações há no recorte."
            ),
        )
        selected_categories = [
            str(category)
            for category in category_selection_raw
        ]
        all_selected = (
            not selected_categories
            or ALL_CATEGORIES_OPTION in selected_categories
        )
        selected_count = len(category_options) if all_selected else len(selected_categories)
        st.caption(f"Categorias selecionadas: {selected_count} de {len(category_options)}")

        categories_to_filter: list[str] = category_options if all_selected else selected_categories
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
        categories=categories_to_filter,
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

    # Build display DataFrame; save original index mapping before reset
    display_df = observed_df[["Data", "Descrição", "Tipo", "Valor", "Categoria", "Fonte", "categoria_manual"]].copy()
    display_df["🔒"] = display_df["categoria_manual"].astype(bool)
    display_df = display_df.drop(columns=["categoria_manual"])
    display_df["🗑"] = False
    orig_index = display_df.index.tolist()  # positional → st.session_state.df index
    display_df = display_df.reset_index(drop=True)

    editor_key = f"tx_editor_{st.session_state.get('tx_editor_v', 0)}"

    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        height=600,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "Descrição": st.column_config.TextColumn("Descrição", width="large"),
            "Tipo": st.column_config.SelectboxColumn(
                "Tipo",
                options=["Entrada", "Saída"],
                width="small",
            ),
            "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            "Categoria": st.column_config.SelectboxColumn(
                "Categoria",
                options=categories,
                required=True,
            ),
            "Fonte": st.column_config.TextColumn("Fonte", disabled=True),
            "🔒": st.column_config.CheckboxColumn(
                "🔒",
                help="Proteger categoria da reclassificação automática",
            ),
            "🗑": st.column_config.CheckboxColumn(
                "🗑",
                help="Marcar para deletar — salvo ao marcar",
            ),
        },
        key=editor_key,
    )

    # Detect edits (only if no pending dialog)
    if "pending_cat_change" not in st.session_state:
        edited_view = edited_df
        display_view = display_df

        # Deletion via 🗑 checkbox
        to_delete_mask = edited_view["🗑"].astype(bool)
        if to_delete_mask.any():
            deleted_orig = [orig_index[i] for i in edited_view.index[to_delete_mask]]
            st.session_state.df = (
                st.session_state.df.drop(index=deleted_orig).reset_index(drop=True)
            )
            finance_service.save_dataframe(st.session_state.df)
            st.session_state.tx_editor_v = st.session_state.get("tx_editor_v", 0) + 1
            st.rerun()

        # Category change → dialog
        changed_cat_mask = (
            edited_view["Categoria"].fillna("") != display_view["Categoria"].fillna("")
        )
        if changed_cat_mask.any():
            pos = edited_view.index[changed_cat_mask][0]
            orig_idx = orig_index[pos]
            st.session_state.pending_cat_change = {
                "index": orig_idx,
                "description": observed_df.at[orig_idx, "Descrição"],
                "old_category": _format_category(display_view.at[pos, "Categoria"]),
                "new_category": _format_category(edited_view.at[pos, "Categoria"]),
            }
            st.rerun()

        # Direct field changes → save immediately
        data_changed = pd.to_datetime(edited_view["Data"], errors="coerce") != pd.to_datetime(display_view["Data"], errors="coerce")
        desc_changed = edited_view["Descrição"].fillna("") != display_view["Descrição"].fillna("")
        tipo_changed = edited_view["Tipo"].fillna("") != display_view["Tipo"].fillna("")
        valor_changed = edited_view["Valor"].round(2) != display_view["Valor"].round(2)
        lock_changed = edited_view["🔒"].astype(bool) != display_view["🔒"].astype(bool)
        any_changed = data_changed | desc_changed | tipo_changed | valor_changed | lock_changed  # 🗑 handled above

        if any_changed.any():
            for pos in edited_view.index[any_changed]:
                orig_idx = orig_index[pos]
                if data_changed.at[pos]:
                    new_data = pd.to_datetime(str(edited_view.at[pos, "Data"]), errors="coerce")
                    if not pd.isna(new_data):
                        st.session_state.df.at[orig_idx, "Data"] = new_data
                if desc_changed.at[pos]:
                    st.session_state.df.at[orig_idx, "Descrição"] = edited_view.at[pos, "Descrição"]
                if tipo_changed.at[pos]:
                    new_tipo = str(edited_view.at[pos, "Tipo"] or "")
                    if new_tipo in ("Entrada", "Saída"):
                        st.session_state.df.at[orig_idx, "Tipo"] = new_tipo
                        current_valor = float(st.session_state.df.at[orig_idx, "Valor"] or 0)
                        if new_tipo == "Entrada" and current_valor < 0:
                            st.session_state.df.at[orig_idx, "Valor"] = abs(current_valor)
                        elif new_tipo == "Saída" and current_valor > 0:
                            st.session_state.df.at[orig_idx, "Valor"] = -abs(current_valor)
                if valor_changed.at[pos]:
                    raw = pd.to_numeric(edited_view.at[pos, "Valor"], errors="coerce")
                    st.session_state.df.at[orig_idx, "Valor"] = 0.0 if pd.isna(raw) else float(raw)
                if lock_changed.at[pos]:
                    st.session_state.df.at[orig_idx, "categoria_manual"] = bool(edited_view.at[pos, "🔒"])
            finance_service.save_dataframe(st.session_state.df)
            st.session_state.tx_editor_v = st.session_state.get("tx_editor_v", 0) + 1
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
