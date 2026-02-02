"""Utility Optimization page - Merton optimal spending and allocation."""

import numpy as np
import streamlit as st

from fundedness.allocation.constant import ConstantAllocationPolicy
from fundedness.allocation.merton_optimal import MertonOptimalAllocationPolicy
from fundedness.merton import calculate_merton_optimal, merton_optimal_allocation
from fundedness.models.simulation import SimulationConfig
from fundedness.models.utility import UtilityModel
from fundedness.simulate import run_simulation_with_utility
from fundedness.viz.optimal import (
    create_optimal_allocation_curve,
    create_optimal_policy_summary,
    create_optimal_spending_curve,
    create_sensitivity_heatmap,
    create_spending_comparison_by_age,
    create_utility_comparison_chart,
)
from fundedness.withdrawals.fixed_swr import FixedRealSWRPolicy
from fundedness.withdrawals.merton_optimal import MertonOptimalSpendingPolicy
from streamlit_app.utils.session_state import (
    get_household,
    get_market_model,
    initialize_session_state,
)

st.set_page_config(page_title="Utility Optimization", page_icon="", layout="wide")

initialize_session_state()

st.title("Utility Optimization")
st.markdown("""
Explore utility-optimal retirement spending and allocation based on
Merton's optimal consumption and portfolio choice theory.

This approach finds the spending rate and asset allocation that maximize your
expected lifetime utility, accounting for your risk aversion and time preferences.
""")

# Get data from session
household = get_household()
market_model = get_market_model()

initial_wealth = household.total_assets
spending_floor = household.essential_spending
starting_age = 65
if household.primary_member:
    starting_age = household.primary_member.age

# Sidebar controls
with st.sidebar:
    st.subheader("Utility Parameters")

    gamma = st.slider(
        "Risk Aversion (gamma)",
        min_value=1.0,
        max_value=6.0,
        value=3.0,
        step=0.5,
        help="Higher gamma = more risk averse. Typical values: 2-5",
    )

    time_preference = st.slider(
        "Time Preference (%)",
        min_value=0.0,
        max_value=5.0,
        value=2.0,
        step=0.5,
        help="Rate at which you discount future consumption",
    ) / 100

    subsistence_floor = st.number_input(
        "Subsistence Floor ($)",
        min_value=0,
        max_value=200000,
        value=int(spending_floor),
        step=5000,
        help="Minimum annual spending to maintain",
    )

    st.divider()

    st.subheader("Planning Horizon")

    end_age = st.slider(
        "Planning End Age",
        min_value=80,
        max_value=110,
        value=95,
        help="Age to plan until (life expectancy)",
    )

    st.divider()

    st.subheader("Simulation Settings")

    n_simulations = st.select_slider(
        "Number of Simulations",
        options=[500, 1000, 2500, 5000],
        value=1000,
    )

# Create utility model
utility_model = UtilityModel(
    gamma=gamma,
    subsistence_floor=subsistence_floor,
    time_preference=time_preference,
)

# Calculate optimal values
remaining_years = end_age - starting_age
optimal = calculate_merton_optimal(
    wealth=initial_wealth,
    market_model=market_model,
    utility_model=utility_model,
    remaining_years=remaining_years,
)

# Display key metrics
st.subheader("Your Optimal Policy")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Optimal Equity Allocation",
        f"{optimal.optimal_equity_allocation:.0%}",
        help="Unconstrained Merton optimal allocation",
    )

with col2:
    st.metric(
        "Wealth-Adjusted Allocation",
        f"{optimal.wealth_adjusted_allocation:.0%}",
        help="Adjusted for your distance from subsistence floor",
    )

with col3:
    st.metric(
        "Optimal Spending Rate",
        f"{optimal.optimal_spending_rate:.1%}",
        help=f"For your {remaining_years}-year horizon",
    )

with col4:
    initial_spending = initial_wealth * optimal.optimal_spending_rate
    st.metric(
        "Year 1 Spending",
        f"${initial_spending:,.0f}",
        help="Based on current wealth",
    )

st.divider()

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs([
    "Optimal Curves",
    "Strategy Comparison",
    "Parameter Sensitivity",
    "Detailed Analysis",
])

