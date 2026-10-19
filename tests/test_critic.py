
from decimal import Decimal

from data.synthetic_data import generate_inventory
from agents.inventory_analyst import InventoryAnalystAgent
from agents.replenishment import ReplenishmentAgent
from agents.critic import CriticAgent


def make_plan(budget=5000):
    data = generate_inventory()
    analysis = InventoryAnalystAgent().run(data)
    plan = ReplenishmentAgent().run(analysis, budget)
    result = CriticAgent().run(data, analysis, plan, budget)
    return data, analysis, plan, result


def test_critic_validates_correct_plan():
    _, _, _, result = make_plan()
    assert result["status"] in {"PASS", "WARNING"}


def test_critic_rejects_wrong_cost():
    data, analysis, plan, _ = make_plan()
    plan.loc[0, "approved_cost"] = Decimal("999999.00")
    result = CriticAgent().run(data, analysis, plan, 5000)
    assert result["status"] == "FAIL"
    assert any("cost mismatch" in error for error in result["errors"])


def test_critic_rejects_negative_quantity():
    data, analysis, plan, _ = make_plan()
    plan.loc[0, "approved_quantity"] = -1
    result = CriticAgent().run(data, analysis, plan, 5000)
    assert result["status"] == "FAIL"
