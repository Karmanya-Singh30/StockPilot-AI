
from decimal import Decimal

from data.synthetic_data import generate_inventory
from agents.inventory_analyst import InventoryAnalystAgent
from agents.replenishment import ReplenishmentAgent


def test_purchase_plan_respects_budget():
    data = generate_inventory()
    analysis = InventoryAnalystAgent().run(data)
    plan = ReplenishmentAgent().run(analysis, 1000)
    total = sum(plan["approved_cost"], Decimal("0.00"))
    assert total <= Decimal("1000.00")


def test_plan_has_approved_quantities():
    data = generate_inventory()
    analysis = InventoryAnalystAgent().run(data)
    plan = ReplenishmentAgent().run(analysis, 5000)
    assert "approved_quantity" in plan.columns
    assert (plan["approved_quantity"] >= 0).all()


def test_zero_budget_approves_no_positive_cost_items():
    data = generate_inventory()
    analysis = InventoryAnalystAgent().run(data)
    plan = ReplenishmentAgent().run(analysis, 0)
    assert all(value == Decimal("0.00") for value in plan["approved_cost"])
