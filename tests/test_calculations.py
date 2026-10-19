
import math
import pytest

from utils.calculations import (
    average_daily_demand,
    days_of_stock,
    reorder_point,
    target_stock,
    suggested_order_quantity,
    line_item_cost,
)


def test_average_daily_demand():
    assert average_daily_demand(280, 14) == 20


def test_zero_demand_has_infinite_stock_cover():
    assert math.isinf(days_of_stock(10, 0))


def test_zero_stock():
    assert days_of_stock(0, 5) == 0


def test_negative_stock_rejected():
    with pytest.raises(ValueError):
        days_of_stock(-1, 2)


def test_reorder_point():
    assert reorder_point(20, 2, 10) == 50


def test_target_stock():
    assert target_stock(20, 2, 1.5) == 70


def test_suggested_order_quantity():
    assert suggested_order_quantity(30, 70) == 40


def test_minimum_order_quantity():
    assert suggested_order_quantity(30, 32, 10) == 10


def test_no_order_needed():
    assert suggested_order_quantity(100, 70) == 0


def test_line_item_cost():
    assert str(line_item_cost(40, 30)) == "1200.00"


def test_invalid_sales_period():
    with pytest.raises(ValueError):
        average_daily_demand(10, 0)


def test_negative_unit_cost_rejected():
    with pytest.raises(ValueError):
        line_item_cost(2, -10)
