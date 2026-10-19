
"""Deterministic inventory and purchasing calculations."""

from decimal import Decimal, ROUND_HALF_UP
import math


def average_daily_demand(units_sold: float, period_days: int) -> float:
    """Calculate average units sold per day."""
    if period_days <= 0:
        raise ValueError("Sales period must be greater than zero.")
    if not math.isfinite(units_sold) or units_sold < 0:
        raise ValueError("Units sold must be finite and non-negative.")
    return units_sold / period_days


def days_of_stock(current_stock: float, daily_demand: float) -> float:
    """Return stock coverage in days; infinity means zero demand."""
    if not math.isfinite(current_stock) or current_stock < 0:
        raise ValueError("Current stock must be finite and non-negative.")
    if not math.isfinite(daily_demand) or daily_demand < 0:
        raise ValueError("Daily demand must be finite and non-negative.")
    if daily_demand == 0:
        return math.inf
    return current_stock / daily_demand


def reorder_point(
    daily_demand: float,
    lead_time_days: int,
    safety_stock: float,
) -> float:
    """Demand during lead time plus safety stock."""
    if daily_demand < 0 or lead_time_days < 0 or safety_stock < 0:
        raise ValueError("Demand, lead time and safety stock cannot be negative.")
    if not all(math.isfinite(v) for v in (daily_demand, safety_stock)):
        raise ValueError("Demand and safety stock must be finite.")
    return daily_demand * lead_time_days + safety_stock


def target_stock(
    daily_demand: float,
    lead_time_days: int,
    target_coverage_days: float,
) -> float:
    """Target stock covers lead time plus additional coverage.

    Safety stock is included in the reorder-point policy, not added again
    here. This avoids double-counting safety stock in the target calculation.
    """
    values = (daily_demand, target_coverage_days)
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Demand and coverage must be finite.")
    if daily_demand < 0 or lead_time_days < 0 or target_coverage_days < 0:
        raise ValueError("Demand and coverage inputs cannot be negative.")
    return daily_demand * (lead_time_days + target_coverage_days)


def suggested_order_quantity(
    current_stock: float,
    target: float,
    minimum_order_quantity: int = 0,
) -> int:
    """Return whole units needed to reach target, respecting an MOQ."""
    if current_stock < 0 or target < 0:
        raise ValueError("Stock and target cannot be negative.")
    if not math.isfinite(current_stock) or not math.isfinite(target):
        raise ValueError("Stock and target must be finite.")
    if minimum_order_quantity < 0:
        raise ValueError("Minimum order quantity cannot be negative.")

    deficit = max(0.0, target - current_stock)
    quantity = math.ceil(deficit)

    if quantity == 0:
        return 0

    if minimum_order_quantity:
        quantity = max(quantity, minimum_order_quantity)

    return quantity


def money(value: float | str | Decimal) -> Decimal:
    """Convert a non-negative monetary amount to two decimal places."""
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0:
        raise ValueError("Money must be finite and non-negative.")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def line_item_cost(quantity: int, unit_cost: float | str | Decimal) -> Decimal:
    """Calculate the purchase cost for one product."""
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
        raise ValueError("Quantity must be a non-negative integer.")
    return money(Decimal(quantity) * Decimal(str(unit_cost)))
