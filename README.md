# StockPilot AI — Agentic Retail Inventory Management

StockPilot AI is a multi-agent inventory management and decision-support system designed to make retail inventory planning smarter, more efficient, and budget-aware.

The project explores how AI agents can collaborate to analyze inventory levels, identify potential stockouts, recommend replenishment quantities, and validate purchasing decisions against budget constraints.

## Overview

Managing retail inventory involves balancing product availability, customer demand, supplier lead times, and purchasing costs. StockPilot AI addresses this challenge through a coordinated agent workflow that transforms inventory data into actionable replenishment recommendations.

The application features an interactive dashboard for exploring inventory data, reviewing stock risks, analyzing purchasing recommendations, and monitoring agent activity.

## Features

- **Inventory Monitoring:** Analyze current stock, sales demand, supplier lead times, unit costs, and safety stock.
- **Stockout Risk Analysis:** Identify products that may require replenishment.
- **Intelligent Replenishment:** Calculate suggested order quantities using inventory planning formulas.
- **Budget-Aware Purchasing:** Prioritize replenishment recommendations within a specified purchasing budget.
- **Multi-Agent Orchestration:** Coordinate specialized agents through a central workflow.
- **Independent Plan Validation:** Evaluate proposed purchasing plans against validation and budget constraints.
- **Interactive Dashboard:** Explore inventory metrics, product data, replenishment plans, and agent execution logs.
- **Synthetic Data Generation:** Generate sample retail inventory data for experimentation.
- **CSV Import and Export:** Work with inventory data through supported CSV workflows.
- **Automated Testing:** Use Pytest to validate calculations, input handling, and workflow behavior.

## Agent Architecture

StockPilot AI uses a modular multi-agent architecture in which specialized agents collaborate through a central orchestration workflow.

### 1. Planner Agent

Coordinates the planning process and determines the sequence of inventory analysis and replenishment tasks.

### 2. Inventory Analyst Agent

Evaluates stock levels, sales demand, supplier lead times, and safety stock to identify products that may need replenishment.

### 3. Replenishment Agent

Calculates suggested order quantities and estimates purchase costs based on inventory planning rules.

### 4. Critic / Validator Agent

Reviews the proposed purchasing plan, checks applicable constraints, and identifies issues that require correction.

### Central Orchestrator

The orchestration layer coordinates the agents, manages workflow execution, records agent events, and supports bounded revision attempts where implemented.

## Technology Stack

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Pytest

## Project Structure

    StockPilot-AI/
    ├── agents/
    ├── orchestration/
    ├── data/
    ├── utils/
    ├── tests/
    ├── docs/
    ├── app.py
    ├── requirements.txt
    ├── README.md
    └── .gitignore

## Installation

### Prerequisites

- Python 3.10 or later
- Git

### Clone the Repository

    git clone https://github.com/Karmanya-Singh30/StockPilot-AI.git
    cd StockPilot-AI

### Create a Virtual Environment

On Windows PowerShell:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

### Install Dependencies

    python -m pip install -r requirements.txt

### Launch the Application

    streamlit run app.py

Once Streamlit starts, open the local URL displayed in the terminal to access the dashboard.

## Inventory Planning Logic

StockPilot AI uses standard inventory planning calculations to generate replenishment recommendations.

### Average Daily Demand

Average Daily Demand = Units Sold / Sales Period in Days

This estimates average product demand per day from the available sales history.

### Reorder Point

Reorder Point = (Average Daily Demand × Supplier Lead Time) + Safety Stock

This estimates the stock level at which replenishment should be considered.

### Target Stock

Target Stock = Average Daily Demand × (Supplier Lead Time + Additional Coverage Days)

This estimates the desired inventory level based on supplier lead time and additional coverage requirements.

### Suggested Order Quantity

Suggested Order Quantity = Maximum of 0 and (Target Stock − Current Stock)

This estimates how much additional inventory is required to reach the target stock level.

### Estimated Purchase Cost

Estimated Purchase Cost = Suggested Order Quantity × Unit Cost

These calculations provide the basis for replenishment planning. Zero-demand products and invalid inputs should be handled according to the implemented validation logic.

## Budget-Aware Decision Making

A central goal of StockPilot AI is to make replenishment recommendations practical under purchasing constraints.

The workflow evaluates proposed orders against a specified budget and is designed to prioritize critical inventory requirements while keeping approved purchasing plans within the available budget.

The final recommendations depend on the inventory data, prioritization rules, and validation logic implemented in the system.

## Testing

Run the automated test suite using:

    python -m pytest -v

Tests cover the behaviors implemented in the project, including inventory calculations, validation, and workflow execution.

Test counts and pass rates should be reported only after executing the suite and reviewing its actual output.

## Limitations

- Synthetic data may not reflect real retail demand patterns.
- Basic demand calculations may not capture seasonality, promotions, or sudden changes in customer behavior.
- Recommendations depend on the accuracy of inventory, sales, supplier, and cost information.
- Budget prioritization is limited by the rules implemented in the workflow.
- The system is a prototype and may require additional integrations, monitoring, and reliability improvements before production use.

## Future Improvements

- Integration with live inventory management systems
- Advanced demand forecasting and seasonal analysis
- Supplier reliability and delivery-time analysis
- Historical inventory trends and sales forecasting
- Persistent database integration
- More detailed explanations for agent recommendations
- Expanded testing with real-world retail datasets
- Deployment as a hosted web application

## About

StockPilot AI explores the use of multi-agent systems for retail inventory intelligence, replenishment planning, and budget-aware decision support.

The goal is to demonstrate how specialized AI agents, deterministic inventory calculations, and independent validation can work together to support more informed inventory decisions.

## Repository

GitHub: https://github.com/Karmanya-Singh30/StockPilot-AI
