
import streamlit as st
import pandas as pd
import plotly.express as px

from data.synthetic_data import generate_inventory
from orchestration.workflow import StockPilotWorkflow
from utils.validation import validate_inventory

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
# Colors, fonts and radii live in .streamlit/config.toml ("Stockroom ledger").
st.set_page_config(
    page_title="StockPilot AI",
    page_icon=":material/inventory_2:",
    layout="wide",
    initial_sidebar_state="auto",
)

RISK_ORDER = ["OUT OF STOCK", "CRITICAL", "HIGH", "MEDIUM", "LOW"]
RISK_BADGE = {
    "OUT OF STOCK": "red",
    "CRITICAL": "red",
    "HIGH": "orange",
    "MEDIUM": "orange",
    "LOW": "green",
}
# Plotly needs explicit hex values; these mirror redColor/orangeColor/greenColor in config.toml.
RISK_COLORS = {
    "light": {"OUT OF STOCK": "#7A1A12", "CRITICAL": "#B42318", "HIGH": "#B45309",
              "MEDIUM": "#D9922E", "LOW": "#2F7D4F"},
    "dark": {"OUT OF STOCK": "#C2412F", "CRITICAL": "#F0705F", "HIGH": "#E8954A",
             "MEDIUM": "#F2C27B", "LOW": "#5BBF86"},
}


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def money(value):
    try:
        return f"₹{float(value):,.2f}"
    except (ValueError, TypeError):
        return "—"


def numeric(df, column, default=0):
    if column not in df.columns:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors="coerce").fillna(default)


def find_column(df, *candidates):
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def style_chart(fig, height=300):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


def heading(title, subtitle=None):
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)


def by_severity(df, column):
    rank = df[column].astype(str).str.upper().map({r: i for i, r in enumerate(RISK_ORDER)})
    return df.assign(_rank=rank.fillna(len(RISK_ORDER))).sort_values("_rank").drop(columns="_rank")


def run_workflow():
    try:
        with st.spinner("Agents are analyzing stock, planning orders and validating the plan..."):
            st.session_state.workflow_result = StockPilotWorkflow().run(
                st.session_state.inventory.copy(), st.session_state.budget
            )
    except Exception as exc:
        st.session_state.workflow_result = None
        st.session_state.workflow_error = f"{type(exc).__name__}: {exc}"


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
if "inventory" not in st.session_state:
    st.session_state.inventory = generate_inventory()

if "workflow_result" not in st.session_state:
    st.session_state.workflow_result = None

if "inventory_source" not in st.session_state:
    st.session_state.inventory_source = "Built-in demo dataset"


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### :material/inventory_2: StockPilot AI")
    st.caption("Agentic inventory planning for retail stockrooms.")

    st.subheader("Planning controls")
    st.number_input(
        "Purchase budget (₹)",
        min_value=0.0,
        value=10000.0,
        step=500.0,
        key="budget",
        help="Maximum total proposed purchase cost.",
    )

    uploaded_file = st.file_uploader(
        "Import inventory",
        type=["csv"],
        help="Upload a CSV containing the required inventory columns.",
    )

    if uploaded_file is not None:
        try:
            imported = pd.read_csv(uploaded_file)
            errors = validate_inventory(imported)
            if errors:
                st.error("\n".join(f"- {error}" for error in errors), title="CSV validation failed")
            else:
                signature = (
                    uploaded_file.name,
                    uploaded_file.size,
                    uploaded_file.file_id if hasattr(uploaded_file, "file_id") else "",
                )
                if st.session_state.get("upload_signature") != signature:
                    st.session_state.inventory = imported
                    st.session_state.workflow_result = None
                    st.session_state.upload_signature = signature
                    st.session_state.inventory_source = uploaded_file.name
                    st.success("Inventory imported.")
        except Exception as exc:
            st.error(f"Could not import CSV: {exc}")

    st.caption(f"Data source: `{st.session_state.inventory_source}`")

    if st.button("Reset demo data", icon=":material/restart_alt:", width="stretch"):
        st.session_state.inventory = generate_inventory()
        st.session_state.workflow_result = None
        st.session_state.inventory_source = "Built-in demo dataset"
        st.session_state.pop("upload_signature", None)
        st.rerun()

    st.divider()
    st.caption(
        ":material/lock: Runs locally  \n"
        ":material/science: Works with synthetic data  \n"
        ":material/how_to_reg: Every order needs human approval"
    )

