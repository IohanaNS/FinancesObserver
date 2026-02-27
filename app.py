from application import build_services, initialize_session_dataframe
from core import fmt_brl
from presentation import configure_page, inject_styles, render_theme_switch
from presentation.main_screen import render_main_screen


def main() -> None:
    configure_page()
    render_theme_switch()
    inject_styles()

    finance_service, bills_service = build_services()
    df = initialize_session_dataframe(finance_service)
    render_main_screen(
        finance_service=finance_service,
        bills_service=bills_service,
        df=df,
        formatter=fmt_brl,
    )


if __name__ == "__main__":
    main()
