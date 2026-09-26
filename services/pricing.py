from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP


DISCOUNT_RATE = Decimal("0.25")
MONEY_STEP = Decimal("0.01")


def previous_calendar_month(calculation_date: date) -> tuple[date, date]:
    """Return an inclusive start and exclusive end for the previous calendar month."""
    current_month_start = calculation_date.replace(day=1)
    if current_month_start.month == 1:
        previous_start = current_month_start.replace(
            year=current_month_start.year - 1,
            month=12,
        )
    else:
        previous_start = current_month_start.replace(month=current_month_start.month - 1)
    return previous_start, current_month_start


def discounted_price(price: Decimal | int | float | str, had_previous_month_orders: bool) -> Decimal:
    amount = Decimal(str(price))
    if not had_previous_month_orders:
        amount *= Decimal("1") - DISCOUNT_RATE
    return amount.quantize(MONEY_STEP, rounding=ROUND_HALF_UP)
