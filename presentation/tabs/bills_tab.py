from collections.abc import Callable
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.bills_service import BillsService
from presentation.components import section_header


def render_bills_tab(bills_service: BillsService, formatter: Callable[[float], str]) -> None:
    section_header("💳 Faturas do Cartão de Crédito")

    if "cc_info" not in st.session_state:
        cache = bills_service.load_cached_cards()
        if cache:
            st.session_state.cc_info = cache["cards"]
            st.session_state.cc_info_updated = cache["updated_at"]

    if st.button("🔄 Atualizar Faturas", use_container_width=True, key="fetch_bills"):
        try:
            with st.spinner("Consultando faturas no Pluggy..."):
                cc_info = bills_service.fetch_cards()
                st.session_state.cc_info = cc_info
                st.session_state.cc_info_updated = datetime.now().isoformat()

            if not cc_info:
                st.warning("Nenhuma conta de cartão de crédito encontrada.")
            else:
                st.success("Faturas atualizadas!")
                st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001 - errors are surfaced in UI
            st.error(f"Erro ao buscar faturas: {exc}")

    if "cc_info_updated" in st.session_state:
        try:
            updated_dt = pd.to_datetime(st.session_state.cc_info_updated).strftime("%d/%m/%Y %H:%M")
        except Exception:  # noqa: BLE001 - fallback display
            updated_dt = st.session_state.cc_info_updated
        st.caption(f"Última atualização: {updated_dt}")

    if "cc_info" not in st.session_state or not st.session_state.cc_info:
        return

    for cc in st.session_state.cc_info:
        st.markdown(f"### 🏦 {cc['banco']} — {cc['account_name']}")

        col_l1, col_l2 = st.columns(2)
        with col_l1:
            if cc["credit_limit"]:
                st.markdown(
                    '<div class="metric-card"><div class="metric-label">Limite Total</div>'
                    f'<div class="metric-value metric-blue">{formatter(cc["credit_limit"])}</div></div>',
                    unsafe_allow_html=True,
                )
        with col_l2:
            if cc["available_limit"]:
                st.markdown(
                    '<div class="metric-card"><div class="metric-label">Limite Disponível</div>'
                    f'<div class="metric-value metric-green">{formatter(cc["available_limit"])}</div></div>',
                    unsafe_allow_html=True,
                )

        if cc["credit_limit"] and cc["available_limit"]:
            used = cc["credit_limit"] - cc["available_limit"]
            used_pct = used / cc["credit_limit"] * 100 if cc["credit_limit"] > 0 else 0
            st.markdown(f"**Utilizado:** {formatter(used)} ({used_pct:.1f}%)")

        if cc["bills"]:
            # --- Evolução mensal (todas as faturas disponíveis) ---
            monthly_data: dict[str, float] = {}
            for bill in cc["bills"]:
                try:
                    bill_date = pd.to_datetime(bill.get("dueDate"))
                    if bill_date.tz is not None:
                        bill_date = bill_date.tz_localize(None)
                    month_key = bill_date.strftime("%Y-%m")
                    monthly_data[month_key] = monthly_data.get(month_key, 0) + bill.get("totalAmount", 0)
                except Exception:  # noqa: BLE001
                    pass

            if monthly_data:
                sorted_months = sorted(monthly_data.keys())
                labels = [datetime.strptime(m, "%Y-%m").strftime("%b/%Y") for m in sorted_months]
                values = [monthly_data[m] for m in sorted_months]

                fig = go.Figure(go.Bar(
                    x=labels,
                    y=values,
                    text=[formatter(v) for v in values],
                    textposition="outside",
                    marker_color="#636EFA",
                ))
                fig.update_layout(
                    title="Evolução Mensal da Fatura",
                    xaxis_title="Mês",
                    yaxis_title="Valor (R$)",
                    height=350,
                    margin=dict(t=40, b=40),
                )
                st.plotly_chart(fig, use_container_width=True)

            # --- Lista de faturas recentes ---
            cutoff = datetime.now() - timedelta(days=35)
            recent_bills = []
            for bill in cc["bills"]:
                try:
                    bill_date = pd.to_datetime(bill.get("dueDate"))
                    if bill_date.tz is not None:
                        bill_date = bill_date.tz_localize(None)
                    if bill_date >= cutoff:
                        recent_bills.append(bill)
                except Exception:  # noqa: BLE001 - keep row if date parsing fails
                    recent_bills.append(bill)

            st.markdown(
                f"**Faturas** (último mês — {len(recent_bills)} de {len(cc['bills'])} total):"
            )
            for bill in recent_bills:
                due = bill.get("dueDate", "—")
                total = bill.get("totalAmount", 0)
                minimum = bill.get("minimumPaymentAmount")
                status = bill.get("status", "")

                if due != "—":
                    try:
                        due_fmt = pd.to_datetime(due).strftime("%d/%m/%Y")
                    except Exception:  # noqa: BLE001 - fallback display
                        due_fmt = due
                else:
                    due_fmt = due

                status_emoji = {"OPEN": "🟡", "CLOSED": "🔴", "FUTURE": "🔵"}.get(status, "⚪")
                with st.container():
                    bc1, bc2, bc3 = st.columns([2, 2, 1])
                    with bc1:
                        st.markdown(f"{status_emoji} **Vencimento:** {due_fmt}")
                    with bc2:
                        st.markdown(f"**Total:** {formatter(total)}")
                    with bc3:
                        if minimum is not None:
                            st.markdown(f"**Mín:** {formatter(minimum)}")

                charges = bill.get("financeCharges", [])
                if charges:
                    for charge in charges:
                        ch_type = charge.get("type", "").replace("_", " ").title()
                        ch_amount = charge.get("amount", 0)
                        st.caption(f"  ↳ {ch_type}: {formatter(ch_amount)}")
        else:
            st.info(
                "Nenhuma fatura disponível para este cartão. "
                "Este endpoint pode não ser suportado pela sua instituição via conexão direta."
            )

        st.divider()
