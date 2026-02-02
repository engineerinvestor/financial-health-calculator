"""CEFR waterfall chart visualization."""

import plotly.graph_objects as go

from fundedness.cefr import CEFRResult
from fundedness.viz.colors import COLORS, WATERFALL_COLORS, get_plotly_layout_defaults


def create_cefr_waterfall(
    cefr_result: CEFRResult,
    show_liability: bool = True,
    title: str = "CEFR Calculation Breakdown",
    height: int = 500,
    width: int | None = None,
) -> go.Figure:
    """Create a waterfall chart showing CEFR calculation breakdown.

    Shows: Gross Assets → Tax Haircut → Liquidity Haircut → Reliability Haircut → Net Assets
    Optionally shows liability comparison.

    Args:
        cefr_result: CEFR calculation result
        show_liability: Whether to show liability PV for comparison
        title: Chart title
        height: Chart height in pixels
        width: Chart width in pixels (None = responsive)

    Returns:
        Plotly Figure object
    """
    # Prepare data
    labels = [
        "Gross Assets",
        "Tax Haircut",
        "Liquidity Haircut",
        "Reliability Haircut",
        "Net Assets",
    ]
    values = [
        cefr_result.gross_assets,
        -cefr_result.total_tax_haircut,
        -cefr_result.total_liquidity_haircut,
        -cefr_result.total_reliability_haircut,
        cefr_result.net_assets,
    ]
    measures = ["absolute", "relative", "relative", "relative", "total"]

    if show_liability and cefr_result.liability_pv > 0:
        labels.append("Liability PV")
        values.append(cefr_result.liability_pv)
        measures.append("absolute")

    # Create waterfall
    fig = go.Figure(
        go.Waterfall(
            name="CEFR",
            orientation="v",
            measure=measures,
            x=labels,
            textposition="outside",
            text=[f"${abs(v):,.0f}" for v in values],
            y=values,
            connector={"line": {"color": COLORS["neutral_light"]}},
            increasing={"marker": {"color": WATERFALL_COLORS["increase"]}},
            decreasing={"marker": {"color": WATERFALL_COLORS["decrease"]}},
            totals={"marker": {"color": WATERFALL_COLORS["total"]}},
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Value: $%{y:,.0f}<br>"
                "<extra></extra>"
            ),
        )
    )

    # Add liability reference line if shown
    if show_liability and cefr_result.liability_pv > 0:
        fig.add_hline(
            y=cefr_result.liability_pv,
            line_dash="dash",
            line_color=COLORS["danger_secondary"],
            annotation_text=f"Liability PV: ${cefr_result.liability_pv:,.0f}",
            annotation_position="top right",
        )

    # Apply layout
    layout = get_plotly_layout_defaults()
    layout.update({
        "title": {"text": title},
        "height": height,
        "yaxis": {
            "title": "Value ($)",
            "tickformat": "$,.0f",
            "gridcolor": COLORS["neutral_light"],
        },
        "xaxis": {
            "title": "",
        },
        "showlegend": False,
    })

    if width:
        layout["width"] = width

    fig.update_layout(**layout)

    # Add CEFR annotation
    cefr_text = f"CEFR: {cefr_result.cefr:.2f}"
    if cefr_result.is_funded:
        cefr_color = COLORS["success_primary"]
    else:
        cefr_color = COLORS["danger_primary"]

    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref="paper",
        yref="paper",
        text=f"<b>{cefr_text}</b>",
        showarrow=False,
        font={"size": 16, "color": cefr_color},
        bgcolor=COLORS["background"],
        bordercolor=cefr_color,
        borderwidth=2,
        borderpad=8,
    )

    return fig


def create_haircut_breakdown_bar(
    cefr_result: CEFRResult,
    title: str = "Haircut Breakdown by Category",
    height: int = 400,
    width: int | None = None,
) -> go.Figure:
    """Create a horizontal bar chart showing haircut breakdown.

    Args:
        cefr_result: CEFR calculation result
        title: Chart title
        height: Chart height in pixels
        width: Chart width in pixels (None = responsive)

    Returns:
        Plotly Figure object
    """
    categories = ["Tax", "Liquidity", "Reliability"]
    values = [
        cefr_result.total_tax_haircut,
        cefr_result.total_liquidity_haircut,
        cefr_result.total_reliability_haircut,
    ]
    percentages = [
        v / cefr_result.gross_assets * 100 if cefr_result.gross_assets > 0 else 0
        for v in values
    ]

    colors = [
        COLORS["warning_primary"],
        COLORS["accent_primary"],
        COLORS["danger_primary"],
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=categories,
            x=values,
            orientation="h",
            marker_color=colors,
            text=[f"${v:,.0f} ({p:.1f}%)" for v, p in zip(values, percentages)],
            textposition="auto",
            hovertemplate=(
                "<b>%{y} Haircut</b><br>"
                "Amount: $%{x:,.0f}<br>"
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
            "title": "Haircut Amount ($)",
            "tickformat": "$,.0f",
            "gridcolor": COLORS["neutral_light"],
        },
        "yaxis": {
            "title": "",
        },
        "showlegend": False,
    })

    if width:
        layout["width"] = width

    fig.update_layout(**layout)

    return fig
