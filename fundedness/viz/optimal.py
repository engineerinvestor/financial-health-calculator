"""Visualization components for utility optimization and optimal policies."""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fundedness.merton import (
    optimal_allocation_by_wealth,
    optimal_spending_by_age,
    merton_optimal_allocation,
    merton_optimal_spending_rate,
)
from fundedness.models.market import MarketModel
from fundedness.models.utility import UtilityModel
from fundedness.viz.colors import COLORS, get_plotly_layout_defaults


def create_optimal_allocation_curve(
    market_model: MarketModel,
    utility_model: UtilityModel,
    max_wealth: float = 3_000_000,
    n_points: int = 100,
    title: str = "Optimal Equity Allocation by Wealth",
) -> go.Figure:
    """Create a chart showing optimal equity allocation vs wealth.

    Shows how allocation should decrease as wealth approaches the
    subsistence floor.

    Args:
        market_model: Market assumptions
        utility_model: Utility parameters
        max_wealth: Maximum wealth to show on x-axis
        n_points: Number of points to plot
        title: Chart title

    Returns:
        Plotly Figure object
    """
    floor = utility_model.subsistence_floor
    wealth_levels = np.linspace(floor * 0.5, max_wealth, n_points)

    allocations = optimal_allocation_by_wealth(
        market_model=market_model,
        utility_model=utility_model,
        wealth_levels=wealth_levels,
    )

    # Unconstrained optimal
    k_star = merton_optimal_allocation(market_model, utility_model)

    fig = go.Figure()

    # Main allocation curve
    fig.add_trace(go.Scatter(
        x=wealth_levels,
        y=allocations * 100,
        mode="lines",
        name="Optimal Allocation",
        line=dict(color=COLORS["wealth_primary"], width=3),
        hovertemplate="Wealth: $%{x:,.0f}<br>Equity: %{y:.1f}%<extra></extra>",
    ))

    # Unconstrained optimal line
    fig.add_trace(go.Scatter(
        x=[wealth_levels[0], wealth_levels[-1]],
        y=[k_star * 100, k_star * 100],
        mode="lines",
        name=f"Unconstrained Optimal ({k_star:.0%})",
        line=dict(color=COLORS["neutral_secondary"], width=2, dash="dash"),
    ))

    # Floor line
    fig.add_trace(go.Scatter(
        x=[floor, floor],
        y=[0, k_star * 100],
        mode="lines",
        name=f"Subsistence Floor (${floor:,.0f})",
        line=dict(color=COLORS["danger_primary"], width=2, dash="dot"),
    ))

    # Layout
    layout = get_plotly_layout_defaults()
    layout.update(
        title=dict(text=title),
        xaxis=dict(
            title="Wealth ($)",
            tickformat="$,.0f",
            range=[0, max_wealth],
        ),
        yaxis=dict(
            title="Equity Allocation (%)",
            range=[0, min(100, k_star * 100 + 10)],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        showlegend=True,
    )
    fig.update_layout(**layout)

    return fig


def create_optimal_spending_curve(
    market_model: MarketModel,
    utility_model: UtilityModel,
    starting_age: int = 65,
    end_age: int = 100,
    title: str = "Optimal Spending Rate by Age",
    show_comparison: bool = True,
) -> go.Figure:
    """Create a chart showing optimal spending rate vs age.

    Shows how spending rate should increase as remaining horizon shortens.

    Args:
        market_model: Market assumptions
        utility_model: Utility parameters
        starting_age: Starting age to plot
        end_age: Ending age to plot
        title: Chart title
        show_comparison: Whether to show 4% rule comparison

    Returns:
        Plotly Figure object
    """
    rates = optimal_spending_by_age(
        market_model=market_model,
        utility_model=utility_model,
        starting_age=starting_age,
        end_age=end_age,
    )

    ages = list(rates.keys())
    spending_rates = [rates[age] * 100 for age in ages]

    fig = go.Figure()

    # Main spending curve
    fig.add_trace(go.Scatter(
        x=ages,
        y=spending_rates,
        mode="lines",
        name="Merton Optimal",
        line=dict(color=COLORS["success_primary"], width=3),
        hovertemplate="Age: %{x}<br>Spending Rate: %{y:.1f}%<extra></extra>",
    ))

    # 4% rule comparison
    if show_comparison:
        fig.add_trace(go.Scatter(
            x=ages,
            y=[4.0] * len(ages),
            mode="lines",
            name="Fixed 4% Rule",
            line=dict(color=COLORS["warning_primary"], width=2, dash="dash"),
        ))

    # Infinite horizon rate
    infinite_rate = merton_optimal_spending_rate(market_model, utility_model) * 100
    fig.add_trace(go.Scatter(
        x=[starting_age, end_age],
        y=[infinite_rate, infinite_rate],
        mode="lines",
        name=f"Infinite Horizon ({infinite_rate:.1f}%)",
        line=dict(color=COLORS["neutral_secondary"], width=1, dash="dot"),
    ))

    layout = get_plotly_layout_defaults()
    layout.update(
        title=dict(text=title),
        xaxis=dict(
            title="Age",
            range=[starting_age, end_age],
        ),
        yaxis=dict(
            title="Spending Rate (%)",
            range=[0, max(15, max(spending_rates) + 2)],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
    )
    fig.update_layout(**layout)

    return fig


def create_utility_comparison_chart(
    strategy_names: list[str],
    expected_utilities: list[float],
    certainty_equivalents: list[float],
    title: str = "Utility Comparison Across Strategies",
) -> go.Figure:
    """Create a comparison chart of utility metrics across strategies.

    Shows both expected lifetime utility and certainty equivalent
    consumption for each strategy.

    Args:
        strategy_names: Names of strategies being compared
        expected_utilities: Expected lifetime utility for each strategy
        certainty_equivalents: CE consumption for each strategy
        title: Chart title

    Returns:
        Plotly Figure object
    """
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Expected Lifetime Utility", "Certainty Equivalent Consumption"),
        horizontal_spacing=0.15,
    )

    # Normalize utilities for display (shift to positive)
    min_utility = min(expected_utilities)
    display_utilities = [u - min_utility + 1 for u in expected_utilities]

    # Utility bar chart
    fig.add_trace(
        go.Bar(
            x=strategy_names,
            y=display_utilities,
            marker_color=COLORS["wealth_primary"],
            text=[f"{u:.2e}" for u in expected_utilities],
            textposition="outside",
            hovertemplate="%{x}<br>Utility: %{text}<extra></extra>",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    # CE consumption bar chart
    fig.add_trace(
        go.Bar(
            x=strategy_names,
            y=certainty_equivalents,
            marker_color=COLORS["success_primary"],
            text=[f"${ce:,.0f}" for ce in certainty_equivalents],
            textposition="outside",
            hovertemplate="%{x}<br>CE: %{text}<extra></extra>",
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    layout = get_plotly_layout_defaults()
    layout.update(
        title=dict(text=title),
        height=400,
    )
    fig.update_layout(**layout)

    fig.update_yaxes(title_text="Utility (shifted)", row=1, col=1)
    fig.update_yaxes(title_text="CE Consumption ($)", tickformat="$,.0f", row=1, col=2)

    return fig


def create_optimal_policy_summary(
    market_model: MarketModel,
    utility_model: UtilityModel,
    wealth: float,
    starting_age: int = 65,
    end_age: int = 100,
    title: str = "Optimal Policy Summary",
) -> go.Figure:
    """Create a summary chart showing key optimal policy values.

    Displays optimal allocation, spending rate, and other key metrics
    in a combined visualization.

    Args:
        market_model: Market assumptions
        utility_model: Utility parameters
        wealth: Current wealth level
        starting_age: Current age
        end_age: Planning horizon end age
        title: Chart title

    Returns:
        Plotly Figure object
    """
    from fundedness.merton import calculate_merton_optimal

    remaining_years = end_age - starting_age
    result = calculate_merton_optimal(
        wealth=wealth,
        market_model=market_model,
        utility_model=utility_model,
        remaining_years=remaining_years,
    )

    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}],
               [{"type": "indicator"}, {"type": "indicator"}]],
        subplot_titles=(
            "Optimal Equity Allocation",
            "Wealth-Adjusted Allocation",
            "Optimal Spending Rate",
            "Certainty Equivalent Return",
        ),
    )

    # Optimal allocation gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=result.optimal_equity_allocation * 100,
            number={"suffix": "%"},
            gauge=dict(
                axis=dict(range=[0, 100]),
                bar=dict(color=COLORS["wealth_primary"]),
                steps=[
                    {"range": [0, 40], "color": COLORS["success_light"]},
                    {"range": [40, 70], "color": COLORS["warning_light"]},
                    {"range": [70, 100], "color": COLORS["danger_light"]},
                ],
            ),
        ),
        row=1,
        col=1,
    )

    # Wealth-adjusted allocation gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=result.wealth_adjusted_allocation * 100,
            number={"suffix": "%"},
            gauge=dict(
                axis=dict(range=[0, 100]),
                bar=dict(color=COLORS["accent_primary"]),
                steps=[
                    {"range": [0, 40], "color": COLORS["success_light"]},
                    {"range": [40, 70], "color": COLORS["warning_light"]},
                    {"range": [70, 100], "color": COLORS["danger_light"]},
                ],
            ),
        ),
        row=1,
        col=2,
    )

    # Spending rate gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=result.optimal_spending_rate * 100,
            number={"suffix": "%"},
            gauge=dict(
                axis=dict(range=[0, 15]),
                bar=dict(color=COLORS["success_primary"]),
                steps=[
                    {"range": [0, 4], "color": COLORS["success_light"]},
                    {"range": [4, 7], "color": COLORS["warning_light"]},
                    {"range": [7, 15], "color": COLORS["danger_light"]},
                ],
            ),
        ),
        row=2,
        col=1,
    )

    # CE return gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=result.certainty_equivalent_return * 100,
            number={"suffix": "%"},
            gauge=dict(
                axis=dict(range=[0, 8]),
                bar=dict(color=COLORS["neutral_primary"]),
                steps=[
                    {"range": [0, 2], "color": COLORS["danger_light"]},
                    {"range": [2, 4], "color": COLORS["warning_light"]},
                    {"range": [4, 8], "color": COLORS["success_light"]},
                ],
            ),
        ),
        row=2,
        col=2,
    )

    layout = get_plotly_layout_defaults()
    layout.update(
        title=dict(text=title),
        height=500,
    )
    fig.update_layout(**layout)

    return fig


