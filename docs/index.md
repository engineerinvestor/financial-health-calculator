# Financial Health Calculator

A comprehensive Python financial planning toolkit with CEFR calculations, Monte Carlo simulations, and beautiful Plotly visualizations.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/engineerinvestor/financial-health-calculator/blob/main/examples/01_cefr_basics.ipynb)

## Features

- **CEFR (Certainty-Equivalent Funded Ratio)**: A fundedness metric that accounts for taxes, liquidity, and concentration risk
- **Monte Carlo Simulations**: Project retirement outcomes with configurable market assumptions
- **Withdrawal Strategy Lab**: Compare strategies including fixed SWR, guardrails, VPW, RMD-style, and Merton optimal
- **Utility Optimization**: Merton optimal spending and allocation based on lifetime utility maximization
- **Beautiful Visualizations**: Interactive Plotly charts with fan charts, waterfalls, and survival curves
- **REST API**: FastAPI backend for programmatic access
- **Streamlit App**: User-friendly web interface

## Quick Example

```python
from fundedness import Asset, BalanceSheet, Liability, compute_cefr
from fundedness.models.assets import AccountType, LiquidityClass, ConcentrationLevel

# Define your assets
assets = [
    Asset(
        name="401(k)",
        value=500_000,
        account_type=AccountType.TAX_DEFERRED,
        liquidity_class=LiquidityClass.RETIREMENT,
        concentration_level=ConcentrationLevel.DIVERSIFIED,
    ),
]

# Define your spending
liabilities = [
    Liability(name="Living Expenses", annual_amount=50_000, is_essential=True),
]

# Calculate CEFR
result = compute_cefr(
    balance_sheet=BalanceSheet(assets=assets),
    liabilities=liabilities,
    planning_horizon=30,
)

print(f"CEFR: {result.cefr:.2f}")
```

## Getting Started

- [Installation](getting-started/installation.md) - How to install the package
- [Quick Start](getting-started/quickstart.md) - Get up and running quickly

## User Guide

- [CEFR Explained](guide/cefr.md) - Understanding the CEFR metric
- [Monte Carlo Simulations](guide/simulations.md) - Running projections
- [Withdrawal Strategies](guide/withdrawals.md) - Comparing approaches
- [Utility Optimization](guide/utility-optimization.md) - Merton optimal spending and allocation
- [Visualizations](guide/visualizations.md) - Creating charts

## API Reference

- [Core Functions](api/core.md) - Main calculation functions
- [Models](api/models.md) - Data models reference
- [Withdrawals](api/withdrawals.md) - Withdrawal policy classes
- [Visualizations](api/viz.md) - Plotting functions

## License

MIT License

## Disclaimer

This tool is for educational purposes only and does not constitute financial advice. Consult a qualified financial advisor for personalized recommendations.
