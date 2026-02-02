"""Fan chart visualization for Monte Carlo projections."""

import numpy as np
import plotly.graph_objects as go

from fundedness.viz.colors import COLORS, get_plotly_layout_defaults


def create_fan_chart(
    years: np.ndarray,
    percentiles: dict[str, np.ndarray],
    title: str = "Wealth Projection",
    y_label: str = "Portfolio Value ($)",
    show_median_line: bool = True,
    show_floor: float | None = None,
    height: int = 500,
    width: int | None = None,
) -> go.Figure:
    """Create a fan chart showing percentile bands over time.

    Args:
        years: Array of year values (x-axis)
        percentiles: Dictionary mapping percentile names to value arrays
            Expected keys: "P10", "P25", "P50", "P75", "P90"
        title: Chart title
        y_label: Y-axis label
        show_median_line: Whether to show a distinct median line
        show_floor: Optional floor value to show as horizontal line
        height: Chart height in pixels
        width: Chart width in pixels (None = responsive)

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # P10-P90 band (outermost)
    if "P10" in percentiles and "P90" in percentiles:
        fig.add_trace(
            go.Scatter(
                x=np.concatenate([years, years[::-1]]),
                y=np.concatenate([percentiles["P90"], percentiles["P10"][::-1]]),
                fill="toself",
                fillcolor="rgba(52, 152, 219, 0.15)",
                line={"width": 0},
                name="P10-P90 Range",
                hoverinfo="skip",
                showlegend=True,
            )
        )

    # P25-P75 band (middle)
    if "P25" in percentiles and "P75" in percentiles:
        fig.add_trace(
            go.Scatter(
                x=np.concatenate([years, years[::-1]]),
                y=np.concatenate([percentiles["P75"], percentiles["P25"][::-1]]),
                fill="toself",
                fillcolor="rgba(52, 152, 219, 0.3)",
                line={"width": 0},
                name="P25-P75 Range",
                hoverinfo="skip",
                showlegend=True,
            )
        )

    # Percentile lines
    percentile_styles = {
        "P90": {"color": COLORS["success_secondary"], "dash": "dot", "width": 1},
        "P75": {"color": COLORS["success_primary"], "dash": "dash", "width": 1},
        "P50": {"color": COLORS["wealth_primary"], "dash": "solid", "width": 3},
        "P25": {"color": COLORS["warning_primary"], "dash": "dash", "width": 1},
        "P10": {"color": COLORS["danger_secondary"], "dash": "dot", "width": 1},
    }

    for pct_name, values in percentiles.items():
        if pct_name in percentile_styles:
            style = percentile_styles[pct_name]
            is_median = pct_name == "P50"

            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=values,
                    mode="lines",
                    name=pct_name,
                    line={
                        "color": style["color"],
                        "dash": style["dash"],
                        "width": style["width"] if not (is_median and show_median_line) else 3,
                    },
                    hovertemplate=(
                        f"<b>{pct_name}</b><br>"
                        "Year: %{x}<br>"
                        "Value: $%{y:,.0f}<br>"
                        "<extra></extra>"
                    ),
                    showlegend=not (pct_name in ["P90", "P75", "P25", "P10"]),
                )
            )

    # Add floor line if specified
    if show_floor is not None:
        fig.add_hline(
            y=show_floor,
            line_dash="dash",
            line_color=COLORS["danger_primary"],
            line_width=2,
            annotation_text=f"Floor: ${show_floor:,.0f}",
            annotation_position="top right",
            annotation_font_color=COLORS["danger_primary"],
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
            "rangemode": "tozero",
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


def create_spending_fan_chart(
    years: np.ndarray,
    percentiles: dict[str, np.ndarray],
    floor_spending: float | None = None,
    target_spending: float | None = None,
    title: str = "Spending Projection",
    height: int = 500,
    width: int | None = None,
) -> go.Figure:
    """Create a fan chart specifically for spending projections.

    Args:
        years: Array of year values
        percentiles: Dictionary mapping percentile names to spending arrays
        floor_spending: Essential spending floor
        target_spending: Target spending level
        title: Chart title
        height: Chart height in pixels
        width: Chart width in pixels

    Returns:
        Plotly Figure object
    """
    fig = create_fan_chart(
        years=years,
        percentiles=percentiles,
        title=title,
        y_label="Annual Spending ($)",
        show_floor=floor_spending,
        height=height,
        width=width,
    )

    # Add target spending line if specified
    if target_spending is not None:
        fig.add_hline(
            y=target_spending,
            line_dash="dot",
            line_color=COLORS["success_primary"],
            line_width=2,
            annotation_text=f"Target: ${target_spending:,.0f}",
            annotation_position="top left",
            annotation_font_color=COLORS["success_primary"],
        )

    return fig
