
"""Inventory Analyst Agent: evaluates product-level inventory risk."""

import math
import pandas as pd

from utils.calculations import (
    average_daily_demand,
    days_of_stock,
    reorder_point,
)
from utils.validation import validate_inventory


class InventoryAnalystAgent:
    """Analyzes demand, stock cover, reorder points and estimated risk."""

    name = "Inventory Analyst Agent"

    def run(self, inventory: pd.DataFrame) -> pd.DataFrame:
        errors = validate_inventory(inventory)
        if errors:
            raise ValueError("Invalid inventory data: " + "; ".join(errors))

        result = inventory.copy()
        result["daily_demand"] = result.apply(
            lambda r: average_daily_demand(
                float(r["units_sold"]), int(r["sales_period_days"])
            ),
            axis=1,
        )

        result["days_remaining"] = result.apply(
            lambda r: days_of_stock(
                float(r["current_stock"]), float(r["daily_demand"])
            ),
            axis=1,
        )

        result["reorder_point"] = result.apply(
            lambda r: reorder_point(
                float(r["daily_demand"]),
                int(r["supplier_lead_time_days"]),
                float(r["safety_stock"]),
            ),
            axis=1,
        )

        def classify(row) -> str:
            stock = float(row["current_stock"])
            demand = float(row["daily_demand"])
            cover = float(row["days_remaining"])
            lead = int(row["supplier_lead_time_days"])
            point = float(row["reorder_point"])

            if stock <= 0 and demand > 0:
                return "OUT OF STOCK"
            if demand > 0 and cover < lead:
                return "CRITICAL"
            if stock <= point:
                return "HIGH"
            if demand > 0 and cover <= lead + 2:
                return "MEDIUM"
            return "LOW"

        result["risk_level"] = result.apply(classify, axis=1)

        def explain(row) -> str:
            risk = row["risk_level"]
            if risk == "OUT OF STOCK":
                return "No units are available while recent demand is positive."
            if risk == "CRITICAL":
                return (
                    f"Estimated stock cover ({row['days_remaining']:.1f} days) "
                    f"is shorter than supplier lead time "
                    f"({row['supplier_lead_time_days']} days)."
                )
            if risk == "HIGH":
                return "Current stock is at or below the calculated reorder point."
            if risk == "MEDIUM":
                return "Stock cover is approaching the supplier lead-time window."
            if row["daily_demand"] == 0:
                return "No recent demand; review before replenishing."
            return "Current inventory is above the defined risk thresholds."

        result["risk_explanation"] = result.apply(explain, axis=1)

        # Infinity is valid for internal zero-demand handling. The UI can
        # display it as "No recent demand" instead of a numeric infinity.
        result["days_remaining"] = result["days_remaining"].map(
            lambda x: x if math.isfinite(x) else math.inf
        )
        return result