budget = st.session_state.budget


# ─────────────────────────────────────────────────────────────
# DATA PREPARATION
# ─────────────────────────────────────────────────────────────
inventory = st.session_state.inventory.copy()
name_col = find_column(inventory, "product_name", "name")
stock_col = find_column(inventory, "current_stock")
cost_col = find_column(inventory, "unit_cost")
category_col = find_column(inventory, "category")

stock = numeric(inventory, stock_col) if stock_col else pd.Series(0, index=inventory.index)
unit_cost = numeric(inventory, cost_col) if cost_col else pd.Series(0, index=inventory.index)
stock_value = float((stock * unit_cost).sum())
product_count = len(inventory)
total_units = float(stock.sum())
category_count = int(inventory[category_col].nunique()) if category_col else 0

result = st.session_state.workflow_result
analysis = result.get("analysis") if isinstance(result, dict) else None
purchase_plan = result.get("purchase_plan") if isinstance(result, dict) else None
validation = result.get("validation", {}) if isinstance(result, dict) else {}
events = result.get("events", []) if isinstance(result, dict) else []
workflow_status = result.get("status", "NOT RUN") if isinstance(result, dict) else "NOT RUN"

analysis_df = analysis.copy() if isinstance(analysis, pd.DataFrame) else pd.DataFrame()
plan_df = purchase_plan.copy() if isinstance(purchase_plan, pd.DataFrame) else pd.DataFrame()

risk_col = find_column(analysis_df, "risk_level", "risk", "stock_status")

approved_cost = validation.get("total_approved_cost", 0)
try:
    approved_cost_value = float(approved_cost)
except (ValueError, TypeError):
    approved_cost_value = 0.0

if not approved_cost_value and not plan_df.empty:
    approved_cost_col = find_column(plan_df, "approved_cost", "approved_order_cost", "line_cost")
    if approved_cost_col:
        approved_cost_value = float(numeric(plan_df, approved_cost_col).sum())

chart_mode = "dark" if st.context.theme.type == "dark" else "light"


# ─────────────────────────────────────────────────────────────
# HEADER: stock tags + run action, shared by every page
# ─────────────────────────────────────────────────────────────
def header(title, subtitle):
    with st.container(horizontal=True, vertical_alignment="bottom"):
        with st.container():
            st.title(title)
            st.caption(subtitle)
        st.button(
            "Run agents" if not result else "Re-run agents",
            icon=":material/play_arrow:",
            type="primary",
            on_click=run_workflow,
        )

    if error := st.session_state.pop("workflow_error", None):
        st.error(error, title="Workflow could not run")

    if risk_col:
        counts = analysis_df[risk_col].astype(str).str.upper().value_counts()
        tags = [
            f":{RISK_BADGE.get(level, 'gray')}-badge[{level} · {counts[level]}]"
            for level in RISK_ORDER if level in counts
        ]
        status_badge = ":green-badge[:material/check: Plan validated]" if workflow_status == "VALIDATED" \
            else f":red-badge[:material/close: Plan {workflow_status.lower()}]"
        st.markdown(" ".join([status_badge, *tags]))
    else:
        status_badge = ":gray-badge[Not analyzed yet]" if workflow_status == "NOT RUN" \
            else f":red-badge[:material/close: {workflow_status}]"
        st.markdown(
            f"{status_badge} `{product_count}` products · `{category_count}` categories · "
            f"budget `{money(budget)}`"
        )


