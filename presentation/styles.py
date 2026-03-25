import streamlit as st


def configure_page() -> None:
    st.set_page_config(
        page_title="Financeiro",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="auto",
    )


def _resolve_initial_theme_mode() -> str:
    base_theme = st.get_option("theme.base")
    if base_theme in {"light", "dark"}:
        return base_theme
    return "light"


def _apply_streamlit_theme(theme_mode: str) -> None:
    current = st.get_option("theme.base")
    if current != theme_mode:
        st._config.set_option("theme.base", theme_mode)
        st.rerun()


def render_theme_switch() -> str:
    if "ui_theme_mode" not in st.session_state:
        st.session_state.ui_theme_mode = _resolve_initial_theme_mode()

    current_mode = st.session_state.ui_theme_mode
    icon = "🌙" if current_mode == "light" else "☀️"

    _, switch_col = st.columns([20, 1])
    with switch_col:
        if st.button(
            icon,
            key="ui_theme_switch",
            help="Alternar tema claro/escuro",
            use_container_width=True,
        ):
            st.session_state.ui_theme_mode = "dark" if current_mode == "light" else "light"

    active_mode = st.session_state.ui_theme_mode
    _apply_streamlit_theme(active_mode)
    return active_mode


def inject_styles() -> None:
    css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,500;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;600&display=swap');

    .main-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--text-color);
        margin-bottom: 0;
    }
    .subtitle {
        font-family: 'DM Sans', sans-serif;
        color: color-mix(in srgb, var(--text-color) 65%, transparent);
        opacity: 0.75;
        font-size: 1rem; margin-top: -8px; margin-bottom: 24px;
    }

    .metric-card {
        background: var(--secondary-background-color);
        border: 1px solid color-mix(in srgb, var(--text-color) 18%, transparent);
        border-radius: 16px;
        padding: 20px 24px; text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.08); }
    .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 600; margin: 4px 0; }
    .metric-label {
        font-size: 0.85rem; font-weight: 500;
        color: color-mix(in srgb, var(--text-color) 65%, transparent);
        opacity: 0.75;
    }
    .metric-green { color: #059669; }
    .metric-red { color: #dc2626; }
    .metric-blue { color: #2563eb; }
    .metric-amber { color: #d97706; }

    .section-header {
        font-size: 1.3rem; font-weight: 700;
        color: var(--text-color) !important;
        margin: 32px 0 16px 0; padding-bottom: 8px;
        border-bottom: 3px solid color-mix(in srgb, var(--text-color) 40%, transparent);
        display: inline-block;
    }

    .rule-chip {
        display: inline-flex; align-items: center; gap: 6px;
        background: var(--secondary-background-color);
        border: 1px solid color-mix(in srgb, var(--text-color) 18%, transparent);
        border-radius: 20px;
        padding: 6px 14px; margin: 4px; font-size: 0.85rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .rule-keyword { font-weight: 600; color: var(--text-color); }
    .rule-arrow { color: color-mix(in srgb, var(--text-color) 50%, transparent); }
    .rule-category { color: var(--text-color); opacity: 0.9; }

    /* ── Mobile responsiveness ── */
    @media screen and (max-width: 768px) {
        /* Compact container padding */
        .main .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-top: 0.5rem !important;
        }

        /* Typography */
        .main-title { font-size: 1.5rem !important; }
        .subtitle { font-size: 0.82rem !important; margin-bottom: 12px !important; }
        .section-header { font-size: 1.05rem !important; margin: 16px 0 10px 0 !important; }

        /* KPI cards */
        .metric-card { padding: 12px 10px !important; border-radius: 12px !important; }
        .metric-value { font-size: 1.1rem !important; }
        .metric-label { font-size: 0.72rem !important; }

        /* Stack all columns vertically */
        [data-testid="stHorizontalBlock"],
        div.stHorizontalBlock {
            flex-wrap: wrap !important;
        }
        [data-testid="stColumn"],
        div.stColumn {
            width: 100% !important;
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }

        /* Bigger touch targets for buttons */
        .stButton > button {
            min-height: 44px !important;
            font-size: 0.95rem !important;
            border-radius: 10px !important;
        }

        /* Theme toggle: keep compact and right-aligned on mobile */
        [data-testid="stHorizontalBlock"]:has(#ui_theme_switch) {
            justify-content: flex-end !important;
        }
        [data-testid="stHorizontalBlock"]:has(#ui_theme_switch) [data-testid="stColumn"] {
            min-width: auto !important;
            flex: 0 0 auto !important;
            width: auto !important;
        }

        /* Larger form inputs */
        .stTextInput input,
        .stNumberInput input {
            min-height: 44px !important;
            font-size: 1rem !important;
        }
        .stSelectbox > div > div {
            min-height: 44px !important;
        }
        .stDateInput input {
            min-height: 44px !important;
            font-size: 1rem !important;
        }

        /* Tabs: horizontally scrollable strip */
        .stTabs [data-baseweb="tab-list"] {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
            flex-wrap: nowrap !important;
            scrollbar-width: none !important;
        }
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none !important; }
        .stTabs [data-baseweb="tab"] {
            white-space: nowrap !important;
            padding: 8px 10px !important;
            font-size: 0.78rem !important;
            min-width: auto !important;
        }

        /* Tables & data editors: horizontal scroll */
        [data-testid="stDataFrame"] > div,
        [data-testid="stDataEditor"] > div {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }
    }
</style>
"""
    st.html(css)
