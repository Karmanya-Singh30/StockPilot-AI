
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data.synthetic_data import generate_inventory
from orchestration.workflow import StockPilotWorkflow
from utils.validation import validate_inventory

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StockPilot AI | Command Center",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

BG = "#0B1120"
PANEL = "#111B2E"
BORDER = "#243249"
MUTED = "#8FA2BB"
TEXT = "#EDF4FF"
GREEN = "#34D399"
RED = "#FB7185"
AMBER = "#FBBF24"
BLUE = "#60A5FA"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --background-color: #0B1120;
    --secondary-background-color: #111B2E;
    --text-color: #EDF4FF;
    --primary-color: #34D399;
}
.stApp {
    background:
      radial-gradient(ellipse at 80% 0%, rgba(16,185,129,.075), transparent 35%),
      #0B1120;
    font-family: 'DM Sans', sans-serif;
}
h1,h2,h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.5px;
}
.block-container {
    max-width: 1550px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}
[data-testid="stSidebar"] {
    background: #0D1627;
    border-right: 1px solid #243249;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.3rem; }
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #142137, #101A2B);
    border: 1px solid #243249;
    padding: 17px 19px;
    border-radius: 15px;
    min-height: 125px;
}
[data-testid="stMetricLabel"] {
    color: #8FA2BB !important;
    font-size: 13px !important;
}
[data-testid="stMetricValue"] {
    color: #EDF4FF !important;
    font-family: 'Space Grotesk', sans-serif;
}
[data-testid="stMetricDelta"] { font-size: 12px; }
.stButton > button, .stDownloadButton > button {
    border-radius: 10px;
    border: 1px solid #2D425C;
    min-height: 42px;
    font-weight: 600;
    transition: all .18s ease;
}
.stButton > button[kind="primary"] {
    background: #34D399;
    border-color: #34D399;
    color: #07131A;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #34D399;
    color: #34D399;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #243249;
    border-radius: 12px;
    overflow: hidden;
}
div[data-testid="stTabs"] button { font-weight: 600; }
hr { border-color: #243249; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #243249 !important;
    border-radius: 14px !important;
}
div[data-testid="stAlert"] { border-radius: 12px; }
small, .muted { color: #8FA2BB; }
.hero {
    background: linear-gradient(115deg, #14263A 0%, #102A2B 100%);
    border: 1px solid #285044;
    border-radius: 20px;
    padding: 25px 28px;
    margin-bottom: 22px;
    position: relative;
    overflow: hidden;
}
.hero:after {
    content: '↗';
    position: absolute;
    right: 28px;
    top: 12px;
    font-size: 78px;
    color: rgba(52,211,153,.13);
    font-family: 'Space Grotesk', sans-serif;
}
.eyebrow {
    color: #34D399;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 2px;
    font-weight: 700;
}
.hero h1 {
    margin: 8px 0 5px;
    font-size: 33px;
    color: #F1F7FF;
}
.hero p { color: #A9BDD2; margin-bottom: 0; font-size: 14px; }
.section-head {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 19px;
    font-weight: 600;
    margin: 12px 0 4px;
}
.section-sub { color: #8FA2BB; font-size: 12px; margin-bottom: 13px; }
.pill {
    display: inline-block;
    border: 1px solid #285044;
    background: rgba(52,211,153,.09);
    color: #34D399;
    padding: 5px 10px;
    border-radius: 100px;
    font-size: 11px;
    font-weight: 700;
}
.info-card {
    background: #111B2E;
    border: 1px solid #243249;
    border-radius: 14px;
    padding: 17px;
}
.info-label { color: #8FA2BB; font-size: 12px; margin-bottom: 7px; }
.info-value { font-size: 22px; font-weight: 700; color: #EDF4FF; }
.info-note { font-size: 11px; color: #8FA2BB; margin-top: 5px; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


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
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color=TEXT, size=12),
        margin=dict(l=10, r=10, t=35, b=10),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=MUTED),
        ),
        xaxis=dict(
            gridcolor=BORDER,
            zerolinecolor=BORDER,
            linecolor=BORDER,
        ),
        yaxis=dict(
            gridcolor=BORDER,
            zerolinecolor=BORDER,
            linecolor=BORDER,
        ),
    )
    return fig


def heading(title, subtitle=None):
    st.markdown(f'<div class="section-head">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-sub">{subtitle}</div>', unsafe_allow_html=True)


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
    st.markdown(
        f"""
        <div style="padding:5px 0 23px;">
          <div style="display:flex;align-items:center;gap:10px;">
            <div style="background:#163D35;border:1px solid #285044;
                        border-radius:12px;padding:10px;font-size:22px;">📦</div>
            <div>
              <div style="font-family:Space Grotesk;font-weight:700;
                          font-size:20px;color:#EDF4FF;">StockPilot<span style="color:#34D399"> AI</span></div>
              <div style="font-size:10px;letter-spacing:1.4px;color:#8FA2BB;">INVENTORY INTELLIGENCE</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("##### WORKSPACE")
    page = st.radio(
        "Navigation",
        ["Command Center", "Inventory Explorer", "Replenishment", "Agent Activity"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("##### PLANNING CONTROLS")

    budget = st.number_input(
        "Purchase budget (₹)",
        min_value=0.0,
        value=10000.0,
        step=500.0,
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
                st.error("CSV validation failed")
                for error in errors:
                    st.caption(f"• {error}")
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

    st.caption(f"Data source: {st.session_state.inventory_source}")

    if st.button("↻ Reset demo data", use_container_width=True):
        st.session_state.inventory = generate_inventory()
        st.session_state.workflow_result = None
        st.session_state.inventory_source = "Built-in demo dataset"
        st.session_state.pop("upload_signature", None)
        st.rerun()

    st.divider()
    st.markdown(
        f"""
        <div style="font-size:11px;color:#8FA2BB;line-height:1.8;">
        <span style="color:#34D399">●</span> Local application<br>
        <span style="color:#34D399">●</span> Synthetic-data ready<br>
        <span style="color:#FBBF24">●</span> Human approval required
        </div>
        """,
        unsafe_allow_html=True,
    )


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
if risk_col:
    risk_series = analysis_df[risk_col].astype(str).str.upper()
else:
    risk_series = pd.Series(dtype=str)

critical_count = int(risk_series.str.contains("CRITICAL|HIGH|OUT|URGENT", regex=True).sum()) if len(risk_series) else 0
low_count = int(risk_series.str.contains("LOW|MEDIUM|REORDER|WARNING", regex=True).sum()) if len(risk_series) else 0

approved_cost = validation.get("total_approved_cost", 0)
try:
    approved_cost_value = float(approved_cost)
except (ValueError, TypeError):
    approved_cost_value = 0.0

if not approved_cost_value and not plan_df.empty:
    approved_cost_col = find_column(plan_df, "approved_cost", "approved_order_cost", "line_cost")
    if approved_cost_col:
        approved_cost_value = float(numeric(plan_df, approved_cost_col).sum())

# ─────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────
status_color = GREEN if workflow_status == "VALIDATED" else AMBER if workflow_status == "NOT RUN" else RED
status_label = "READY TO ANALYZE" if workflow_status == "NOT RUN" else workflow_status

st.markdown(
    f"""
    <div class="hero">
      <div class="eyebrow">RETAIL OPERATIONS / COMMAND CENTER</div>
      <h1>Inventory intelligence, at a glance.</h1>
      <p>Monitor stock health, evaluate demand signals and build budget-aware replenishment plans.</p>
      <div style="margin-top:17px;">
        <span class="pill">● {status_label}</span>
        <span style="font-size:11px;color:#8FA2BB;margin-left:10px;">{product_count} products · {category_count} categories · Budget {money(budget)}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# PAGE: COMMAND CENTER
# ─────────────────────────────────────────────────────────────
if page == "Command Center":
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Products tracked", f"{product_count:,}", f"{category_count} categories")
    k2.metric("Units on hand", f"{total_units:,.0f}", "Across all listed products")
    k3.metric("Inventory value", money(stock_value), "Stock × unit cost")
    k4.metric(
        "Purchase budget",
        money(budget),
        f"{(approved_cost_value / budget * 100):.1f}% proposed"
        if budget > 0 and result else "Run analysis to allocate",
    )

    st.markdown("")
    left, right = st.columns([1.2, 1])

    with left:
        heading("Stock health", "Risk classifications returned by the Inventory Analyst")
        if not analysis_df.empty and risk_col:
            risk_counts = (
                analysis_df[risk_col].astype(str)
                .value_counts()
                .rename_axis("Risk level")
                .reset_index(name="Products")
            )
            fig = px.pie(
                risk_counts,
                names="Risk level",
                values="Products",
                hole=0.68,
                color_discrete_sequence=[GREEN, BLUE, AMBER, RED, "#A78BFA"],
            )
            fig.update_traces(
                textposition="inside",
                textinfo="label+value",
                marker=dict(line=dict(color=BG, width=3)),
            )
            fig.update_layout(showlegend=False, annotations=[
                dict(
                    text=f"<b>{len(analysis_df)}</b><br><span style='font-size:11px'>analyzed</span>",
                    x=0.5, y=0.5, font=dict(size=21, color=TEXT),
                    showarrow=False,
                )
            ])
            st.plotly_chart(style_chart(fig, 310), use_container_width=True)
        else:
            st.info("Run the agents to populate the stock-health chart.")

    with right:
        heading("Inventory by category", "Current units on hand")
        if category_col:
            category_data = inventory.copy()
            category_data["_stock"] = stock
            category_summary = (
                category_data.groupby(category_col, dropna=False)["_stock"]
                .sum().reset_index()
                .sort_values("_stock", ascending=True)
            )
            fig = px.bar(
                category_summary,
                x="_stock",
                y=category_col,
                orientation="h",
                text="_stock",
                color_discrete_sequence=[GREEN],
            )
            fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
            fig.update_layout(
                showlegend=False,
                xaxis_title="Units",
                yaxis_title="",
                uniformtext_minsize=10,
                uniformtext_mode="hide",
            )
            st.plotly_chart(style_chart(fig, 310), use_container_width=True)
        else:
            st.info("No category column found in the inventory.")

    heading("Priority watchlist", "Products that may need attention")
    if not analysis_df.empty:
        display_df = analysis_df.copy()
        if risk_col:
            display_df["_risk_sort"] = display_df[risk_col].astype(str).str.upper()
            display_df = display_df.sort_values("_risk_sort")
            display_df = display_df.drop(columns=["_risk_sort"])
        st.dataframe(display_df.head(8), use_container_width=True, hide_index=True)
    else:
        st.markdown(
            f"""
            <div class="info-card">
              <div class="info-label">NEXT ACTION</div>
              <div class="info-value">Run your inventory agents</div>
              <div class="info-note">The system will calculate demand, stock cover, replenishment needs and independent validation.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    col_run, col_status = st.columns([1, 2])
    with col_run:
        if st.button("▶ Run inventory analysis", type="primary", use_container_width=True):
            try:
                with st.spinner("Agents are working through the inventory..."):
                    workflow = StockPilotWorkflow()
                    st.session_state.workflow_result = workflow.run(inventory, budget)
                st.rerun()
            except Exception as exc:
                st.error(f"Workflow could not run: {exc}")
                st.exception(exc)

    with col_status:
        if result:
            st.caption(
                f"Last run: **{workflow_status}** · "
                f"Validation: **{validation.get('status', 'UNKNOWN')}** · "
                f"Revisions: **{result.get('revision_attempts', 0)}**"
            )
        else:
            st.caption("No analysis run in this session yet.")


# ─────────────────────────────────────────────────────────────
# PAGE: INVENTORY EXPLORER
# ─────────────────────────────────────────────────────────────
elif page == "Inventory Explorer":
    heading("Inventory Explorer", "Search, filter and export the current product dataset.")

    search = st.text_input("⌕ Search products", placeholder="Search product name, ID or category...")
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
                mask |= filtered[col].astype(str).str.contains(search, case=False, na=False)
            filtered = filtered[mask]

    if category_col and category_filter != "All categories":
        filtered = filtered[filtered[category_col].astype(str) == category_filter]

    m1, m2, m3 = st.columns(3)
    m1.metric("Matching products", len(filtered))
    m2.metric("Units shown", f"{numeric(filtered, stock_col).sum():,.0f}" if stock_col else "—")
    m3.metric("Value shown", money((numeric(filtered, stock_col) * numeric(filtered, cost_col)).sum()) if stock_col and cost_col else "—")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        height=460,
    )

    st.download_button(
        "⬇ Export filtered inventory",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="stockpilot_filtered_inventory.csv",
        mime="text/csv",
    )

    if not analysis_df.empty:
        st.divider()
        heading("Calculated inventory signals", "Agent output, kept separate from the source data.")
        st.dataframe(analysis_df, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇ Export analysis",
            data=analysis_df.to_csv(index=False).encode("utf-8"),
            file_name="stockpilot_analysis.csv",
            mime="text/csv",
        )
    else:
        st.info("Run the inventory agents from Command Center to calculate risk and demand signals.")


# ─────────────────────────────────────────────────────────────
# PAGE: REPLENISHMENT
# ─────────────────────────────────────────────────────────────
elif page == "Replenishment":
    heading("Replenishment workspace", "Review proposed orders and the independent Critic validation.")

    b1, b2, b3 = st.columns(3)
    b1.metric("Planning budget", money(budget))
    b2.metric("Proposed approved cost", money(approved_cost_value) if result else "—")
    remaining = max(0.0, budget - approved_cost_value)
    b3.metric("Budget remaining", money(remaining) if result else "—")

    if result:
        if workflow_status == "VALIDATED":
            st.success("Workflow reports a validated plan. Review each line before acting.")
        elif workflow_status == "REJECTED":
            st.error("Workflow rejected the plan. Do not use it for purchasing.")
        else:
            st.warning(f"Workflow status: {workflow_status}")

        if not plan_df.empty:
            st.dataframe(plan_df, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇ Export purchase plan",
                data=plan_df.to_csv(index=False).encode("utf-8"),
                file_name="stockpilot_purchase_plan.csv",
                mime="text/csv",
            )
        else:
            st.info("The workflow returned no purchase-plan rows.")

        st.divider()
        heading("Independent validation", "Results reported by the Critic Agent.")

        checks = validation.get("passed", [])
        warnings = validation.get("warnings", [])
        errors = validation.get("errors", [])

        v1, v2, v3 = st.columns(3)
        v1.metric("Checks passed", len(checks))
        v2.metric("Warnings", len(warnings))
        v3.metric("Errors", len(errors))

        with st.expander("✓ Passed checks", expanded=True):
            if checks:
                for item in checks:
                    st.markdown(f"- {item}")
            else:
                st.caption("No passed checks were reported.")

        with st.expander("⚠ Warnings"):
            if warnings:
                for item in warnings:
                    st.warning(item)
            else:
                st.caption("No warnings reported.")

        with st.expander("✕ Validation errors"):
            if errors:
                for item in errors:
                    st.error(item)
            else:
                st.caption("No validation errors reported.")
    else:
        st.info("No purchase plan yet. Go to Command Center and run the agents to generate one.")

        if st.button("▶ Generate replenishment plan", type="primary"):
            try:
                with st.spinner("Analyzing inventory and validating orders..."):
                    st.session_state.workflow_result = StockPilotWorkflow().run(inventory, budget)
                st.rerun()
            except Exception as exc:
                st.error(f"Workflow failed: {exc}")
                st.exception(exc)


# ─────────────────────────────────────────────────────────────
# PAGE: AGENT ACTIVITY
# ─────────────────────────────────────────────────────────────
elif page == "Agent Activity":
    heading("Agent activity", "Inspect the execution trace produced by the orchestration workflow.")

    if result:
        st.markdown(
            f"""
            <div class="info-card">
              <div class="info-label">WORKFLOW STATE</div>
              <div class="info-value" style="color:{status_color}">{workflow_status}</div>
              <div class="info-note">Revision attempts: {result.get('revision_attempts', 0)} · Validation: {validation.get('status', 'UNKNOWN')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("")
        events_df = pd.DataFrame(events)

        if not events_df.empty:
            if "status" in events_df.columns:
                completed = int(events_df["status"].astype(str).str.upper().eq("COMPLETED").sum())
                failed = int(events_df["status"].astype(str).str.upper().isin(["FAILED", "REJECTED", "FAIL"]).sum())
            else:
                completed, failed = 0, 0

            e1, e2, e3 = st.columns(3)
            e1.metric("Events logged", len(events_df))
            e2.metric("Completed events", completed)
            e3.metric("Failed / rejected events", failed)

            st.dataframe(events_df, use_container_width=True, hide_index=True)

            if "agent" in events_df.columns and "status" in events_df.columns:
                counts = (
                    events_df.groupby(["agent", "status"])
                    .size().reset_index(name="Events")
                )
                fig = px.bar(
                    counts,
                    x="agent",
                    y="Events",
                    color="status",
                    barmode="group",
                    color_discrete_sequence=[GREEN, BLUE, AMBER, RED],
                )
                fig.update_layout(xaxis_title="", yaxis_title="Logged events")
                st.plotly_chart(style_chart(fig, 330), use_container_width=True)

            st.download_button(
                "⬇ Download execution log",
                data=events_df.to_csv(index=False).encode("utf-8"),
                file_name="stockpilot_execution_log.csv",
                mime="text/csv",
            )
        else:
            st.info("No events were returned by the workflow.")
    else:
        st.info("Run the workflow first. The orchestration trace will appear here.")

        st.markdown("""
        <div class="info-card">
          <div class="info-label">WORKFLOW DESIGN</div>
          <div style="font-size:14px;line-height:2;color:#EDF4FF;">
            01 &nbsp; Planner Agent — task sequencing<br>
            02 &nbsp; Inventory Analyst — demand and stock-risk analysis<br>
            03 &nbsp; Replenishment Agent — budget-aware order proposal<br>
            04 &nbsp; Critic Agent — independent validation<br>
            05 &nbsp; Orchestrator — bounded retries and final status
          </div>
          <div class="info-note">Agent roles are shown from the project design; actual execution details appear after a run.</div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("<br><hr>", unsafe_allow_html=True)
footer_left, footer_right = st.columns([2, 1])
with footer_left:
    st.caption("STOCKPILOT AI  ·  AGENTIC RETAIL INVENTORY PLANNING")
with footer_right:
    st.caption("Academic proof of concept · Human review required")
