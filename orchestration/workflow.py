
"""Central orchestrator for the StockPilot AI multi-agent workflow."""

from decimal import Decimal
from typing import Any

import pandas as pd

from agents.planner import PlannerAgent
from agents.inventory_analyst import InventoryAnalystAgent
from agents.replenishment import ReplenishmentAgent
from agents.critic import CriticAgent
from utils.calculations import line_item_cost, money
from utils.validation import validate_inventory


class StockPilotWorkflow:
    """Coordinates agents, records execution events and bounds retries."""

    def __init__(self, max_retries: int = 2):
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative.")

        self.max_retries = max_retries
        self.planner = PlannerAgent()
        self.analyst = InventoryAnalystAgent()
        self.replenishment = ReplenishmentAgent()
        self.critic = CriticAgent()

    def run(
        self,
        inventory: pd.DataFrame,
        budget: float | str | Decimal,
    ) -> dict[str, Any]:
        """Execute analysis, planning, validation and bounded correction."""
        events: list[dict[str, Any]] = []
        plan = self.planner.create_plan()

        def log(agent: str, action: str, status: str, details: str = ""):
            events.append({
                "step": len(events) + 1,
                "agent": agent,
                "action": action,
                "status": status,
                "details": details,
            })

        try:
            budget_amount = money(budget)
        except (ValueError, ArithmeticError) as exc:
            log("Input Validator", "Validate purchasing budget", "FAILED", str(exc))
            return {
                "status": "REJECTED",
                "plan": plan,
                "analysis": None,
                "purchase_plan": pd.DataFrame(),
                "validation": {
                    "status": "FAIL",
                    "passed": [],
                    "warnings": [],
                    "errors": [str(exc)],
                    "total_approved_cost": Decimal("0.00"),
                },
                "events": events,
                "revision_attempts": 0,
            }

        log("Input Validator", "Validate inventory schema and values", "RUNNING")
        input_errors = validate_inventory(inventory)

        if input_errors:
            details = "; ".join(input_errors)
            log("Input Validator", "Validate inventory schema and values", "FAILED", details)
            return {
                "status": "REJECTED",
                "plan": plan,
                "analysis": None,
                "purchase_plan": pd.DataFrame(),
                "validation": {
                    "status": "FAIL",
                    "passed": [],
                    "warnings": [],
                    "errors": input_errors,
                    "total_approved_cost": Decimal("0.00"),
                },
                "events": events,
                "revision_attempts": 0,
            }

        self.planner.update_task(plan, "T1", "COMPLETED", "Input data passed validation.")
        log("Input Validator", "Schema and numeric checks", "PASS")

        try:
            log("Planner Agent", "Create ordered execution plan", "RUNNING")
            log("Planner Agent", "Plan created", "COMPLETED", f"Run ID: {plan['run_id']}")

            self.planner.update_task(plan, "T2", "RUNNING")
            log("Inventory Analyst Agent", "Calculate demand, stock cover and risk", "RUNNING")
            analysis = self.analyst.run(inventory)
            self.planner.update_task(
                plan, "T2", "COMPLETED",
                f"Analyzed {len(analysis)} products."
            )
            log(
                "Inventory Analyst Agent",
                "Calculate reorder points and risk classifications",
                "COMPLETED",
                f"{len(analysis)} products analyzed.",
            )

            self.planner.update_task(plan, "T3", "RUNNING")
            log("Replenishment Agent", "Build budget-aware candidate plan", "RUNNING")
            purchase_plan = self.replenishment.run(analysis, budget_amount)
            self.planner.update_task(
                plan, "T3", "COMPLETED",
                f"{len(purchase_plan)} product rows evaluated."
            )
            log(
                "Replenishment Agent",
                "Allocate proposed quantities under budget",
                "COMPLETED",
                f"Budget: {budget_amount}",
            )

            self.planner.update_task(plan, "T4", "RUNNING")
            validation = self.critic.run(
                inventory, analysis, purchase_plan, budget_amount
            )
            log(
                "Critic / Validation Agent",
                "Independently recompute quantities, costs and budget",
                validation["status"],
                "; ".join(validation["errors"] or validation["warnings"])
                or "All validation checks passed.",
            )

            revision_attempts = 0

            while validation["status"] == "FAIL" and revision_attempts < self.max_retries:
                revision_attempts += 1
                log(
                    "Planner Agent",
                    "Request bounded plan revision",
                    "RUNNING",
                    f"Revision attempt {revision_attempts}/{self.max_retries}.",
                )

                # Rebuild the plan deterministically from validated source data.
                # This is a bounded retry, not a claim that arbitrary errors
                # can always be repaired automatically.
                purchase_plan = self.replenishment.run(analysis, budget_amount)
                validation = self.critic.run(
                    inventory, analysis, purchase_plan, budget_amount
                )

                log(
                    "Critic / Validation Agent",
                    "Revalidate revised purchase plan",
                    validation["status"],
                    "; ".join(validation["errors"] or validation["warnings"])
                    or "Revised plan passed validation.",
                )

            approved = validation["status"] in {"PASS", "WARNING"}

            if approved:
                self.planner.update_task(
                    plan, "T4", "COMPLETED",
                    "Purchase plan passed hard validation checks."
                )
                plan["status"] = "COMPLETED"
                log(
                    "Workflow",
                    "Finalize validated purchase plan",
                    "COMPLETED",
                    "Recommendations are proposals only; no orders were placed.",
                )
                status = "VALIDATED"
            else:
                self.planner.update_task(
                    plan, "T4", "FAILED",
                    "Plan failed validation after bounded retries."
                )
                plan["status"] = "REJECTED"
                log(
                    "Workflow",
                    "Reject invalid purchase plan",
                    "REJECTED",
                    "; ".join(validation["errors"]),
                )
                status = "REJECTED"

            return {
                "status": status,
                "plan": plan,
                "analysis": analysis,
                "purchase_plan": purchase_plan,
                "validation": validation,
                "events": events,
                "revision_attempts": revision_attempts,
            }

        except Exception as exc:
            plan["status"] = "FAILED"
            log(
                "Workflow",
                "Handle unexpected agent/workflow failure",
                "FAILED",
                f"{type(exc).__name__}: {exc}",
            )
            return {
                "status": "FAILED",
                "plan": plan,
                "analysis": None,
                "purchase_plan": pd.DataFrame(),
                "validation": {
                    "status": "FAIL",
                    "passed": [],
                    "warnings": [],
                    "errors": [f"{type(exc).__name__}: {exc}"],
                    "total_approved_cost": Decimal("0.00"),
                },
                "events": events,
                "revision_attempts": 0,
            }
