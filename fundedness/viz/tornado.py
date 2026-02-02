"""Tornado chart for sensitivity analysis."""

import plotly.graph_objects as go

from fundedness.viz.colors import COLORS, get_plotly_layout_defaults


def create_tornado_chart(
    parameters: list[str],
    low_values: list[float],
    high_values: list[float],
    base_value: float,
    parameter_labels: list[str] | None = None,
    title: str = "Sensitivity Analysis",
    value_label: str = "CEFR",
    height: int = 500,
    width: int | None = None,
) -> go.Figure:
    """Create a tornado chart for sensitivity analysis.

    Args:
        parameters: List of parameter names
        low_values: Outcome values when parameter is at low end
        high_values: Outcome values when parameter is at high end
        base_value: Baseline outcome value
        parameter_labels: Display labels for parameters (uses parameters if None)
        title: Chart title
        value_label: Label for the outcome metric
        height: Chart height in pixels
        width: Chart width in pixels

    Returns:
        Plotly Figure object
    """
    if parameter_labels is None:
        parameter_labels = parameters

    # Calculate ranges and sort by total impact
    impacts = []
    for i, (low, high) in enumerate(zip(low_values, high_values)):
        low_impact = base_value - low
        high_impact = high - base_value
        total_impact = abs(high - low)
        impacts.append({
            "param": parameter_labels[i],
            "low": low,
            "high": high,
            "low_impact": low_impact,
            "high_impact": high_impact,
            "total_impact": total_impact,
        })

    # Sort by total impact (largest first)
    impacts.sort(key=lambda x: x["total_impact"], reverse=True)

    fig = go.Figure()

    # Low impact bars (extending left from base)
    fig.add_trace(
        go.Bar(
            y=[i["param"] for i in impacts],
            x=[-(base_value - i["low"]) for i in impacts],
            orientation="h",
            name="Low Scenario",
            marker_color=COLORS["danger_primary"],
            text=[f"{i['low']:.2f}" for i in impacts],
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                f"Low {value_label}: " + "%{customdata:.2f}<br>"
                "<extra></extra>"
            ),
            customdata=[i["low"] for i in impacts],
        )
    )

    # High impact bars (extending right from base)
    fig.add_trace(
        go.Bar(
            y=[i["param"] for i in impacts],
            x=[i["high"] - base_value for i in impacts],
            orientation="h",
            name="High Scenario",
            marker_color=COLORS["success_primary"],
            text=[f"{i['high']:.2f}" for i in impacts],
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                f"High {value_label}: " + "%{customdata:.2f}<br>"
                "<extra></extra>"
            ),
            customdata=[i["high"] for i in impacts],
        )
    )

    # Add base value line
    fig.add_vline(
        x=0,
        line_color=COLORS["text_primary"],
        line_width=2,
    )

    # Apply layout
    layout = get_plotly_layout_defaults()

    # Calculate x-axis range
    max_deviation = max(
        max(abs(base_value - i["low"]) for i in impacts),
        max(abs(i["high"] - base_value) for i in impacts),
    )
    x_range = [-max_deviation * 1.3, max_deviation * 1.3]

    layout.update({
        "title": {"text": title},
        "height": height,
        "xaxis": {
            "title": f"Change in {value_label} from Base ({base_value:.2f})",
            "gridcolor": COLORS["neutral_light"],
            "range": x_range,
            "zeroline": True,
            "zerolinecolor": COLORS["text_primary"],
            "zerolinewidth": 2,
        },
        "yaxis": {
            "title": "",
            "autorange": "reversed",  # Largest impact at top
        },
        "barmode": "overlay",
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

    # Add base value annotation
    fig.add_annotation(
        x=0,
        y=1.1,
        xref="x",
        yref="paper",
        text=f"Base: {base_value:.2f}",
        showarrow=False,
        font={"size": 12, "color": COLORS["text_primary"]},
    )

    return fig


def create_scenario_comparison_chart(
    scenarios: list[str],
    values: list[float],
    base_scenario: str | None = None,
    title: str = "Scenario Comparison",
    value_label: str = "CEFR",
    height: int = 400,
    width: int | None = None,
) -> go.Figure:
    """Create a bar chart comparing different scenarios.

    Args:
        scenarios: List of scenario names
        values: Outcome values for each scenario
        base_scenario: Name of the base scenario (highlighted differently)
        title: Chart title
        value_label: Label for the outcome metric
        height: Chart height in pixels
        width: Chart width in pixels

    Returns:
        Plotly Figure object
    """
    colors = []
    for scenario in scenarios:
        if scenario == base_scenario:
            colors.append(COLORS["wealth_primary"])
        elif values[scenarios.index(scenario)] >= 1.0:
            colors.append(COLORS["success_primary"])
        else:
            colors.append(COLORS["warning_primary"])

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=scenarios,
            y=values,
            marker_color=colors,
            text=[f"{v:.2f}" for v in values],
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"{value_label}: " + "%{y:.2f}<br>"
                "<extra></extra>"
            ),
        )
    )

    # Add threshold line at 1.0 for CEFR
    if value_label == "CEFR":
        fig.add_hline(
            y=1.0,
            line_dash="dash",
            line_color=COLORS["neutral_primary"],
            annotation_text="Fully Funded (1.0)",
            annotation_position="top right",
        )

    # Apply layout
    layout = get_plotly_layout_defaults()
    layout.update({
        "title": {"text": title},
        "height": height,
        "xaxis": {
            "title": "Scenario",
        },
        "yaxis": {
            "title": value_label,
            "gridcolor": COLORS["neutral_light"],
        },
        "showlegend": False,
    })

    if width:
        layout["width"] = width

    fig.update_layout(**layout)

    return fig