with tab1:
    st.subheader("Optimal Policy Curves")

    col1, col2 = st.columns(2)

    with col1:
        # Allocation vs wealth curve
        alloc_fig = create_optimal_allocation_curve(
            market_model=market_model,
            utility_model=utility_model,
            max_wealth=initial_wealth * 3,
            title="Optimal Equity Allocation vs Wealth",
        )
        st.plotly_chart(alloc_fig, use_container_width=True)

        st.markdown("""
        **Key Insight:** As wealth approaches the subsistence floor, optimal
        equity allocation drops to zero - you can't afford to take risk.
        As wealth increases above the floor, allocation approaches the
        unconstrained Merton optimal.
        """)

    with col2:
        # Spending rate vs age curve
        spending_fig = create_optimal_spending_curve(
            market_model=market_model,
            utility_model=utility_model,
            starting_age=starting_age,
            end_age=end_age,
            title="Optimal Spending Rate vs Age",
        )
        st.plotly_chart(spending_fig, use_container_width=True)

        st.markdown("""
        **Key Insight:** Optimal spending rate increases with age as the
        remaining horizon shortens. This differs significantly from the
        fixed 4% rule, which doesn't adapt to age.
        """)

with tab2:
    st.subheader("Strategy Comparison: Merton Optimal vs 4% Rule")

    # Run comparison simulation
    config = SimulationConfig(
        n_simulations=n_simulations,
        n_years=remaining_years,
        market_model=market_model,
        random_seed=42,
    )

    # Policies to compare
    merton_spending = MertonOptimalSpendingPolicy(
        market_model=market_model,
        utility_model=utility_model,
        starting_age=starting_age,
        end_age=end_age,
        floor_spending=subsistence_floor,
    )
    merton_allocation = MertonOptimalAllocationPolicy(
        market_model=market_model,
        utility_model=utility_model,
    )

    fixed_spending = FixedRealSWRPolicy(
        withdrawal_rate=0.04,
        floor_spending=subsistence_floor,
    )
    fixed_allocation = ConstantAllocationPolicy(stock_weight=0.6)

    with st.spinner("Running simulations..."):
        # Run Merton optimal simulation
        merton_result = run_simulation_with_utility(
            initial_wealth=initial_wealth,
            spending_policy=merton_spending,
            allocation_policy=merton_allocation,
            config=config,
            utility_model=utility_model,
            spending_floor=subsistence_floor,
        )

        # Run fixed 4% simulation
        fixed_result = run_simulation_with_utility(
            initial_wealth=initial_wealth,
            spending_policy=fixed_spending,
            allocation_policy=fixed_allocation,
            config=config,
            utility_model=utility_model,
            spending_floor=subsistence_floor,
        )

    # Display comparison metrics
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Merton Optimal")
        st.metric("Expected Utility", f"{merton_result.expected_lifetime_utility:.2e}")
        st.metric("CE Consumption", f"${merton_result.certainty_equivalent_consumption:,.0f}/yr")
        st.metric("Success Rate", f"{merton_result.success_rate:.1%}")
        st.metric("Median Terminal Wealth", f"${merton_result.median_terminal_wealth:,.0f}")

    with col2:
        st.markdown("### Fixed 4% / 60-40")
        st.metric("Expected Utility", f"{fixed_result.expected_lifetime_utility:.2e}")
        st.metric("CE Consumption", f"${fixed_result.certainty_equivalent_consumption:,.0f}/yr")
        st.metric("Success Rate", f"{fixed_result.success_rate:.1%}")
        st.metric("Median Terminal Wealth", f"${fixed_result.median_terminal_wealth:,.0f}")

    # Utility comparison chart
    util_fig = create_utility_comparison_chart(
        strategy_names=["Merton Optimal", "Fixed 4% / 60-40"],
        expected_utilities=[
            merton_result.expected_lifetime_utility,
            fixed_result.expected_lifetime_utility,
        ],
        certainty_equivalents=[
            merton_result.certainty_equivalent_consumption,
            fixed_result.certainty_equivalent_consumption,
        ],
        title="Utility Comparison",
    )
    st.plotly_chart(util_fig, use_container_width=True)

    # Spending comparison
    spending_comparison_fig = create_spending_comparison_by_age(
        market_model=market_model,
        utility_model=utility_model,
        initial_wealth=initial_wealth,
        starting_age=starting_age,
        end_age=end_age,
        title="Annual Spending: Merton Optimal vs 4% Rule",
    )
    st.plotly_chart(spending_comparison_fig, use_container_width=True)

