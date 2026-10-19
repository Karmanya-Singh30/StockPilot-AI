
"""Critic Agent: independently validates replenishment proposals."""

from decimal import Decimal
import pandas as pd

from utils.calculations import (
    line_item_cost,
    money,
    reorder_point,
    target_stock,
)


class CriticAgent:
    """Recomputes key figures and checks the approved plan."""

    name = "Critic / Validation Agent"

    def run(
        self,
        inventory: pd.DataFrame,
        analysis: pd.DataFrame,
        plan: pd.DataFrame,
        budget: float | str | Decimal,
    ) -> dict:
        budget_amount = money(budget)
        errors: list[str] = []
        warnings: list[str] = []
        passed: list[str] = []

        if plan.empty:
            return {
                "status": "PASS",
                "passed": ["Empty purchase plan is valid."],
                "warnings": [],
                "errors": [],
                "total_approved_cost": Decimal("0.00"),
            }

        if plan["product_id"].duplicated().any():
            errors.append("Purchase plan contains duplicate product IDs.")
        else:
            passed.append("Product IDs are unique.")

        source = inventory.set_index("product_id", drop=False)
        analyzed = analysis.set_index("product_id", drop=False)

        for _, row in plan.iterrows():
            product_id = row["product_id"]

            if product_id not in source.index or product_id not in analyzed.index:
                errors.append(f"{product_id}: product missing from source or analysis.")
                continue

            original = source.loc[product_id]
            analytic = analyzed.loc[product_id]

            quantity = row["approved_quantity"]
            if pd.isna(quantity) or float(quantity) < 0 or float(quantity) != int(quantity):
                errors.append(f"{product_id}: invalid approved quantity.")
                continue
            quantity = int(quantity)

            unit_cost = money(original["unit_cost"])
            if unit_cost < 0:
                errors.append(f"{product_id}: negative unit cost.")
                continue

            expected_reorder = reorder_point(
                float(analytic["daily_demand"]),
                int(original["supplier_lead_time_days"]),
                float(original["safety_stock"]),
            )
            if abs(float(row["reorder_point"]) - expected_reorder) > 1e-8:
                errors.append(f"{product_id}: reorder point mismatch.")

            expected_target = target_stock(
                float(analytic["daily_demand"]),
                int(original["supplier_lead_time_days"]),
                float(original["target_coverage_days"]),
            )
            if abs(float(row["target_stock"]) - expected_target) > 1e-8:
                errors.append(f"{product_id}: target stock mismatch.")

            expected_cost = line_item_cost(quantity, unit_cost)
            actual_cost = money(row["approved_cost"])

            if expected_cost != actual_cost:
                errors.append(
                    f"{product_id}: approved cost mismatch "
                    f"(expected {expected_cost}, found {actual_cost})."
                )

            moq = int(original["minimum_order_quantity"])
            if 0 < quantity < moq:
                errors.append(f"{product_id}: approved quantity is below MOQ.")

            if quantity > 0 and quantity < int(row["suggested_quantity"]):
                warnings.append(
                    f"{product_id}: approved quantity is lower than suggested."
                )

        total = sum(plan["approved_cost"].apply(money), Decimal("0.00"))

        if total > budget_amount:
            errors.append(
                f"Budget exceeded: approved cost {total} > budget {budget_amount}."
            )
        else:
            passed.append(f"Budget check passed: {total} <= {budget_amount}.")

        status = "FAIL" if errors else ("WARNING" if warnings else "PASS")

        return {
            "status": status,
            "passed": passed,
            "warnings": warnings,
            "errors": errors,
            "total_approved_cost": total,
        }
