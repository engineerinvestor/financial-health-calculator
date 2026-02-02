"""Time Runway page with Monte Carlo projections."""

import numpy as np
import streamlit as st

from fundedness.models.simulation import SimulationConfig
from fundedness.simulate import run_simulation
from fundedness.viz.fan_chart import create_fan_chart, create_spending_fan_chart
from fundedness.viz.histogram import create_time_distribution_histogram
from fundedness.viz.survival import create_dual_survival_chart, create_survival_curve
from streamlit_app.components.metrics_display import render_simulation_metrics
from streamlit_app.utils.session_state import (
    get_household,
    get_market_model,
    get_simulation_config,
    initialize_session_state,
)

st.set_page_config(page_title="Time Runway", page_icon="📈", layout="wide")

initialize_session_state()

st.title("📈 Time Runway Analysis")

st.markdown("""
Monte Carlo simulation shows the range of possible outcomes based on market uncertainty.
""")

# Sidebar controls
with st.sidebar:
    st.subheader("Simulation Settings")

    n_simulations = st.select_slider(
        "Number of Simulations",
        options=[1000, 2500, 5000, 10000],
        value=5000,
    )

    stock_allocation = st.slider(
        "Stock Allocation",
        min_value=0,
        max_value=100,
        value=60,
        step=5,
        format="%d%%",
    )

    withdrawal_rate = st.slider(
        "Withdrawal Rate",
        min_value=2.0,
        max_value=6.0,
        value=4.0,
        step=0.25,
        format="%.2f%%",
    )

# Get data
household = get_household()
market_model = get_market_model()

# Calculate values
initial_wealth = household.total_assets
annual_spending = initial_wealth * (withdrawal_rate / 100)
spending_floor = household.essential_spending
n_years = household.planning_horizon

# Run simulation
config = SimulationConfig(
    n_simulations=n_simulations,
    n_years=n_years,
    market_model=market_model,
    random_seed=42,
)

with st.spinner(f"Running {n_simulations:,} simulations..."):
    result = run_simulation(
        initial_wealth=initial_wealth,
        annual_spending=annual_spending,
        config=config,
        stock_weight=stock_allocation / 100,
        spending_floor=spending_floor,
    )
    st.session_state.simulation_result = result

# Display metrics
render_simulation_metrics(result)

st.divider()

# Main visualizations
tab1, tab2, tab3 = st.tabs(["📈 Wealth Projection", "📊 Survival Analysis", "📉 Time to Events"])

with tab1:
    st.subheader("Portfolio Value Over Time")

    years = np.arange(1, n_years + 1)
    wealth_fig = create_fan_chart(
        years=years,
        percentiles=result.wealth_percentiles,
        title="Portfolio Value Projection",
        y_label="Portfolio Value ($)",
        show_floor=0,
    )
    st.plotly_chart(wealth_fig, use_container_width=True)

    # Spending projection if available
    if result.spending_paths is not None:
        st.subheader("Spending Over Time")
        spending_fig = create_spending_fan_chart(
            years=years,
            percentiles=result.spending_percentiles,
            floor_spending=spending_floor,
            target_spending=annual_spending,
            title="Spending Projection",
        )
        st.plotly_chart(spending_fig, use_container_width=True)

with tab2:
    st.subheader("Survival Probability")

    survival_prob = result.get_survival_probability()
    floor_survival_prob = result.get_floor_survival_probability()

    col1, col2 = st.columns(2)

    with col1:
        survival_fig = create_survival_curve(
            years=years,
            survival_prob=survival_prob,
            floor_survival_prob=floor_survival_prob,
            title="Probability of Portfolio Survival",
            threshold_years=[10, 20, 30],
        )
        st.plotly_chart(survival_fig, use_container_width=True)

    with col2:
        # Calculate cumulative risk
        ruin_prob = 1 - survival_prob
        floor_breach_prob = 1 - floor_survival_prob

        risk_fig = create_dual_survival_chart(
            years=years,
            ruin_prob=ruin_prob,
            floor_breach_prob=floor_breach_prob,
            title="Cumulative Risk Over Time",
        )
        st.plotly_chart(risk_fig, use_container_width=True)

    # Key survival metrics
    st.subheader("Key Survival Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        p_10 = survival_prob[min(9, len(survival_prob)-1)]
        st.metric("10-Year Survival", f"{p_10:.1%}")

    with col2:
        p_20 = survival_prob[min(19, len(survival_prob)-1)]
        st.metric("20-Year Survival", f"{p_20:.1%}")

    with col3:
        p_30 = survival_prob[min(29, len(survival_prob)-1)]
        st.metric("30-Year Survival", f"{p_30:.1%}")

    with col4:
        final_p = survival_prob[-1]
        st.metric(f"{n_years}-Year Survival", f"{final_p:.1%}")

with tab3:
    st.subheader("Time to Event Distributions")

    col1, col2 = st.columns(2)

    with col1:
        if result.time_to_ruin is not None:
            ruin_hist = create_time_distribution_histogram(
                time_to_event=result.time_to_ruin,
                event_name="Ruin",
                planning_horizon=n_years,
                percentiles_to_show=[10, 25, 50],
                title="Time to Portfolio Depletion",
            )
            st.plotly_chart(ruin_hist, use_container_width=True)

    with col2:
        if result.time_to_floor_breach is not None:
            floor_hist = create_time_distribution_histogram(
                time_to_event=result.time_to_floor_breach,
                event_name="Floor Breach",
                planning_horizon=n_years,
                percentiles_to_show=[10, 25, 50],
                title="Time to Floor Breach",
            )
            st.plotly_chart(floor_hist, use_container_width=True)

# Interpretation
with st.expander("Understanding the Results"):
    st.markdown(f"""
    ### Simulation Summary

    - **Initial Portfolio**: ${initial_wealth:,.0f}
    - **Annual Spending**: ${annual_spending:,.0f} ({withdrawal_rate:.2f}% withdrawal rate)
    - **Essential Spending Floor**: ${spending_floor:,.0f}
    - **Stock Allocation**: {stock_allocation}%
    - **Planning Horizon**: {n_years} years

    ### Interpretation

    - **Success Rate ({result.success_rate:.1%})**: The percentage of simulations where the portfolio lasted the full {n_years} years
    - **Floor Breach Rate ({result.floor_breach_rate:.1%})**: The percentage of simulations where spending had to be cut below essential needs
    - **P10/P50/P90**: The 10th, 50th (median), and 90th percentile outcomes

    ### Key Insights

    {"✅ Your success rate is above 90%, suggesting a sustainable withdrawal rate." if result.success_rate >= 0.9 else ""}
    {"⚠️ Your success rate is between 75-90%. Consider reducing spending or increasing savings." if 0.75 <= result.success_rate < 0.9 else ""}
    {"🚨 Your success rate is below 75%. Significant adjustments may be needed." if result.success_rate < 0.75 else ""}
    """)
