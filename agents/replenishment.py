
from decimal import Decimal

import pandas as pd

from utils.calculations import (
    money,
    target_stock,
    suggested_order_quantity,
)


RISK_PRIORITY = {
    "OUT OF STOCK": 0,
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4,
}


class ReplenishmentAgent:
    """Creates a purchase plan under a fixed procurement budget."""

    def run(
        self,
        analysis: pd.DataFrame,
        budget: float | str | Decimal,
    ) -> pd.DataFrame:
        if not isinstance(analysis, pd.DataFrame):
            raise TypeError("Analysis must be a pandas DataFrame.")

        budget = money(budget)

        # Match the column names used by the project.
        working = analysis.copy()

        if "product_name" not in working.columns and "name" in working.columns:
            working["product_name"] = working["name"]

        if (
            "supplier_lead_time_days" not in working.columns
            and "lead_time_days" in working.columns
        ):
            working["supplier_lead_time_days"] = working["lead_time_days"]

        required = {
            "product_id",
            "current_stock",
            "daily_demand",
            "supplier_lead_time_days",
            "safety_stock",
            "target_coverage_days",
            "minimum_order_quantity",
            "unit_cost",
            "risk_level",
        }

        missing = required - set(working.columns)
        if missing:
            raise ValueError(
                "Analysis is missing required columns: "
                + ", ".join(sorted(missing))
            )

        if working["product_id"].duplicated().any():
            raise ValueError("Product IDs must be unique.")

        rows = []

        for _, row in working.iterrows():
            stock = int(row["current_stock"])
            demand = float(row["daily_demand"])
            lead_time = int(row["supplier_lead_time_days"])
            safety_stock = int(row["safety_stock"])
            coverage = float(row["target_coverage_days"])
            minimum_order = int(row["minimum_order_quantity"])
            unit_cost = money(row["unit_cost"])

            # Target stock = daily demand × (lead time + target coverage).
            target = target_stock(demand, lead_time, coverage)

            # Safety stock is included in the reorder point, not added again
            # to the target stock.
            reorder_point_value = demand * lead_time + safety_stock

            # Use positional arguments to match the project's function.
            suggested_qty = int(
                suggested_order_quantity(stock, target, minimum_order)
            )

            proposed_cost = money(Decimal(suggested_qty) * unit_cost)

            rows.append(
                {
                    **row.to_dict(),
                    "product_name": row.get(
                        "product_name",
                        row.get("name", str(row["product_id"])),
                    ),
                    "target_stock": target,
                    "reorder_point": reorder_point_value,
                    "suggested_quantity": suggested_qty,
                    "proposed_cost": proposed_cost,
                    "priority_rank": RISK_PRIORITY.get(
                        str(row["risk_level"]).upper(), 5
                    ),
                    # Initialize these for every row to prevent NaN values.
                    "approved_quantity": 0,
                    "approved_cost": Decimal("0.00"),
                    "allocation_status": (
                        "NOT REQUIRED"
                        if suggested_qty == 0
                        else "DEFERRED - BUDGET"
                    ),
                }
            )

        if not rows:
            return pd.DataFrame(
                columns=[
                    "product_id",
                    "suggested_quantity",
                    "proposed_cost",
                    "approved_quantity",
                    "approved_cost",
                    "allocation_status",
                ]
            )

        plan = pd.DataFrame(rows)

        # Highest-risk products are allocated budget first.
        plan = plan.sort_values(
            ["priority_rank", "current_stock", "product_id"],
            ascending=[True, True, True],
            kind="stable",
        ).reset_index(drop=True)

        remaining_budget = budget

        for index, row in plan.iterrows():
            suggested_qty = int(row["suggested_quantity"])
            unit_cost = money(row["unit_cost"])
            minimum_order = int(row["minimum_order_quantity"])

            if suggested_qty <= 0:
                plan.at[index, "allocation_status"] = "NOT REQUIRED"
                continue

            if unit_cost == Decimal("0.00"):
                approved_qty = suggested_qty
            else:
                affordable_qty = int(remaining_budget // unit_cost)
                approved_qty = min(suggested_qty, affordable_qty)

                # Never approve an order smaller than the supplier MOQ.
                if approved_qty < minimum_order:
                    approved_qty = 0

            approved_cost = money(Decimal(approved_qty) * unit_cost)

            # Final budget guard.
            if approved_cost > remaining_budget:
                approved_qty = 0
                approved_cost = Decimal("0.00")

            plan.at[index, "approved_quantity"] = approved_qty
            plan.at[index, "approved_cost"] = approved_cost

            if approved_qty == 0:
                status = "DEFERRED - BUDGET"
            elif approved_qty < suggested_qty:
                status = "PARTIALLY APPROVED"
            else:
                status = "APPROVED"

            plan.at[index, "allocation_status"] = status
            remaining_budget -= approved_cost

        plan["approved_quantity"] = plan["approved_quantity"].astype(int)
        plan["approved_cost"] = plan["approved_cost"].apply(money)
        plan["proposed_cost"] = plan["proposed_cost"].apply(money)
        plan["budget"] = budget

        return plan.reset_index(drop=True)
