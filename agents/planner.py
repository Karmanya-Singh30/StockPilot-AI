
"""Planner Agent: defines and tracks the inventory workflow."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class Task:
    task_id: str
    name: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    status: str = "PENDING"
    result_summary: str = ""


class PlannerAgent:
    """Creates a structured execution plan for a stock analysis request."""

    name = "Planner Agent"

    def create_plan(self) -> dict:
        tasks = [
            Task("T1", "Validate data", "Check required columns and inventory values."),
            Task("T2", "Analyze inventory", "Calculate demand, stock cover and risk.", ["T1"]),
            Task("T3", "Build purchase plan", "Calculate quantities and allocate budget.", ["T2"]),
            Task("T4", "Validate plan", "Independently verify quantities, costs and budget.", ["T3"]),
        ]

        return {
            "run_id": str(uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "PLANNED",
            "tasks": [vars(task) for task in tasks],
        }

    @staticmethod
    def update_task(
        plan: dict,
        task_id: str,
        status: str,
        result_summary: str = "",
    ) -> None:
        allowed = {"PENDING", "RUNNING", "COMPLETED", "FAILED", "REJECTED"}
        if status not in allowed:
            raise ValueError(f"Unsupported task status: {status}")

        for task in plan["tasks"]:
            if task["task_id"] == task_id:
                task["status"] = status
                task["result_summary"] = result_summary
                return

        raise KeyError(f"Task not found: {task_id}")
