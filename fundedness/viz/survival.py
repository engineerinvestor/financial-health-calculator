"""Survival curve visualization."""

import numpy as np
import plotly.graph_objects as go

from fundedness.viz.colors import COLORS, get_plotly_layout_defaults


def create_survival_curve(
    years: np.ndarray,
    survival_prob: np.ndarray,
    floor_survival_prob: np.ndarray | None = None,
    title: str = "Portfolio Survival Probability",
    threshold_years: list[int] | None = None,
    height: int = 450,
    width: int | None = None,
) -> go.Figure:
    """Create a survival curve showing probability of not running out of money.

    Args:
        years: Array of year values
        survival_prob: Probability of portfolio survival at each year (above ruin)
        floor_survival_prob: Probability of being above spending floor at each year
        title: Chart title
        threshold_years: Years to highlight with vertical lines (e.g., [20, 30])
        height: Chart height in pixels
        width: Chart width in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Main survival curve (above ruin)
    fig.add_trace(
        go.Scatter(
            x=years,
            y=survival_prob * 100,
            mode="lines",
            name="Above Ruin",
            line={
                "color": COLORS["wealth_primary"],
                "width": 3,
            },
            fill="tozeroy",
            fillcolor="rgba(52, 152, 219, 0.2)",
            hovertemplate=(
                "<b>Year %{x}</b><br>"
                "Survival Probability: %{y:.1f}%<br>"
                "<extra></extra>"
            ),
        )
    )

    # Floor survival curve if provided
    if floor_survival_prob is not None:
        fig.add_trace(
            go.Scatter(
                x=years,
                y=floor_survival_prob * 100,
                mode="lines",
                name="Above Floor",
                line={
                    "color": COLORS["success_primary"],
                    "width": 2,
                    "dash": "dash",
                },
                hovertemplate=(
                    "<b>Year %{x}</b><br>"
                    "Floor Probability: %{y:.1f}%<br>"
                    "<extra></extra>"
                ),
            )
        )

    # Add threshold year markers
    if threshold_years:
        for year in threshold_years:
            if year <= years[-1]:
                idx = np.searchsorted(years, year)
                if idx < len(survival_prob):
                    prob = survival_prob[idx] * 100
                    fig.add_vline(
                        x=year,
                        line_dash="dot",
                        line_color=COLORS["neutral_primary"],
                        annotation_text=f"Year {year}: {prob:.0f}%",
                        annotation_position="top",
                    )

    # Add horizontal reference lines
    for prob_level, label in [(90, "90%"), (75, "75%"), (50, "50%")]:
        fig.add_hline(
            y=prob_level,
            line_dash="dot",
            line_color=COLORS["neutral_light"],
            line_width=1,
        )

    # Apply layout
    layout = get_plotly_layout_defaults()
    layout.update({
        "title": {"text": title},
        "height": height,
        "xaxis": {
            "title": "Years",
            "gridcolor": COLORS["neutral_light"],
            "dtick": 5,
        },
        "yaxis": {
            "title": "Probability (%)",
            "range": [0, 105],
            "gridcolor": COLORS["neutral_light"],
            "ticksuffix": "%",
        },
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

    return fig


def create_dual_survival_chart(
    years: np.ndarray,
    ruin_prob: np.ndarray,
    floor_breach_prob: np.ndarray,
    title: str = "Risk Timeline",
    height: int = 450,
    width: int | None = None,
) -> go.Figure:
    """Create a chart showing both ruin and floor breach probabilities over time.

    Shows the cumulative probability of experiencing each event by each year.

    Args:
        years: Array of year values
        ruin_prob: Cumulative probability of ruin by each year
        floor_breach_prob: Cumulative probability of floor breach by each year
        title: Chart title
        height: Chart height in pixels
        width: Chart width in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Floor breach probability (less severe, but more common)
    fig.add_trace(
        go.Scatter(
            x=years,
            y=floor_breach_prob * 100,
            mode="lines",
            name="Floor Breach Risk",
            line={
                "color": COLORS["warning_primary"],
                "width": 2,
            },
            fill="tozeroy",
            fillcolor="rgba(243, 156, 18, 0.15)",
            hovertemplate=(
                "<b>Year %{x}</b><br>"
                "Floor Breach Risk: %{y:.1f}%<br>"
                "<extra></extra>"
            ),
        )
    )

    # Ruin probability (more severe)
    fig.add_trace(
        go.Scatter(
            x=years,
            y=ruin_prob * 100,
            mode="lines",
            name="Ruin Risk",
            line={
                "color": COLORS["danger_primary"],
                "width": 2,
            },
            fill="tozeroy",
            fillcolor="rgba(231, 76, 60, 0.15)",
            hovertemplate=(
                "<b>Year %{x}</b><br>"
                "Ruin Risk: %{y:.1f}%<br>"
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
            "title": "Years",
            "gridcolor": COLORS["neutral_light"],
            "dtick": 5,
        },
        "yaxis": {
            "title": "Cumulative Probability (%)",
            "range": [0, max(50, max(ruin_prob.max(), floor_breach_prob.max()) * 100 * 1.1)],
            "gridcolor": COLORS["neutral_light"],
            "ticksuffix": "%",
        },
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

    return fig
