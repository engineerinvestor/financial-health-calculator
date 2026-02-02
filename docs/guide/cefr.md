# CEFR Explained

The **Certainty-Equivalent Funded Ratio (CEFR)** is a metric that measures how well-funded your retirement is after accounting for real-world frictions.

## What CEFR Measures

Unlike simple asset-to-liability ratios, CEFR applies three "haircuts" to your assets:

### 1. Tax Haircut

Different account types have different tax implications:

| Account Type | Tax Rate | Example |
|--------------|----------|---------|
| Tax-Exempt | 0% | Roth IRA, Roth 401(k) |
| Taxable | 15% | Brokerage accounts (capital gains) |
| Tax-Deferred | 25% | Traditional IRA, 401(k) |

### 2. Liquidity Haircut

How easily can you access your money?

| Liquidity Class | Factor | Example |
|-----------------|--------|---------|
| Cash | 100% | Savings, checking |
| Near-Cash | 98% | Money market, CDs |
| Marketable | 95% | Stocks, bonds |
| Retirement | 90% | IRAs before 59.5 |
| Illiquid | 80% | Real estate, private equity |

### 3. Reliability Haircut

Concentrated positions carry additional risk:

| Concentration | Factor | Example |
|---------------|--------|---------|
| Diversified | 100% | Index funds |
| Moderate | 95% | Sector funds |
| Concentrated | 85% | Single stock |
| Highly Concentrated | 70% | Company stock, single property |

## The CEFR Formula

```
CEFR = Σ(Asset × (1-τ) × λ × ρ) / PV(Liabilities)
```

Where:

- **τ** = tax rate for the account type
- **λ** = liquidity factor
- **ρ** = reliability factor
- **PV(Liabilities)** = present value of future spending

## Interpreting Your CEFR

| CEFR Range | Status | Interpretation |
|------------|--------|----------------|
| ≥ 2.0 | Excellent | Very well-funded, significant margin |
| 1.5 - 2.0 | Strong | Well-funded with comfortable margin |
| 1.0 - 1.5 | Adequate | Fully funded for expected needs |
| 0.8 - 1.0 | Marginal | Some shortfall risk |
| < 0.8 | Underfunded | Action needed |

## Example Calculation

```python
from fundedness import Asset, BalanceSheet, Liability, compute_cefr
from fundedness.models.assets import AccountType, LiquidityClass, ConcentrationLevel

assets = [
    Asset(
        name="401(k)",
        value=500_000,
        account_type=AccountType.TAX_DEFERRED,  # 25% tax
        liquidity_class=LiquidityClass.RETIREMENT,  # 90% liquidity
        concentration_level=ConcentrationLevel.DIVERSIFIED,  # 100% reliable
    ),
]

# Effective value: $500k × 0.75 × 0.90 × 1.00 = $337,500

liabilities = [
    Liability(name="Expenses", annual_amount=50_000, is_essential=True),
]

result = compute_cefr(
    balance_sheet=BalanceSheet(assets=assets),
    liabilities=liabilities,
    planning_horizon=30,
)
```

## Why CEFR Matters

Traditional metrics like net worth or simple asset ratios can be misleading:

- A $1M 401(k) isn't really $1M after taxes
- Illiquid assets can't easily fund retirement spending
- Concentrated positions carry sequence risk

CEFR gives you a more realistic picture of your retirement readiness.
