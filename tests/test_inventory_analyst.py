
from data.synthetic_data import generate_inventory
from agents.inventory_analyst import InventoryAnalystAgent


def test_analyst_returns_expected_columns():
    result = InventoryAnalystAgent().run(generate_inventory())
    assert "daily_demand" in result.columns
    assert "days_remaining" in result.columns
    assert "reorder_point" in result.columns
    assert "risk_level" in result.columns
    assert len(result) == 25


def test_zero_demand_does_not_crash():
    data = generate_inventory()
    data.loc[data["product_id"] == "P003", "units_sold"] = 0
    result = InventoryAnalystAgent().run(data)
    row = result.loc[result["product_id"] == "P003"].iloc[0]
    assert row["daily_demand"] == 0
    assert row["risk_level"] == "LOW"


def test_out_of_stock_classification():
    data = generate_inventory()
    data.loc[data["product_id"] == "P002", "current_stock"] = 0
    result = InventoryAnalystAgent().run(data)
    row = result.loc[result["product_id"] == "P002"].iloc[0]
    assert row["risk_level"] == "OUT OF STOCK"
