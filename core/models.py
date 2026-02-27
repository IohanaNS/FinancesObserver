from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SidebarState:
    travel_goal: float
    saved_so_far: float
    months_left: int
    date_range: tuple[date, date]
    filter_cats: list[str]
    filter_fontes: list[str]
    sync_from: date
    sync_to: date
    sync_requested: bool


@dataclass(frozen=True)
class FinanceKpis:
    total_income: float
    total_real_expenses: float
    pct_salary: float
    total_invested: float


@dataclass(frozen=True)
class SavingsSimulation:
    monthly_saving: float
    yearly_saving: float
    months_to_goal: float | None