with tab3:
    st.subheader("Parameter Sensitivity Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # Spending rate sensitivity
        spending_heatmap = create_sensitivity_heatmap(
            market_model=market_model,
            gamma_range=(1.5, 5.0),
            rtp_range=(0.01, 0.05),
            metric="spending_rate",
            title="Optimal Spending Rate Sensitivity",
        )
        st.plotly_chart(spending_heatmap, use_container_width=True)

        st.markdown("""
        **Reading the heatmap:**
        - Higher risk aversion (gamma) generally leads to lower spending rates
        - Higher time preference leads to higher spending rates (prefer now vs later)
        """)

    with col2:
        # Allocation sensitivity
        alloc_heatmap = create_sensitivity_heatmap(
            market_model=market_model,
            gamma_range=(1.5, 5.0),
            rtp_range=(0.01, 0.05),
            metric="allocation",
            title="Optimal Equity Allocation Sensitivity",
        )
        st.plotly_chart(alloc_heatmap, use_container_width=True)

        st.markdown("""
        **Reading the heatmap:**
        - Higher risk aversion strongly reduces optimal equity allocation
        - Time preference has minimal effect on allocation
        """)

with tab4:
    st.subheader("Detailed Optimal Policy Analysis")

    # Policy summary gauges
    summary_fig = create_optimal_policy_summary(
        market_model=market_model,
        utility_model=utility_model,
        wealth=initial_wealth,
        starting_age=starting_age,
        end_age=end_age,
    )
    st.plotly_chart(summary_fig, use_container_width=True)

    st.markdown("---")

    st.markdown("### Merton Formula Breakdown")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        **Market Assumptions:**
        - Stock Return: {market_model.stock_return:.1%}
        - Bond Return: {market_model.bond_return:.1%}
        - Stock Volatility: {market_model.stock_volatility:.1%}
        - Risk Premium: {optimal.risk_premium:.1%}
        """)

    with col2:
        st.markdown(f"""
        **Your Preferences:**
        - Risk Aversion (gamma): {gamma}
        - Time Preference: {time_preference:.1%}
        - Subsistence Floor: ${subsistence_floor:,}
        """)

    st.markdown("---")

    st.markdown("### The Math Behind the Numbers")

    with st.expander("Optimal Equity Allocation Formula"):
        st.latex(r"k^* = \frac{\mu - r}{\gamma \times \sigma^2}")
        st.markdown(f"""
        Where:
        - $\\mu$ = expected stock return = {market_model.stock_return:.1%}
        - $r$ = bond return = {market_model.bond_return:.1%}
        - $\\gamma$ = risk aversion = {gamma}
        - $\\sigma$ = stock volatility = {market_model.stock_volatility:.1%}

        Result: $k^*$ = {optimal.optimal_equity_allocation:.1%}
        """)

    with st.expander("Certainty Equivalent Return Formula"):
        st.latex(r"r_{CE} = r + k^*(\mu - r) - \frac{\gamma \times k^{*2} \times \sigma^2}{2}")
        st.markdown(f"""
        The certainty equivalent return is the guaranteed return that provides
        the same utility as the risky portfolio.

        Result: $r_{{CE}}$ = {optimal.certainty_equivalent_return:.2%}
        """)

    with st.expander("Optimal Spending Rate Formula"):
        st.latex(r"c^* = r_{CE} - \frac{r_{CE} - \rho}{\gamma}")
        st.markdown(f"""
        Where:
        - $r_{{CE}}$ = certainty equivalent return = {optimal.certainty_equivalent_return:.2%}
        - $\\rho$ = time preference = {time_preference:.1%}
        - $\\gamma$ = risk aversion = {gamma}

        Result: $c^*$ = {optimal.optimal_spending_rate:.2%} (for infinite horizon)

        With your {remaining_years}-year horizon, the rate adjusts to
        {optimal.optimal_spending_rate:.1%}.
        """)

    with st.expander("Wealth-Adjusted Allocation"):
        st.latex(r"k_{adj} = k^* \times \frac{W - F}{W}")
        st.markdown(f"""
        Near the subsistence floor, you can't afford to take risk:

        - $W$ = current wealth = ${initial_wealth:,}
        - $F$ = subsistence floor = ${subsistence_floor:,}
        - Distance from floor: ${initial_wealth - subsistence_floor:,}

        Adjustment factor: {(initial_wealth - subsistence_floor) / initial_wealth:.1%}

        Result: Adjusted allocation = {optimal.wealth_adjusted_allocation:.0%}
        """)

# Footer
st.divider()
st.markdown("""
**About This Methodology**

This page implements utility-optimal retirement planning based on Robert Merton's
Nobel Prize-winning work on optimal consumption and portfolio choice. For accessible
treatments of these concepts, see Haghani & White's *The Missing Billionaires* (2023)
and research from [Elm Wealth](https://elmwealth.com/).

Key insights:
1. **Spending rate should increase with age** as the remaining horizon shortens
2. **Allocation should decrease as wealth falls** toward the subsistence floor
3. **Risk aversion (gamma) is the critical input** - know your own risk tolerance
4. **The 4% rule is suboptimal** for most investors from a utility perspective
""")