def create_spending_comparison_by_age(
    market_model: MarketModel,
    utility_model: UtilityModel,
    initial_wealth: float,
    starting_age: int = 65,
    end_age: int = 95,
    swr_rate: float = 0.04,
    title: str = "Spending Comparison: Merton Optimal vs 4% Rule",
) -> go.Figure:
    """Compare dollar spending between Merton optimal and fixed SWR.

    Shows how absolute spending differs over time, not just rates.

    Args:
        market_model: Market assumptions
        utility_model: Utility parameters
        initial_wealth: Starting portfolio value
        starting_age: Starting age
        end_age: Ending age
        swr_rate: Fixed SWR rate for comparison
        title: Chart title

    Returns:
        Plotly Figure object
    """
    ages = list(range(starting_age, end_age + 1))

    # Merton optimal spending (assuming constant wealth for illustration)
    rates = optimal_spending_by_age(market_model, utility_model, starting_age, end_age)
    merton_spending = [initial_wealth * rates[age] for age in ages]

    # Fixed SWR spending (grows with inflation estimate)
    inflation = market_model.inflation_mean
    swr_spending = [
        initial_wealth * swr_rate * (1 + inflation) ** (age - starting_age)
        for age in ages
    ]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=ages,
        y=merton_spending,
        mode="lines",
        name="Merton Optimal",
        line=dict(color=COLORS["success_primary"], width=3),
        fill="tozeroy",
        fillcolor="rgba(39, 174, 96, 0.2)",
        hovertemplate="Age %{x}<br>$%{y:,.0f}/year<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=ages,
        y=swr_spending,
        mode="lines",
        name=f"Fixed {swr_rate:.0%} SWR",
        line=dict(color=COLORS["warning_primary"], width=3, dash="dash"),
        hovertemplate="Age %{x}<br>$%{y:,.0f}/year<extra></extra>",
    ))

    layout = get_plotly_layout_defaults()
    layout.update(
        title=dict(text=title),
        xaxis=dict(title="Age"),
        yaxis=dict(title="Annual Spending ($)", tickformat="$,.0f"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
    )
    fig.update_layout(**layout)

    return fig


def create_sensitivity_heatmap(
    market_model: MarketModel,
    gamma_range: tuple[float, float] = (1.5, 5.0),
    rtp_range: tuple[float, float] = (0.01, 0.05),
    n_points: int = 20,
    metric: str = "spending_rate",
    title: str = "Sensitivity: Optimal Spending Rate",
) -> go.Figure:
    """Create a heatmap showing sensitivity to gamma and time preference.

    Args:
        market_model: Market assumptions
        gamma_range: Range of risk aversion values
        rtp_range: Range of time preference values
        n_points: Grid resolution
        metric: "spending_rate" or "allocation"
        title: Chart title

    Returns:
        Plotly Figure object
    """
    gammas = np.linspace(gamma_range[0], gamma_range[1], n_points)
    rtps = np.linspace(rtp_range[0], rtp_range[1], n_points)

    values = np.zeros((n_points, n_points))

    for i, gamma in enumerate(gammas):
        for j, rtp in enumerate(rtps):
            utility_model = UtilityModel(gamma=gamma, time_preference=rtp)
            if metric == "spending_rate":
                values[i, j] = merton_optimal_spending_rate(market_model, utility_model) * 100
            else:
                values[i, j] = merton_optimal_allocation(market_model, utility_model) * 100

    fig = go.Figure(data=go.Heatmap(
        z=values,
        x=rtps * 100,
        y=gammas,
        colorscale="Viridis",
        colorbar=dict(title="%" if metric == "spending_rate" else "Equity %"),
        hovertemplate=(
            "Time Pref: %{x:.1f}%<br>"
            "Gamma: %{y:.1f}<br>"
            "Value: %{z:.1f}%<extra></extra>"
        ),
    ))

    layout = get_plotly_layout_defaults()
    layout.update(
        title=dict(text=title),
        xaxis=dict(title="Time Preference (%)"),
        yaxis=dict(title="Risk Aversion (gamma)"),
    )
    fig.update_layout(**layout)

    return fig
