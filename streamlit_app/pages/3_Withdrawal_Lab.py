"""Withdrawal Strategy Lab page."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import streamlit as st

from fundedness.models.simulation import SimulationConfig
from fundedness.viz.comparison import (
    create_multi_metric_comparison,
    create_strategy_comparison_chart,
    create_strategy_metrics_table,
)
from fundedness.withdrawals.comparison import compare_strategies
from fundedness.withdrawals.fixed_swr import FixedRealSWRPolicy, PercentOfPortfolioPolicy
from fundedness.withdrawals.guardrails import GuardrailsPolicy
from fundedness.withdrawals.rmd_style import AmortizationPolicy, RMDStylePolicy
from fundedness.withdrawals.vpw import VPWPolicy
from streamlit_app.utils.session_state import (
    get_household,
    get_market_model,
    initialize_session_state,
)

st.set_page_config(page_title="Withdrawal Lab", page_icon="💰", layout="wide")

initialize_session_state()

st.title("💰 Withdrawal Strategy Lab")

st.markdown("""
Compare different withdrawal strategies to see which approach works best for your situation.
""")

# Sidebar controls
with st.sidebar:
    st.subheader("Simulation Settings")

    n_simulations = st.select_slider(
        "Number of Simulations",
        options=[1000, 2500, 5000],
        value=2500,
    )

    stock_allocation = st.slider(
        "Stock Allocation",
        min_value=0,
        max_value=100,
        value=60,
        step=5,
        format="%d%%",
    )

    st.divider()

    st.subheader("Strategy Selection")

    use_fixed_swr = st.checkbox("Fixed 4% SWR", value=True)
    use_percent_portfolio = st.checkbox("% of Portfolio", value=True)
    use_guardrails = st.checkbox("Guardrails", value=True)
    use_vpw = st.checkbox("VPW", value=True)
    use_rmd = st.checkbox("RMD-Style", value=False)
    use_amortization = st.checkbox("Amortization", value=False)

# Get data
household = get_household()
market_model = get_market_model()

initial_wealth = household.total_assets
spending_floor = household.essential_spending
starting_age = 65
if household.primary_member:
    starting_age = household.primary_member.age

# Build list of strategies to compare
policies = []

if use_fixed_swr:
    policies.append(FixedRealSWRPolicy(withdrawal_rate=0.04, floor_spending=spending_floor))

if use_percent_portfolio:
    policies.append(PercentOfPortfolioPolicy(withdrawal_rate=0.04, floor=spending_floor))

if use_guardrails:
    policies.append(GuardrailsPolicy(
        initial_rate=0.05,
        upper_guardrail=0.06,
        lower_guardrail=0.04,
        floor_spending=spending_floor,
    ))

if use_vpw:
    policies.append(VPWPolicy(starting_age=starting_age, floor_spending=spending_floor))

if use_rmd:
    policies.append(RMDStylePolicy(starting_age=starting_age, floor_spending=spending_floor))

if use_amortization:
    policies.append(AmortizationPolicy(
        starting_age=starting_age,
        planning_age=95,
        floor_spending=spending_floor,
    ))

if not policies:
    st.warning("Please select at least one withdrawal strategy to compare.")
    st.stop()

# Run comparison
config = SimulationConfig(
    n_simulations=n_simulations,
    n_years=household.planning_horizon,
    market_model=market_model,
    random_seed=42,
)

with st.spinner(f"Comparing {len(policies)} strategies across {n_simulations:,} simulations..."):
    comparison = compare_strategies(
        policies=policies,
        initial_wealth=initial_wealth,
        config=config,
        stock_weight=stock_allocation / 100,
        starting_age=starting_age,
        spending_floor=spending_floor,
    )
    st.session_state.comparison_result = comparison

# Display metrics table
st.subheader("Strategy Comparison")

metrics_fig = create_strategy_metrics_table(
    strategies=comparison.metrics,
    metrics_to_show=[
        "success_rate",
        "median_terminal_wealth",
        "median_initial_spending",
        "average_spending",
        "spending_volatility",
        "floor_breach_rate",
    ],
)
st.plotly_chart(metrics_fig, use_container_width=True)

st.divider()

# Visualizations
tab1, tab2, tab3 = st.tabs(["📈 Wealth Paths", "💵 Spending Paths", "📊 Multi-Metric"])

years = np.arange(1, config.n_years + 1)

with tab1:
    # Prepare wealth data for comparison chart
    wealth_data = {}
    for name, result in comparison.results.items():
        wealth_data[name] = {"wealth_median": result.wealth_percentiles.get("P50", np.zeros(config.n_years))}

    wealth_fig = create_strategy_comparison_chart(
        years=years,
        strategies=wealth_data,
        metric="wealth_median",
        title="Median Wealth Over Time",
        y_label="Portfolio Value ($)",
    )
    st.plotly_chart(wealth_fig, use_container_width=True)

with tab2:
    # Prepare spending data
    spending_data = {}
    for name, result in comparison.results.items():
        spending_data[name] = {"spending_median": result.spending_percentiles.get("P50", np.zeros(config.n_years))}

    spending_fig = create_strategy_comparison_chart(
        years=years,
        strategies=spending_data,
        metric="spending_median",
        title="Median Spending Over Time",
        y_label="Annual Spending ($)",
    )
    st.plotly_chart(spending_fig, use_container_width=True)

with tab3:
    # Multi-metric comparison
    multi_data = {}
    for name, result in comparison.results.items():
        multi_data[name] = {
            "wealth_median": result.wealth_percentiles.get("P50", np.zeros(config.n_years)),
            "spending_median": result.spending_percentiles.get("P50", np.zeros(config.n_years)),
            "survival_prob": result.get_survival_probability(),
        }

    multi_fig = create_multi_metric_comparison(
        years=years,
        strategies=multi_data,
        title="Multi-Metric Strategy Comparison",
    )
    st.plotly_chart(multi_fig, use_container_width=True)

# Strategy descriptions
with st.expander("Strategy Descriptions"):
    st.markdown("""
    ### Fixed SWR (Safe Withdrawal Rate)
    The classic "4% rule" - withdraw 4% of your initial portfolio in year 1, then adjust
    for inflation each year. Simple and predictable, but doesn't adapt to market conditions.

    ### Percent of Portfolio
    Withdraw a fixed percentage (4%) of your current portfolio value each year.
    Automatically adjusts to market performance but creates volatile spending.

    ### Guardrails (Guyton-Klinger)
    Start with a higher initial rate (5%), adjust for inflation, but:
    - Cut spending by 10% if withdrawal rate exceeds 6%
    - Raise spending by 10% if withdrawal rate falls below 4%

    Provides some flexibility while avoiding extreme outcomes.

    ### VPW (Variable Percentage Withdrawal)
    Withdrawal rate varies based on age and expected remaining lifespan.
    Younger retirees withdraw less; rate increases as you age.

    ### RMD-Style
    Uses IRS Required Minimum Distribution tables to determine withdrawal rate.
    Rate automatically increases with age (e.g., ~3.6% at 72, ~5.2% at 80).

    ### Amortization
    Calculates the level payment that would exhaust the portfolio over your
    planning horizon, given expected returns. Recalculates annually.
    """)
