from collections.abc import Callable
from datetime import datetime

import pandas as pd
import streamlit as st

from presentation.components import section_header
from services.finance_service import FinanceService


def _format_optional_amount(value: float | None, formatter: Callable[[float], str]) -> str:
    if value is None or pd.isna(value):
        return "—"
    return formatter(float(value))


def _format_updated_at(value: str) -> str:
    try:
        return pd.to_datetime(value).strftime("%d/%m/%Y %H:%M")
    except Exception:  # noqa: BLE001 - fallback display
        return value


def _render_goal_progress(total_balance: float, goal: float, formatter: Callable[[float], str]) -> None:
    progress = min(total_balance / goal, 1.0) if goal > 0 else 0.0
    missing = max(goal - total_balance, 0.0) if goal > 0 else 0.0

    st.markdown(
        f"""
        <div style="margin: 16px 0;">
            <div class="goal-bar-bg">
                <div class="goal-bar-fill" style="width: {progress*100:.0f}%">{progress*100:.1f}%</div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:currentColor; opacity:0.8;">
                <span>Investido: {formatter(total_balance)}</span>
                <span>Meta: {formatter(goal)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if goal > 0 and missing > 0:
        st.info(f"Faltam **{formatter(missing)}** para atingir sua meta financeira.")
    elif goal > 0:
        st.success("Meta financeira atingida com seus investimentos atuais.")


def render_investments_tab(
    finance_service: FinanceService,
    formatter: Callable[[float], str],
) -> None:
    section_header("📈 Investimentos")
    st.caption(
        "Acompanha investimentos/caixinhas conectados no Pluggy e o progresso para sua meta financeira."
    )

    if "investments_data" not in st.session_state:
        cache = finance_service.load_cached_investments()
        if cache:
            st.session_state.investments_data = cache.get("investments", [])
            st.session_state.investments_updated = cache.get("updated_at")

    goal = float(st.session_state.get("goal", 15000.0))

    if st.button("🔄 Atualizar Investimentos", use_container_width=True, key="fetch_investments"):
        try:
            with st.spinner("Consultando investimentos no Pluggy..."):
                investments = finance_service.fetch_investments()
            st.session_state.investments_data = investments
            st.session_state.investments_updated = datetime.now().isoformat()

            if not investments:
                st.warning(
                    "Nenhum investimento disponível foi encontrado. "
                    "Verifique se o item possui acesso ao produto de investimentos no Pluggy."
                )
            else:
                st.success("Investimentos atualizados!")
                st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001 - errors are surfaced in UI
            st.error(f"Erro ao buscar investimentos: {exc}")

    if "investments_updated" in st.session_state and st.session_state.investments_updated:
        st.caption(f"Última atualização: {_format_updated_at(st.session_state.investments_updated)}")

    investments = st.session_state.get("investments_data", [])
    if not investments:
        st.warning(
            "A integração Pluggy desta conexão não retornou investimentos no endpoint oficial. "
            "Exibindo estimativa baseada em transações classificadas."
        )
        tx_df = st.session_state.get("df", pd.DataFrame())
        estimated = finance_service.estimate_investments_from_transactions(tx_df)
        if estimated.empty:
            st.info(
                "Sem dados suficientes para estimar investimentos. "
                "Sincronize transações e confirme a categorização em Investimentos/Resgate Investimento."
            )
            return

        total_estimated = float(estimated["Saldo Estimado"].sum())
        st.markdown(
            '<div class="metric-card"><div class="metric-label">📌 Saldo Estimado por Transações</div>'
            f'<div class="metric-value metric-amber">{formatter(total_estimated)}</div></div>',
            unsafe_allow_html=True,
        )
        _render_goal_progress(total_estimated, goal, formatter)

        estimated_display = estimated.copy()
        for column in ["Aportes", "Resgates", "Saldo Estimado"]:
            estimated_display[column] = estimated_display[column].apply(
                lambda value: _format_optional_amount(float(value), formatter)
            )
        st.dataframe(estimated_display, use_container_width=True, hide_index=True)
        return

    total_balance = sum(item["saldo_atual"] for item in investments if item.get("saldo_atual") is not None)
    total_available = sum(
        item["saldo_disponivel"] for item in investments if item.get("saldo_disponivel") is not None
    )

    col_total, col_available = st.columns(2)
    with col_total:
        st.markdown(
            '<div class="metric-card"><div class="metric-label">💼 Patrimônio Investido</div>'
            f'<div class="metric-value metric-blue">{formatter(total_balance)}</div></div>',
            unsafe_allow_html=True,
        )
    with col_available:
        st.markdown(
            '<div class="metric-card"><div class="metric-label">💧 Valor Disponível</div>'
            f'<div class="metric-value metric-green">{formatter(total_available)}</div></div>',
            unsafe_allow_html=True,
        )

    _render_goal_progress(total_balance, goal, formatter)

    raw = pd.DataFrame(investments).rename(
        columns={
            "banco": "Banco",
            "investimento": "Investimento",
            "tipo": "Tipo",
            "subtipo": "Subtipo",
            "saldo_atual": "Saldo Atual",
            "saldo_disponivel": "Saldo Disponível",
            "moeda": "Moeda",
        }
    )

    by_bank = raw.groupby("Banco", as_index=False).agg(
        **{"Saldo Atual": ("Saldo Atual", "sum")}
    )
    by_bank = by_bank.sort_values(by=["Saldo Atual"], ascending=[False])
    if not by_bank.empty:
        st.markdown("**Distribuição por banco**")
        st.bar_chart(by_bank.set_index("Banco"), y="Saldo Atual", use_container_width=True)

    display = raw.copy()
    display["Saldo Atual"] = display["Saldo Atual"].apply(
        lambda value: _format_optional_amount(value, formatter)
    )
    display["Saldo Disponível"] = display["Saldo Disponível"].apply(
        lambda value: _format_optional_amount(value, formatter)
    )

    columns = ["Banco", "Investimento", "Tipo", "Subtipo", "Saldo Atual", "Saldo Disponível", "Moeda"]
    if (display["Subtipo"].fillna("") == "").all():
        columns.remove("Subtipo")
    if (display["Saldo Disponível"] == "—").all():
        columns.remove("Saldo Disponível")

    st.dataframe(display[columns], use_container_width=True, hide_index=True)