# ─────────────────────────────────────────────────────────────
# PAGE: COMMAND CENTER
# ─────────────────────────────────────────────────────────────
def command_center():
    header("Command center", "Stock health, demand signals and budget-aware replenishment in one view.")

    with st.container(horizontal=True):
        st.metric("Products tracked", f"{product_count:,}", border=True,
                  help=f"{category_count} categories")
        st.metric("Units on hand", f"{total_units:,.0f}", border=True,
                  help="Across all listed products")
        st.metric("Inventory value", money(stock_value), border=True, help="Stock × unit cost")
        st.metric(
            "Budget proposed",
            f"{approved_cost_value / budget * 100:.1f}%" if budget > 0 and result else "—",
            border=True,
            help=f"Share of the {money(budget)} budget allocated by the Replenishment Agent",
        )

    left, right = st.columns([1.2, 1])

    with left:
        heading("Stock health", "Products per risk level, most urgent first.")
        if not analysis_df.empty and risk_col:
            risk_counts = (
                analysis_df[risk_col].astype(str).str.upper()
                .value_counts()
                .reindex(RISK_ORDER).dropna()
                .rename_axis("Risk level")
                .reset_index(name="Products")
            )
            fig = px.bar(
                risk_counts,
                x="Products",
                y="Risk level",
                orientation="h",
                text="Products",
                color="Risk level",
                color_discrete_map=RISK_COLORS[chart_mode],
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="",
                              yaxis=dict(categoryorder="array", categoryarray=RISK_ORDER[::-1]))
            st.plotly_chart(style_chart(fig, 300), alt="Bar chart of products per risk level")
        else:
            st.info("Run the agents to classify every product by stock risk.",
                    icon=":material/play_arrow:")

    with right:
        heading("Units by category", "Current units on hand.")
        if category_col:
            category_summary = (
                inventory.assign(Units=stock)
                .groupby(category_col, dropna=False)["Units"]
                .sum().reset_index()
                .sort_values("Units", ascending=True)
            )
            fig = px.bar(category_summary, x="Units", y=category_col, orientation="h", text="Units")
            fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
            fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
            st.plotly_chart(style_chart(fig, 300), alt="Bar chart of units on hand per category")
        else:
            st.info("No category column found in the inventory.")

    heading("Priority watchlist", "Products below the low-risk threshold, most urgent first.")
    if not analysis_df.empty and risk_col:
        watch = by_severity(analysis_df, risk_col)
        watch = watch[watch[risk_col].astype(str).str.upper() != "LOW"]
        cols = [c for c in ["product_id", name_col, category_col, stock_col, "days_remaining",
                            "reorder_point", risk_col, "risk_explanation"] if c and c in watch.columns]
        st.dataframe(
            watch[cols],
            hide_index=True,
            column_config={
                "product_id": st.column_config.TextColumn("SKU"),
                "product_name": "Product",
                "category": "Category",
                "current_stock": st.column_config.NumberColumn("On hand", format="%d"),
                "days_remaining": st.column_config.NumberColumn("Days of cover", format="%.1f"),
                "reorder_point": st.column_config.NumberColumn("Reorder point", format="%.0f"),
                "risk_level": "Risk",
                "risk_explanation": st.column_config.TextColumn("Why", width="large"),
            },
            alt="Products needing attention, sorted by risk",
        )
    else:
        with st.container(border=True):
            st.markdown("**Next step: run the agents**")
            st.caption(
                "The agents work out daily demand, days of cover, reorder points and a "
                "budget-aware purchase plan. A separate Critic agent then checks the plan."
            )


