from collections.abc import Callable

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services.finance_service import FinanceService
from presentation.components import section_header


def render_dashboard_tab(
    filtered_df,
    finance_service: FinanceService,
    category_icons: dict[str, str],
    formatter: Callable[[float], str],
) -> None:
    col_left, col_right = st.columns([3, 2])

    with col_left:
        section_header("Gastos por Categoria")
        cat_summary = finance_service.get_summary_by_category(filtered_df)
        if not cat_summary.empty:
            cat_summary["Label"] = cat_summary["Categoria"].map(
                lambda c: f"{category_icons.get(c, '📌')} {c}"
            )
            fig_cat = px.bar(
                cat_summary,
                x="Total",
                y="Label",
                orientation="h",
                color="Total",
                color_continuous_scale=["#fecaca", "#dc2626"],
                text=cat_summary["Total"].apply(formatter),
            )
            fig_cat.update_layout(
                yaxis=dict(categoryorder="total ascending", title=""),
                xaxis=dict(title="", showticklabels=False),
                coloraxis_showscale=False,
                margin=dict(l=0, r=20, t=10, b=10),
                height=max(300, len(cat_summary) * 40),
                font=dict(family="DM Sans"),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            fig_cat.update_traces(textposition="outside")
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Nenhum gasto encontrado para os filtros selecionados.")

    with col_right:
        section_header("Distribuição")
        if not cat_summary.empty:
            total_gasto = cat_summary["Total"].sum()
            pie_labels = cat_summary["Categoria"].map(
                lambda c: f"{category_icons.get(c, '📌')} {c}"
            )
            _PALETTE = [
                "#6366f1", "#f59e0b", "#10b981", "#ef4444", "#3b82f6",
                "#8b5cf6", "#ec4899", "#14b8a6", "#f97316", "#84cc16",
                "#06b6d4", "#a855f7",
            ]
            fig_pie = px.pie(
                cat_summary,
                values="Total",
                names=pie_labels,
                color_discrete_sequence=_PALETTE,
                hole=0.52,
            )
            fig_pie.update_traces(
                textposition="inside",
                textinfo="percent",
                texttemplate="<b>%{percent:.0%}</b>",
                insidetextfont=dict(size=14, family="DM Sans", color="white"),
                hovertemplate="<b>%{label}</b><br>%{customdata}<br>%{percent:.1%}<extra></extra>",
                customdata=cat_summary["Total"].apply(formatter),
            )
            fig_pie.update_layout(
                margin=dict(l=0, r=0, t=10, b=10),
                height=380,
                font=dict(family="DM Sans", size=11),
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(font=dict(size=10), orientation="v"),
                annotations=[dict(
                    text=f"<b>{formatter(total_gasto)}</b><br>total",
                    x=0.5, y=0.5,
                    font=dict(size=13, family="DM Sans"),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    section_header("Gastos Diários")
    daily = finance_service.get_daily_expenses(filtered_df)
    if not daily.empty:
        fig_daily = go.Figure()
        fig_daily.add_trace(
            go.Bar(
                x=daily["Data"],
                y=daily["Total"],
                marker=dict(
                    color=daily["Total"],
                    colorscale=[[0, "#93c5fd"], [0.5, "#f59e0b"], [1, "#dc2626"]],
                ),
                text=daily["Total"].apply(formatter),
                textposition="outside",
                hovertemplate="%{x}<br>%{text}<extra></extra>",
            )
        )
        fig_daily.update_layout(
            xaxis=dict(title="", tickformat="%d/%m"),
            yaxis=dict(title="", showticklabels=False),
            margin=dict(l=0, r=0, t=10, b=10),
            height=300,
            font=dict(family="DM Sans"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig_daily, use_container_width=True)

    section_header("Por Banco / Fonte")
    fonte_summary = finance_service.get_summary_by_fonte(filtered_df)
    if not fonte_summary.empty:
        fig_fonte = go.Figure()
        fig_fonte.add_trace(
            go.Bar(
                name="Entradas",
                x=fonte_summary["Fonte"],
                y=fonte_summary["Entradas"],
                marker_color="#059669",
                text=fonte_summary["Entradas"].apply(formatter),
                textposition="outside",
            )
        )
        fig_fonte.add_trace(
            go.Bar(
                name="Saídas",
                x=fonte_summary["Fonte"],
                y=fonte_summary["Saídas"],
                marker_color="#dc2626",
                text=fonte_summary["Saídas"].apply(formatter),
                textposition="outside",
            )
        )
        fig_fonte.update_layout(
            barmode="group",
            yaxis=dict(title="", showticklabels=False),
            xaxis=dict(title=""),
            margin=dict(l=0, r=0, t=10, b=10),
            height=320,
            font=dict(family="DM Sans"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_fonte, use_container_width=True)
