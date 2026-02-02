# Quick Start

This guide will get you up and running with the Financial Health Calculator.

## Basic CEFR Calculation

The CEFR (Certainty-Equivalent Funded Ratio) measures how well-funded your retirement is.

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
    Asset(
        name="Roth IRA",
        value=200_000,
        account_type=AccountType.TAX_EXEMPT,
        liquidity_class=LiquidityClass.RETIREMENT,
        concentration_level=ConcentrationLevel.DIVERSIFIED,
    ),
]

# Define your spending needs
liabilities = [
    Liability(name="Living Expenses", annual_amount=50_000, is_essential=True),
    Liability(name="Travel", annual_amount=20_000, is_essential=False),
]

# Calculate CEFR
result = compute_cefr(
    balance_sheet=BalanceSheet(assets=assets),
    liabilities=liabilities,
    planning_horizon=30,
)

print(f"CEFR: {result.cefr:.2f}")
print(f"Funded: {result.is_funded}")
print(result.get_interpretation())
```

## Running Monte Carlo Simulations

Project retirement outcomes with market simulations:

```python
from fundedness import run_simulation

results = run_simulation(
    initial_portfolio=700_000,
    annual_spending=70_000,
    years=30,
    n_simulations=1000,
)

print(f"Success Rate: {results.success_rate:.1%}")
print(f"Median Final Value: ${results.median_final_value:,.0f}")
```

## Running the Streamlit App

Launch the interactive web interface:

```bash
pip install fundedness[streamlit]
streamlit run streamlit_app/app.py
```

Then open your browser to `http://localhost:8501`.

## Running the REST API

Start the FastAPI backend:

```bash
pip install fundedness[api]
uvicorn api.main:app --reload
```

API documentation is available at `http://localhost:8000/docs`.

## Next Steps

- Learn about [CEFR in depth](../guide/cefr.md)
- Explore [Monte Carlo simulations](../guide/simulations.md)
- Compare [withdrawal strategies](../guide/withdrawals.md)
- Try the [interactive tutorials](../examples/tutorials.md)