# ─────────────────────────────────────────────────────────────
# PAGE: INVENTORY EXPLORER
# ─────────────────────────────────────────────────────────────
def inventory_explorer():
    header("Inventory explorer", "Search, filter and export the current product dataset.")

    with st.container(horizontal=True, vertical_alignment="bottom"):
        search = st.text_input("Search products", placeholder="Product name, SKU, category or supplier",
                               icon=":material/search:")
        category_filter = "All categories"
        if category_col:
            options = ["All categories"] + sorted(inventory[category_col].dropna().astype(str).unique().tolist())
            category_filter = st.selectbox("Category", options)

    filtered = inventory.copy()

    if search:
        searchable_cols = [c for c in ["product_id", "product_name", "name", "category", "supplier_name"] if c in filtered.columns]
        if searchable_cols:
            mask = pd.Series(False, index=filtered.index)
            for col in searchable_cols:
                mask |= filtered[col].astype(str).str.contains(search, case=False, na=False, regex=False)
            filtered = filtered[mask]

    if category_col and category_filter != "All categories":
        filtered = filtered[filtered[category_col].astype(str) == category_filter]

    with st.container(horizontal=True):
        st.metric("Matching products", len(filtered), border=True)
        st.metric("Units shown", f"{numeric(filtered, stock_col).sum():,.0f}" if stock_col else "—", border=True)
        st.metric("Value shown", money((numeric(filtered, stock_col) * numeric(filtered, cost_col)).sum())
                  if stock_col and cost_col else "—", border=True)

    st.dataframe(filtered, hide_index=True, height=460, alt="Filtered inventory table")

    st.download_button(
        "Export filtered inventory",
        data=csv_bytes(filtered),
        file_name="stockpilot_filtered_inventory.csv",
        mime="text/csv",
        icon=":material/download:",
    )

    st.divider()
    heading("Calculated inventory signals", "Agent output, kept separate from the source data.")
    if not analysis_df.empty:
        st.dataframe(analysis_df, hide_index=True, alt="Agent-calculated inventory signals")
        st.download_button(
            "Export analysis",
            data=csv_bytes(analysis_df),
            file_name="stockpilot_analysis.csv",
            mime="text/csv",
            icon=":material/download:",
        )
    else:
        st.info("Run the agents to calculate risk and demand signals.", icon=":material/play_arrow:")


# ─────────────────────────────────────────────────────────────
# PAGE: REPLENISHMENT
# ─────────────────────────────────────────────────────────────
def replenishment():
    header("Replenishment", "Review proposed orders and the independent Critic validation.")

    with st.container(horizontal=True):
        st.metric("Planning budget", money(budget), border=True)
        st.metric("Proposed approved cost", money(approved_cost_value) if result else "—", border=True)
        st.metric("Budget remaining", money(max(0.0, budget - approved_cost_value)) if result else "—",
                  border=True)

    if not result:
        st.info("No purchase plan yet. Run the agents to generate one.", icon=":material/play_arrow:")
        return

    if workflow_status == "VALIDATED":
        st.success("Review each line before you place any order.", title="Plan validated")
    elif workflow_status == "REJECTED":
        st.error("Do not use this plan for purchasing.", title="Plan rejected")
    else:
        st.warning(f"Workflow status: {workflow_status}")

    if not plan_df.empty:
        st.dataframe(
            plan_df,
            hide_index=True,
            column_order=[c for c in ["priority_rank", "product_id", "product_name", "risk_level",
                                      "suggested_quantity", "approved_quantity", "approved_cost",
                                      "allocation_status", "unit_cost", "supplier_name"] if c in plan_df.columns],
            column_config={
                "priority_rank": st.column_config.NumberColumn("Priority", format="%d"),
                "product_id": "SKU",
                "product_name": "Product",
                "risk_level": "Risk",
                "suggested_quantity": st.column_config.NumberColumn("Suggested qty", format="%d"),
                "approved_quantity": st.column_config.NumberColumn("Approved qty", format="%d"),
                "approved_cost": st.column_config.NumberColumn("Approved cost (₹)", format="%.2f"),
                "allocation_status": "Allocation",
                "unit_cost": st.column_config.NumberColumn("Unit cost (₹)", format="%.2f"),
                "supplier_name": "Supplier",
            },
            alt="Proposed purchase plan",
        )
        st.download_button(
            "Export purchase plan",
            data=csv_bytes(plan_df),
            file_name="stockpilot_purchase_plan.csv",
            mime="text/csv",
            icon=":material/download:",
        )
    else:
        st.info("The workflow returned no purchase-plan rows.")

    st.divider()
    heading("Independent validation", "Results reported by the Critic Agent.")

    checks = validation.get("passed", [])
    warnings = validation.get("warnings", [])
    errors = validation.get("errors", [])

    with st.container(horizontal=True):
        st.metric("Checks passed", len(checks), border=True)
        st.metric("Warnings", len(warnings), border=True)
        st.metric("Errors", len(errors), border=True)

    with st.expander("Passed checks", icon=":material/check_circle:", expanded=True):
        if checks:
            st.markdown("\n".join(f"- {item}" for item in checks))
        else:
            st.caption("No passed checks were reported.")

    with st.expander("Warnings", icon=":material/warning:", expanded=bool(warnings)):
        if warnings:
            for item in warnings:
                st.warning(item)
        else:
            st.caption("No warnings reported.")

    with st.expander("Validation errors", icon=":material/error:", expanded=bool(errors)):
        if errors:
            for item in errors:
                st.error(item)
        else:
            st.caption("No validation errors reported.")


