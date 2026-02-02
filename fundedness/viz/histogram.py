"""Histogram visualizations for time-to-event distributions."""

import numpy as np
import plotly.graph_objects as go

from fundedness.viz.colors import COLORS, get_plotly_layout_defaults


def create_time_distribution_histogram(
    time_to_event: np.ndarray,
    event_name: str = "Ruin",
    planning_horizon: int | None = None,
    percentiles_to_show: list[int] | None = None,
    title: str | None = None,
    height: int = 400,
    width: int | None = None,
) -> go.Figure:
    """Create a histogram of time-to-event distribution.

    Args:
        time_to_event: Array of time values (years until event, inf for no event)
        event_name: Name of the event (e.g., "Ruin", "Floor Breach")
        planning_horizon: Maximum planning horizon (for x-axis)
        percentiles_to_show: Percentiles to mark (e.g., [10, 50, 90])
        title: Chart title (auto-generated if None)
        height: Chart height in pixels
        width: Chart width in pixels

    Returns:
        Plotly Figure object
    """
    # Filter out infinite values (no event occurred)
    finite_times = time_to_event[np.isfinite(time_to_event)]
    never_occurred_count = np.sum(~np.isfinite(time_to_event))
    total_count = len(time_to_event)

    if title is None:
        title = f"Time to {event_name} Distribution"

    fig = go.Figure()

    if len(finite_times) > 0:
        # Determine bins
        max_time = planning_horizon or int(np.ceil(finite_times.max()))
        bins = np.arange(0, max_time + 2, 1)

        # Create histogram
        fig.add_trace(
            go.Histogram(
                x=finite_times,
                xbins={"start": 0, "end": max_time + 1, "size": 1},
                marker_color=COLORS["danger_primary"],
                opacity=0.7,
                name=f"Years to {event_name}",
                hovertemplate=(
                    "<b>Year %{x}</b><br>"
                    "Count: %{y}<br>"
                    "<extra></extra>"
                ),
            )
        )

        # Add percentile lines
        if percentiles_to_show:
            percentile_colors = {
                10: COLORS["danger_secondary"],
                25: COLORS["warning_secondary"],
                50: COLORS["wealth_primary"],
                75: COLORS["success_secondary"],
                90: COLORS["success_primary"],
            }

            for pct in percentiles_to_show:
                value = np.percentile(finite_times, pct)
                color = percentile_colors.get(pct, COLORS["neutral_primary"])
                fig.add_vline(
                    x=value,
                    line_dash="dash",
                    line_color=color,
                    line_width=2,
                    annotation_text=f"P{pct}: {value:.1f}y",
                    annotation_position="top",
                    annotation_font_color=color,
                )

    # Add annotation for "never occurred" count
    if never_occurred_count > 0:
        never_pct = never_occurred_count / total_count * 100
        fig.add_annotation(
            x=0.98,
            y=0.98,
            xref="paper",
            yref="paper",
            text=f"Never {event_name.lower()}ed: {never_pct:.1f}%<br>({never_occurred_count:,} paths)",
            showarrow=False,
            font={"size": 12, "color": COLORS["success_primary"]},
            bgcolor=COLORS["background"],
            bordercolor=COLORS["success_primary"],
            borderwidth=1,
            borderpad=6,
            align="right",
        )

    # Apply layout
    layout = get_plotly_layout_defaults()
    layout.update({
        "title": {"text": title},
        "height": height,
        "xaxis": {
            "title": f"Years to {event_name}",
            "gridcolor": COLORS["neutral_light"],
            "dtick": 5,
        },
        "yaxis": {
            "title": "Number of Paths",
            "gridcolor": COLORS["neutral_light"],
        },
        "showlegend": False,
        "bargap": 0.1,
    })

    if width:
        layout["width"] = width

    fig.update_layout(**layout)

    return fig


def create_outcome_distribution_histogram(
    terminal_values: np.ndarray,
    initial_value: float | None = None,
    target_value: float | None = None,
    title: str = "Terminal Wealth Distribution",
    height: int = 400,
    width: int | None = None,
) -> go.Figure:
    """Create a histogram of terminal portfolio values.

    Args:
        terminal_values: Array of terminal portfolio values
        initial_value: Starting portfolio value (for reference)
        target_value: Target terminal value (for reference)
        title: Chart title
        height: Chart height in pixels
        width: Chart width in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Create histogram with log-scale bins for wealth distribution
    fig.add_trace(
        go.Histogram(
            x=terminal_values,
            nbinsx=50,
            marker_color=COLORS["wealth_primary"],
            opacity=0.7,
            name="Terminal Value",
            hovertemplate=(
                "<b>Value Range</b><br>"
                "$%{x:,.0f}<br>"
                "Count: %{y}<br>"
                "<extra></extra>"
            ),
        )
    )

    # Add reference lines
    if initial_value is not None:
        fig.add_vline(
            x=initial_value,
            line_dash="dash",
            line_color=COLORS["neutral_primary"],
            line_width=2,
            annotation_text=f"Initial: ${initial_value:,.0f}",
            annotation_position="top",
        )

    if target_value is not None:
        fig.add_vline(
            x=target_value,
            line_dash="dot",
            line_color=COLORS["success_primary"],
            line_width=2,
            annotation_text=f"Target: ${target_value:,.0f}",
            annotation_position="top",
        )

    # Add median line
    median_value = np.median(terminal_values)
    fig.add_vline(
        x=median_value,
        line_dash="solid",
        line_color=COLORS["wealth_secondary"],
        line_width=2,
        annotation_text=f"Median: ${median_value:,.0f}",
        annotation_position="bottom",
    )

    # Apply layout
    layout = get_plotly_layout_defaults()
    layout.update({
        "title": {"text": title},
        "height": height,
        "xaxis": {
            "title": "Portfolio Value ($)",
            "tickformat": "$,.0f",
            "gridcolor": COLORS["neutral_light"],
        },
        "yaxis": {
            "title": "Number of Paths",
            "gridcolor": COLORS["neutral_light"],
        },
        "showlegend": False,
        "bargap": 0.05,
    })

    if width:
        layout["width"] = width

    fig.update_layout(**layout)

    return fig
