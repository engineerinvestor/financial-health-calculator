# Visualizations

The Financial Health Calculator includes beautiful Plotly visualizations for understanding your financial health.

## Available Charts

### CEFR Waterfall Chart

Shows how haircuts affect your effective assets:

```python
from fundedness.viz import plot_cefr_waterfall

fig = plot_cefr_waterfall(cefr_result)
fig.show()
```

The waterfall shows:

- Starting gross assets
- Tax haircut reduction
- Liquidity haircut reduction
- Reliability haircut reduction
- Final effective assets

### Simulation Fan Chart

Visualizes the range of portfolio outcomes:

```python
from fundedness.viz import plot_simulation_fan_chart

fig = plot_simulation_fan_chart(simulation_results)
fig.show()
```

Features:

- Median trajectory line
- 25th-75th percentile band (likely range)
- 5th-95th percentile band (extended range)
- Individual simulation traces (optional)

### Portfolio Survival Curve

Shows probability of portfolio lasting each year:

```python
from fundedness.viz import plot_survival_curve

fig = plot_survival_curve(simulation_results)
fig.show()
```

Useful for understanding:

- When portfolio failure risk increases
- How different strategies affect longevity

### Strategy Comparison Chart

Compare withdrawal strategies side-by-side:

```python
from fundedness.viz import plot_strategy_comparison

fig = plot_strategy_comparison(comparison_results)
fig.show()
```

Shows for each strategy:

- Success rate
- Average spending
- Spending volatility
- Final portfolio distribution

### Asset Allocation Chart

Visualize asset allocation over time:

```python
from fundedness.viz import plot_allocation_glidepath

fig = plot_allocation_glidepath(allocation_strategy)
fig.show()
```

## Customization

### Colors and Themes

```python
from fundedness.viz import set_theme

set_theme("dark")  # or "light", "minimal"
```

### Chart Dimensions

```python
fig = plot_simulation_fan_chart(
    results,
    width=1000,
    height=600,
)
```

### Export Options

```python
# Save as HTML (interactive)
fig.write_html("chart.html")

# Save as PNG (static)
fig.write_image("chart.png")

# Save as SVG (vector)
fig.write_image("chart.svg")
```

## Integration with Streamlit

Charts work seamlessly in Streamlit:

```python
import streamlit as st
from fundedness.viz import plot_simulation_fan_chart

st.plotly_chart(
    plot_simulation_fan_chart(results),
    use_container_width=True,
)
```

## Interactive Features

All charts include Plotly interactivity:

- **Hover**: See exact values at any point
- **Zoom**: Click and drag to zoom
- **Pan**: Shift-drag to pan
- **Reset**: Double-click to reset view
- **Download**: Save as PNG via toolbar