# ─────────────────────────────────────────────────────────────
# PAGE: AGENT ACTIVITY
# ─────────────────────────────────────────────────────────────
def agent_activity():
    header("Agent activity", "The execution trace produced by the orchestration workflow.")

    if not result:
        st.info("Run the agents first. The orchestration trace will appear here.",
                icon=":material/play_arrow:")
        with st.container(border=True):
            st.markdown("**Workflow design**")
            st.markdown(
                "1. **Planner Agent** sequences the tasks\n"
                "2. **Inventory Analyst** analyzes demand and stock risk\n"
                "3. **Replenishment Agent** proposes orders within budget\n"
                "4. **Critic Agent** validates the plan independently\n"
                "5. **Orchestrator** bounds retries and sets the final status"
            )
            st.caption("Agent roles come from the project design. Run details appear after a run.")
        return

    events_df = pd.DataFrame(events)
    if events_df.empty:
        st.info("No events were returned by the workflow.")
        return

    if "status" in events_df.columns:
        status_upper = events_df["status"].astype(str).str.upper()
        completed = int(status_upper.isin(["COMPLETED", "PASS"]).sum())
        failed = int(status_upper.isin(["FAILED", "REJECTED", "FAIL"]).sum())
    else:
        completed, failed = 0, 0

    with st.container(horizontal=True):
        st.metric("Revision attempts", result.get("revision_attempts", 0), border=True)
        st.metric("Events logged", len(events_df), border=True)
        st.metric("Completed or passed", completed, border=True)
        st.metric("Failed or rejected", failed, border=True)

    st.dataframe(
        events_df,
        hide_index=True,
        column_config={
            "step": st.column_config.NumberColumn("Step", format="%d", width="small"),
            "agent": "Agent",
            "action": "Action",
            "status": "Status",
            "details": st.column_config.TextColumn("Details", width="large"),
        },
        alt="Agent execution log",
    )

    st.download_button(
        "Download execution log",
        data=csv_bytes(events_df),
        file_name="stockpilot_execution_log.csv",
        mime="text/csv",
        icon=":material/download:",
    )


# ─────────────────────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────────────────────
page = st.navigation(
    [
        st.Page(command_center, title="Command center", icon=":material/dashboard:", default=True),
        st.Page(inventory_explorer, title="Inventory explorer", icon=":material/inventory:"),
        st.Page(replenishment, title="Replenishment", icon=":material/local_shipping:"),
        st.Page(agent_activity, title="Agent activity", icon=":material/account_tree:"),
    ],
    position="top",
)
page.run()

st.divider()
st.caption("StockPilot AI · Academic proof of concept · Proposals only. No orders are placed without human review.")
