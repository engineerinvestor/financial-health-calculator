"""Strategy comparison visualizations."""

from typing import Any

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fundedness.viz.colors import COLORS, STRATEGY_COLORS, get_plotly_layout_defaults


def create_strategy_comparison_chart(
    years: np.ndarray,
    strategies: dict[str, dict[str, np.ndarray]],
    metric: str = "wealth_median",
    title: str = "Strategy Comparison",
    y_label: str = "Portfolio Value ($)",
    height: int = 500,
    width: int | None = None,
) -> go.Figure:
    """Create a line chart comparing multiple strategies.

    Args:
        years: Array of year values
        strategies: Dictionary mapping strategy name to metrics dict
            Each metrics dict should contain arrays for the requested metric
        metric: Which metric to plot (e.g., "wealth_median", "spending_median")
        title: Chart title
        y_label: Y-axis label
        height: Chart height in pixels
        width: Chart width in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    for i, (name, metrics) in enumerate(strategies.items()):
        if metric not in metrics:
            continue

        color = STRATEGY_COLORS[i % len(STRATEGY_COLORS)]

        fig.add_trace(
            go.Scatter(
                x=years,
                y=metrics[metric],
                mode="lines",
                name=name,
                line={"color": color, "width": 2},
                hovertemplate=(
                    f"<b>{name}</b><br>"
                    "Year: %{x}<br>"
                    "Value: $%{y:,.0f}<br>"
                    "<extra></extra>"
                ),
            )
        )

    # Apply layout
    layout = get_plotly_layout_defaults()
    layout.update({
        "title": {"text": title},
        "height": height,
        "xaxis": {
            "title": "Year",
            "gridcolor": COLORS["neutral_light"],
            "dtick": 5,
        },
        "yaxis": {
            "title": y_label,
            "tickformat": "$,.0f",
            "gridcolor": COLORS["neutral_light"],
        },
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        "hovermode": "x unified",
    })

    if width:
        layout["width"] = width

    fig.update_layout(**layout)

    return fig


def create_strategy_metrics_table(
    strategies: dict[str, dict[str, Any]],
    metrics_to_show: list[str] | None = None,
    title: str = "Strategy Metrics Summary",
    height: int = 300,
    width: int | None = None,
) -> go.Figure:
    """Create a table comparing strategy metrics.

    Args:
        strategies: Dictionary mapping strategy name to metrics dict
        metrics_to_show: List of metric names to display
        title: Chart title
        height: Chart height in pixels
        width: Chart width in pixels

    Returns:
        Plotly Figure object
    """
    if metrics_to_show is None:
        metrics_to_show = [
            "success_rate",
            "median_terminal_wealth",
            "median_spending",
            "spending_volatility",
            "worst_drawdown",
        ]

    metric_labels = {
        "success_rate": "Success Rate",
        "median_terminal_wealth": "Median Terminal Wealth",
        "median_spending": "Median Spending",
        "spending_volatility": "Spending Volatility",
        "worst_drawdown": "Worst Drawdown",
        "time_to_ruin_p10": "Time to Ruin (P10)",
        "floor_breach_rate": "Floor Breach Rate",
    }

    metric_formats = {
        "success_rate": lambda x: f"{x:.1%}",
        "median_terminal_wealth": lambda x: f"${x:,.0f}",
        "median_spending": lambda x: f"${x:,.0f}",
        "spending_volatility": lambda x: f"{x:.1%}",
        "worst_drawdown": lambda x: f"{x:.1%}",
        "time_to_ruin_p10": lambda x: f"{x:.1f} years",
        "floor_breach_rate": lambda x: f"{x:.1%}",
    }

    # Build table data
    strategy_names = list(strategies.keys())
    header_values = ["Metric"] + strategy_names

    rows = []
    for metric in metrics_to_show:
        row = [metric_labels.get(metric, metric)]
        formatter = metric_formats.get(metric, lambda x: f"{x:.2f}")

        for name in strategy_names:
            value = strategies[name].get(metric, None)
            if value is not None:
                row.append(formatter(value))
            else:
                row.append("N/A")
        rows.append(row)

    # Transpose for plotly table format
    cell_values = list(zip(*rows))

    fig = go.Figure(
        data=[
            go.Table(
                header={
                    "values": header_values,
                    "fill_color": COLORS["wealth_primary"],
                    "font": {"color": "white", "size": 12},
                    "align": "center",
                    "height": 30,
                },
                cells={
                    "values": cell_values,
                    "fill_color": [COLORS["background_alt"]] + [COLORS["background"]] * len(strategy_names),
                    "font": {"color": COLORS["text_primary"], "size": 11},
                    "align": ["left"] + ["center"] * len(strategy_names),
                    "height": 25,
                },
            )
        ]
    )

    layout = get_plotly_layout_defaults()
    layout.update({
        "title": {"text": title},
        "height": height,
        "margin": {"l": 20, "r": 20, "t": 60, "b": 20},
    })

    if width:
        layout["width"] = width

    fig.update_layout(**layout)

    return fig


def create_multi_metric_comparison(
    years: np.ndarray,
    strategies: dict[str, dict[str, np.ndarray]],
    title: str = "Multi-Metric Strategy Comparison",
    height: int = 800,
    width: int | None = None,
) -> go.Figure:
    """Create a multi-panel chart comparing strategies across metrics.

    Args:
        years: Array of year values
        strategies: Dictionary mapping strategy name to metrics dict
        title: Chart title
        height: Chart height in pixels
        width: Chart width in pixels

    Returns:
        Plotly Figure object with subplots
    """
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Median Wealth",
            "Median Spending",
            "Survival Probability",
            "Spending as % of Initial",
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
    )

    metrics_config = [
        ("wealth_median", 1, 1, "$,.0f"),
        ("spending_median", 1, 2, "$,.0f"),
        ("survival_prob", 2, 1, ".0%"),
        ("spending_ratio", 2, 2, ".1%"),
    ]

    for i, (name, metrics) in enumerate(strategies.items()):
        color = STRATEGY_COLORS[i % len(STRATEGY_COLORS)]

        for metric, row, col, fmt in metrics_config:
            if metric not in metrics:
                continue

            values = metrics[metric]
            if metric == "survival_prob":
                values = values * 100  # Convert to percentage

            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=values,
                    mode="lines",
                    name=name,
                    line={"color": color, "width": 2},
                    showlegend=(row == 1 and col == 1),  # Only show legend once
                    hovertemplate=(
                        f"<b>{name}</b><br>"
                        "Year: %{x}<br>"
                        "Value: %{y}<br>"
                        "<extra></extra>"
                    ),
                ),
                row=row,
                col=col,
            )

    # Apply layout
    layout = get_plotly_layout_defaults()
    layout.update({
        "title": {"text": title},
        "height": height,
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    })

    if width:
        layout["width"] = width

    fig.update_layout(**layout)

    # Update axes
    fig.update_xaxes(title_text="Year", gridcolor=COLORS["neutral_light"])
    fig.update_yaxes(gridcolor=COLORS["neutral_light"])

    fig.update_yaxes(tickformat="$,.0f", row=1, col=1)
    fig.update_yaxes(tickformat="$,.0f", row=1, col=2)
    fig.update_yaxes(ticksuffix="%", row=2, col=1)
    fig.update_yaxes(ticksuffix="%", row=2, col=2)

    return fig
