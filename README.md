# Financial Health Calculator

[![PyPI version](https://img.shields.io/pypi/v/fundedness.svg)](https://pypi.org/project/fundedness/)
[![Python versions](https://img.shields.io/pypi/pyversions/fundedness.svg)](https://pypi.org/project/fundedness/)
[![CI](https://github.com/engineerinvestor/financial-health-calculator/actions/workflows/ci.yml/badge.svg)](https://github.com/engineerinvestor/financial-health-calculator/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/engineerinvestor/financial-health-calculator/branch/main/graph/badge.svg)](https://codecov.io/gh/engineerinvestor/financial-health-calculator)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://engineerinvestor.github.io/financial-health-calculator/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/engineerinvestor/financial-health-calculator/blob/main/examples/01_cefr_basics.ipynb)

A comprehensive Python financial planning toolkit with CEFR calculations, Monte Carlo simulations, and beautiful Plotly visualizations.

## Features

- **CEFR (Certainty-Equivalent Funded Ratio)**: A fundedness metric that accounts for taxes, liquidity, and concentration risk
- **Monte Carlo Simulations**: Project retirement outcomes with configurable market assumptions
- **Withdrawal Strategy Lab**: Compare strategies including fixed SWR, guardrails, VPW, RMD-style, and Merton optimal
- **Utility Optimization**: Victor Haghani / Elm Wealth methodology for optimal spending and allocation
- **Beautiful Visualizations**: Interactive Plotly charts with fan charts, waterfalls, and survival curves
- **REST API**: FastAPI backend for programmatic access
- **Streamlit App**: User-friendly web interface

## Quick Start

### Installation

```bash
pip install fundedness
```

For development with all extras:
```bash
pip install "fundedness[all]"
```

### Basic Usage

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

# Define your spending
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

## Tutorials

- [CEFR Basics](https://colab.research.google.com/github/engineerinvestor/financial-health-calculator/blob/main/examples/01_cefr_basics.ipynb) - Introduction to the CEFR metric
- [Time Distribution Analysis](https://colab.research.google.com/github/engineerinvestor/financial-health-calculator/blob/main/examples/02_time_distribution.ipynb) - Monte Carlo simulations
- [Withdrawal Strategy Comparison](https://colab.research.google.com/github/engineerinvestor/financial-health-calculator/blob/main/examples/03_withdrawal_comparison.ipynb) - Compare different approaches

## Running the Apps

### Streamlit Web App

```bash
streamlit run streamlit_app/app.py
```

### FastAPI REST API

```bash
uvicorn api.main:app --reload
```

API documentation available at `http://localhost:8000/docs`

## Key Concepts

### CEFR (Certainty-Equivalent Funded Ratio)

CEFR measures how well-funded your retirement is after accounting for:

- **Tax Haircuts**: What you'll owe when withdrawing from different account types
- **Liquidity Haircuts**: How easily you can access your assets
- **Reliability Haircuts**: Risk from concentrated positions

**Formula:**
```
CEFR = Σ(Asset × (1-τ) × λ × ρ) / PV(Liabilities)
```

Where τ = tax rate, λ = liquidity factor, ρ = reliability factor

**Interpretation:**
- CEFR ≥ 2.0: Excellent - Very well-funded
- CEFR 1.5-2.0: Strong - Well-funded with margin
- CEFR 1.0-1.5: Adequate - Fully funded
- CEFR < 1.0: Underfunded - Action needed

### Withdrawal Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| Fixed SWR | 4% of initial portfolio, adjusted for inflation | Predictability |
| % of Portfolio | Fixed % of current value | Market adaptation |
| Guardrails | Adjustable with floor/ceiling | Balance |
| VPW | Age-based variable percentage | Maximizing spending |
| RMD-Style | IRS distribution table based | Tax efficiency |
| Merton Optimal | Utility-maximizing spending rate | Optimality |

### Utility Optimization

The toolkit includes Merton's optimal consumption and portfolio choice framework, as applied in modern retirement planning research<sup>[1]</sup>:

- **Optimal Equity Allocation**: `k* = (μ - r) / (γ × σ²)`
- **Wealth-Adjusted Allocation**: Reduces equity as wealth approaches subsistence floor
- **Optimal Spending Rate**: Increases with age as horizon shortens
- **Expected Lifetime Utility**: Track utility across Monte Carlo paths

Key insights from this methodology:
1. Optimal spending starts low (~2-3%) and rises with age
2. Allocation should decrease as wealth approaches the floor
3. Risk aversion (gamma) is the critical input parameter
4. The 4% rule is suboptimal from a utility perspective

## Development

### Setup

```bash
git clone https://github.com/engineerinvestor/financial-health-calculator.git
cd financial-health-calculator
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
ruff check .
mypy fundedness
```

## Project Structure

```
financial-health-calculator/
├── fundedness/           # Core Python package
│   ├── models/           # Pydantic data models
│   ├── viz/              # Plotly visualizations
│   ├── withdrawals/      # Withdrawal strategies (SWR, guardrails, VPW, Merton)
│   ├── allocation/       # Asset allocation strategies (constant, glidepath, Merton)
│   ├── cefr.py           # CEFR calculation
│   ├── simulate.py       # Monte Carlo engine with utility tracking
│   ├── merton.py         # Merton optimal formulas
│   ├── optimize.py       # Policy parameter optimization
│   └── policies.py       # Spending/allocation policies
├── api/                  # FastAPI REST API
├── streamlit_app/        # Streamlit web application
│   └── pages/            # Includes Utility Optimization page
├── examples/             # Jupyter notebooks
└── tests/                # pytest tests
```

## Contact

- Twitter: [@egr_investor](https://x.com/egr_investor)
- GitHub: [engineerinvestor](https://github.com/engineerinvestor)
- Email: egr.investor@gmail.com

## License

MIT License

## References

1. Haghani, V., & White, J. (2023). *The Missing Billionaires: A Guide to Better Financial Decisions*. Wiley. See also [Elm Wealth](https://elmwealth.com/) for related research on optimal spending and allocation.

2. Merton, R. C. (1969). Lifetime Portfolio Selection under Uncertainty: The Continuous-Time Case. *The Review of Economics and Statistics*, 51(3), 247-257.

## Disclaimer

This tool is for educational purposes only and does not constitute financial advice. Consult a qualified financial advisor for personalized recommendations.
