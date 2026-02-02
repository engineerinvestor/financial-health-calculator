# Financial Health Calculator

A comprehensive Python financial planning toolkit with CEFR calculations, Monte Carlo simulations, and beautiful Plotly visualizations.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/engineerinvestor/financial-health-calculator/blob/main/examples/01_cefr_basics.ipynb)

## Features

- **CEFR (Certainty-Equivalent Funded Ratio)**: A fundedness metric that accounts for taxes, liquidity, and concentration risk
- **Monte Carlo Simulations**: Project retirement outcomes with configurable market assumptions
- **Withdrawal Strategy Lab**: Compare strategies including fixed SWR, guardrails, VPW, and RMD-style
- **Beautiful Visualizations**: Interactive Plotly charts with fan charts, waterfalls, and survival curves
- **REST API**: FastAPI backend for programmatic access
- **Streamlit App**: User-friendly web interface

## Quick Start

### Installation

```bash
pip install git+https://github.com/engineerinvestor/financial-health-calculator.git
```

For development with all extras:
```bash
pip install "git+https://github.com/engineerinvestor/financial-health-calculator.git#egg=fundedness[all]"
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
│   ├── withdrawals/      # Withdrawal strategies
│   ├── allocation/       # Asset allocation strategies
│   ├── cefr.py           # CEFR calculation
│   ├── simulate.py       # Monte Carlo engine
│   └── policies.py       # Spending/allocation policies
├── api/                  # FastAPI REST API
├── streamlit_app/        # Streamlit web application
├── examples/             # Jupyter notebooks
└── tests/                # pytest tests
```

## Contact

- Twitter: [@egr_investor](https://x.com/egr_investor)
- GitHub: [engineerinvestor](https://github.com/engineerinvestor)
- Email: egr.investor@gmail.com

## License

MIT License

## Disclaimer

This tool is for educational purposes only and does not constitute financial advice. Consult a qualified financial advisor for personalized recommendations.
