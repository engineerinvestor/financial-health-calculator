# Tutorials

Interactive Jupyter notebooks to learn the Financial Health Calculator.

## Colab Notebooks

These notebooks run in Google Colab - no installation required!

### 1. CEFR Basics

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/engineerinvestor/financial-health-calculator/blob/main/examples/01_cefr_basics.ipynb)

Learn the fundamentals of CEFR:

- What CEFR measures
- Defining assets with tax and liquidity characteristics
- Defining liabilities and spending needs
- Calculating and interpreting your CEFR
- Visualizing the haircut breakdown

### 2. Time Distribution Analysis

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/engineerinvestor/financial-health-calculator/blob/main/examples/02_time_distribution.ipynb)

Explore Monte Carlo simulations:

- Running basic simulations
- Understanding success rates
- Interpreting percentile bands
- Visualizing portfolio trajectories
- Sensitivity analysis

### 3. Withdrawal Strategy Comparison

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/engineerinvestor/financial-health-calculator/blob/main/examples/03_withdrawal_comparison.ipynb)

Compare withdrawal approaches:

- Fixed SWR (4% rule)
- Guardrails strategy
- Variable Percentage Withdrawal
- RMD-style withdrawals
- Trade-offs between stability and spending

## Running Locally

Clone the repo and run notebooks locally:

```bash
git clone https://github.com/engineerinvestor/financial-health-calculator.git
cd financial-health-calculator
pip install -e ".[dev]"
jupyter notebook examples/
```

## Example Code

### Quick CEFR Check

```python
from fundedness import Asset, BalanceSheet, Liability, compute_cefr
from fundedness.models.assets import AccountType, LiquidityClass, ConcentrationLevel

# Simple example
result = compute_cefr(
    balance_sheet=BalanceSheet(assets=[
        Asset(
            name="Portfolio",
            value=1_000_000,
            account_type=AccountType.TAXABLE,
            liquidity_class=LiquidityClass.MARKETABLE,
            concentration_level=ConcentrationLevel.DIVERSIFIED,
        ),
    ]),
    liabilities=[
        Liability(name="Spending", annual_amount=40_000, is_essential=True),
    ],
    planning_horizon=30,
)

print(f"CEFR: {result.cefr:.2f} - {result.get_interpretation()}")
```

### Quick Simulation

```python
from fundedness import run_simulation

results = run_simulation(
    initial_portfolio=1_000_000,
    annual_spending=40_000,
    years=30,
)

print(f"Success Rate: {results.success_rate:.1%}")
```

### Quick Visualization

```python
from fundedness import run_simulation
from fundedness.viz import plot_simulation_fan_chart

results = run_simulation(
    initial_portfolio=1_000_000,
    annual_spending=40_000,
    years=30,
)

fig = plot_simulation_fan_chart(results)
fig.show()
```
