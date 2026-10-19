
from data.synthetic_data import generate_inventory
from orchestration.workflow import StockPilotWorkflow


def test_workflow_completes():
    result = StockPilotWorkflow().run(generate_inventory(), 5000)
    assert result["status"] == "VALIDATED"
    assert result["validation"]["status"] in {"PASS", "WARNING"}
    assert len(result["events"]) > 0


def test_invalid_inventory_is_rejected():
    data = generate_inventory()
    data.loc[0, "current_stock"] = -10
    result = StockPilotWorkflow().run(data, 5000)
    assert result["status"] == "REJECTED"
    assert result["validation"]["status"] == "FAIL"


def test_invalid_budget_is_rejected():
    result = StockPilotWorkflow().run(generate_inventory(), -100)
    assert result["status"] == "REJECTED"


def test_retry_count_is_bounded():
    workflow = StockPilotWorkflow(max_retries=2)
    assert workflow.max_retries == 2
