
"""Generate deterministic, fictional supermarket inventory data."""

from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42


def generate_inventory(seed: int = SEED, product_count: int = 25) -> pd.DataFrame:
    """Create fictional inventory records with useful demonstration cases."""
    if product_count < 1:
        raise ValueError("product_count must be at least 1.")

    rng = np.random.default_rng(seed)

    products = [
        ("P001", "Packaged Milk", "Dairy"),
        ("P002", "Yogurt Cup", "Dairy"),
        ("P003", "Butter", "Dairy"),
        ("P004", "Cheddar Cheese", "Dairy"),
        ("P005", "Bread Loaf", "Packaged Foods"),
        ("P006", "Breakfast Cereal", "Packaged Foods"),
        ("P007", "Instant Noodles", "Packaged Foods"),
        ("P008", "Rice Bag", "Packaged Foods"),
        ("P009", "Bottled Water", "Beverages"),
        ("P010", "Orange Juice", "Beverages"),
        ("P011", "Coffee Jar", "Beverages"),
        ("P012", "Tea Pack", "Beverages"),
        ("P013", "Shampoo", "Personal Care"),
        ("P014", "Toothpaste", "Personal Care"),
        ("P015", "Hand Wash", "Personal Care"),
        ("P016", "Laundry Detergent", "Household"),
        ("P017", "Dishwashing Liquid", "Household"),
        ("P018", "Paper Towels", "Household"),
        ("P019", "Cooking Oil", "Packaged Foods"),
        ("P020", "Biscuits", "Packaged Foods"),
        ("P021", "Energy Drink", "Beverages"),
        ("P022", "Face Wash", "Personal Care"),
        ("P023", "Floor Cleaner", "Household"),
        ("P024", "Cheese Slices", "Dairy"),
        ("P025", "Granola Bar", "Packaged Foods"),
    ]

    if product_count > len(products):
        raise ValueError(f"Maximum supported product_count is {len(products)}.")

    rows = []

    for product_id, name, category in products[:product_count]:
        rows.append({
            "product_id": product_id,
            "product_name": name,
            "category": category,
            "current_stock": int(rng.integers(10, 150)),
            "units_sold": int(rng.integers(20, 300)),
            "sales_period_days": 14,
            "unit_cost": round(float(rng.uniform(10, 250)), 2),
            "supplier_lead_time_days": int(rng.integers(1, 8)),
            "safety_stock": int(rng.integers(5, 25)),
            "target_coverage_days": 1.5,
            "minimum_order_quantity": 0,
            "supplier_name": f"Supplier {int(rng.integers(1, 6))}",
        })

    data = pd.DataFrame(rows)

    # Fixed edge cases make demonstrations repeatable.
    overrides = {
        "P001": {"current_stock": 30, "units_sold": 280,
                 "sales_period_days": 14, "unit_cost": 30.0,
                 "supplier_lead_time_days": 2, "safety_stock": 10,
                 "target_coverage_days": 1.5},
        "P002": {"current_stock": 0},
        "P003": {"units_sold": 0},
        "P004": {"current_stock": 250},
        "P005": {"supplier_lead_time_days": 7},
    }

    for product_id, changes in overrides.items():
        mask = data["product_id"] == product_id
        if mask.any():
            for column, value in changes.items():
                data.loc[mask, column] = value

    return data


def save_sample_csv(path: str | Path | None = None) -> Path:
    """Save sample inventory to the project's data directory by default."""
    destination = (
        Path(path) if path is not None
        else Path(__file__).resolve().parent / "sample_inventory.csv"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    generate_inventory().to_csv(destination, index=False)
    return destination


if __name__ == "__main__":
    print(f"Created sample data: {save_sample_csv()}")
