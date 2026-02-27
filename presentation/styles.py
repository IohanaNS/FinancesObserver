import streamlit as st


def configure_page() -> None:
    st.set_page_config(
        page_title="Financeiro",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded",
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

    .goal-bar-bg {
        background: color-mix(in srgb, currentColor 16%, transparent);
        border-radius: 12px; height: 28px; overflow: hidden; margin: 8px 0;
    }
    .goal-bar-fill {
        height: 100%; border-radius: 12px;
        background: linear-gradient(90deg, #059669 0%, #10b981 100%);
        transition: width 0.8s ease; display: flex; align-items: center; justify-content: center;
        color: white; font-weight: 600; font-size: 0.8rem; font-family: 'JetBrains Mono', monospace;
    }

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
</style>
"""
    st.html(css)
