
"""Input schema and value validation for inventory data."""

import math
import pandas as pd


REQUIRED_COLUMNS = [
    "product_id",
    "product_name",
    "category",
    "current_stock",
    "units_sold",
    "sales_period_days",
    "unit_cost",
    "supplier_lead_time_days",
    "safety_stock",
    "target_coverage_days",
    "minimum_order_quantity",
]


NON_NEGATIVE_COLUMNS = [
    "current_stock",
    "units_sold",
    "unit_cost",
    "supplier_lead_time_days",
    "safety_stock",
    "target_coverage_days",
    "minimum_order_quantity",
]


def validate_inventory(data: pd.DataFrame) -> list[str]:
    """Return validation errors; an empty list means the input is valid."""
    errors: list[str] = []

    if not isinstance(data, pd.DataFrame):
        return ["Input must be a pandas DataFrame."]

    if data.empty:
        return ["Inventory dataset is empty."]

    missing = [c for c in REQUIRED_COLUMNS if c not in data.columns]
    if missing:
        return [f"Missing required columns: {', '.join(missing)}"]

    if data["product_id"].isna().any():
        errors.append("product_id cannot contain missing values.")
    elif data["product_id"].astype(str).str.strip().eq("").any():
        errors.append("product_id cannot be blank.")
    elif data["product_id"].duplicated().any():
        errors.append("product_id values must be unique.")

    for column in ["product_name", "category"]:
        if data[column].isna().any():
            errors.append(f"{column} cannot contain missing values.")
        elif data[column].astype(str).str.strip().eq("").any():
            errors.append(f"{column} cannot be blank.")

    numeric_columns = [
        "current_stock",
        "units_sold",
        "sales_period_days",
        "unit_cost",
        "supplier_lead_time_days",
        "safety_stock",
        "target_coverage_days",
        "minimum_order_quantity",
    ]

    for column in numeric_columns:
        values = pd.to_numeric(data[column], errors="coerce")

        if values.isna().any():
            errors.append(f"{column} contains missing or invalid numeric values.")
            continue

        if not all(math.isfinite(float(v)) for v in values):
            errors.append(f"{column} must contain finite numeric values.")
            continue

        if (values < 0).any():
            errors.append(f"{column} cannot contain negative values.")

        if column in [
            "sales_period_days",
            "supplier_lead_time_days",
            "minimum_order_quantity",
        ] and not (values == values.round()).all():
            errors.append(f"{column} must contain whole numbers.")

    if "sales_period_days" in data.columns:
        periods = pd.to_numeric(data["sales_period_days"], errors="coerce")
        if periods.notna().all() and (periods <= 0).any():
            errors.append("sales_period_days must be greater than zero.")

    return errors
