"""Color palette and styling constants for visualizations."""

# Primary colors
COLORS = {
    # Blues for wealth/assets
    "wealth_primary": "#3498db",
    "wealth_secondary": "#2980b9",
    "wealth_light": "#5dade2",
    "wealth_dark": "#1a5276",

    # Greens for spending/survival/positive outcomes
    "success_primary": "#27ae60",
    "success_secondary": "#2ecc71",
    "success_light": "#58d68d",
    "success_dark": "#1e8449",

    # Reds for haircuts/negative outcomes
    "danger_primary": "#e74c3c",
    "danger_secondary": "#c0392b",
    "danger_light": "#ec7063",
    "danger_dark": "#922b21",

    # Oranges for warnings/caution
    "warning_primary": "#f39c12",
    "warning_secondary": "#e67e22",
    "warning_light": "#f5b041",
    "warning_dark": "#b9770e",

    # Purples for alternatives/special
    "accent_primary": "#9b59b6",
    "accent_secondary": "#8e44ad",
    "accent_light": "#bb8fce",
    "accent_dark": "#6c3483",

    # Grays for neutral elements
    "neutral_primary": "#7f8c8d",
    "neutral_secondary": "#95a5a6",
    "neutral_light": "#bdc3c7",
    "neutral_dark": "#5d6d7e",

    # Background colors
    "background": "#ffffff",
    "background_alt": "#f8f9fa",

    # Text colors
    "text_primary": "#2c3e50",
    "text_secondary": "#7f8c8d",
}

# Fan chart percentile colors (gradient from optimistic to pessimistic)
FAN_CHART_COLORS = {
    "P90": "rgba(46, 204, 113, 0.3)",   # Light green (optimistic)
    "P75": "rgba(46, 204, 113, 0.4)",
    "P50": "rgba(52, 152, 219, 0.8)",   # Solid blue (median)
    "P25": "rgba(231, 76, 60, 0.4)",
    "P10": "rgba(231, 76, 60, 0.3)",    # Light red (pessimistic)
}

# Waterfall chart colors
WATERFALL_COLORS = {
    "increase": COLORS["success_primary"],
    "decrease": COLORS["danger_primary"],
    "total": COLORS["wealth_primary"],
}

# Strategy comparison colors (for withdrawal lab)
STRATEGY_COLORS = [
    COLORS["wealth_primary"],
    COLORS["success_primary"],
    COLORS["accent_primary"],
    COLORS["warning_primary"],
    COLORS["danger_primary"],
]

# Default Plotly template settings
TEMPLATE_SETTINGS = {
    "template": "plotly_white",
    "font_family": "Inter, system-ui, -apple-system, sans-serif",
    "title_font_size": 18,
    "axis_font_size": 12,
    "legend_font_size": 11,
}


def get_plotly_layout_defaults() -> dict:
    """Get default layout settings for consistent styling."""
    return {
        "template": TEMPLATE_SETTINGS["template"],
        "font": {
            "family": TEMPLATE_SETTINGS["font_family"],
            "size": TEMPLATE_SETTINGS["axis_font_size"],
            "color": COLORS["text_primary"],
        },
        "title": {
            "font": {
                "size": TEMPLATE_SETTINGS["title_font_size"],
                "color": COLORS["text_primary"],
            },
            "x": 0.5,
            "xanchor": "center",
        },
        "paper_bgcolor": COLORS["background"],
        "plot_bgcolor": COLORS["background"],
        "margin": {"l": 60, "r": 40, "t": 60, "b": 60},
        "hoverlabel": {
            "bgcolor": COLORS["background"],
            "font_size": 12,
            "font_family": TEMPLATE_SETTINGS["font_family"],
        },
    }
