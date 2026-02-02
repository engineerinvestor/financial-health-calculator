# Withdrawal Strategies

Choosing the right withdrawal strategy affects both your spending and portfolio longevity. This guide compares the main approaches.

## Strategy Overview

| Strategy | Description | Pros | Cons |
|----------|-------------|------|------|
| Fixed SWR | 4% of initial portfolio, inflation-adjusted | Predictable income | Ignores market conditions |
| % of Portfolio | Fixed % of current value | Adapts to market | Volatile income |
| Guardrails | Adjustable with floor/ceiling | Balance of both | More complex |
| VPW | Age-based variable percentage | Maximizes spending | Requires discipline |
| RMD-Style | IRS distribution table | Tax-efficient | Conservative early |

## Fixed Safe Withdrawal Rate (SWR)

The classic "4% rule" from the Trinity Study.

```python
from fundedness.withdrawals import FixedSWRPolicy

policy = FixedSWRPolicy(
    initial_portfolio=1_000_000,
    withdrawal_rate=0.04,
    inflation_rate=0.025,
)

# Year 1: $40,000
# Year 2: $41,000 (inflation adjusted)
# Year 3: $42,025
```

**Best for**: Those who prioritize predictable income.

## Percentage of Portfolio

Withdraw a fixed percentage of current portfolio value each year.

```python
from fundedness.withdrawals import PercentOfPortfolioPolicy

policy = PercentOfPortfolioPolicy(
    withdrawal_rate=0.04,
)

# If portfolio = $1M: withdraw $40,000
# If portfolio = $800k: withdraw $32,000
# If portfolio = $1.2M: withdraw $48,000
```

**Best for**: Those comfortable with variable income who want market adaptation.

## Guardrails Strategy

Combines fixed spending with guardrails that trigger adjustments.

```python
from fundedness.withdrawals import GuardrailsPolicy

policy = GuardrailsPolicy(
    initial_spending=40_000,
    ceiling_rate=0.05,   # Increase if rate drops below this
    floor_rate=0.03,     # Decrease if rate rises above this
    adjustment=0.10,     # Adjust by 10%
)
```

**How it works**:

1. Start with base spending
2. If current rate < ceiling: increase spending by 10%
3. If current rate > floor: decrease spending by 10%

**Best for**: Balance between stability and market responsiveness.

## Variable Percentage Withdrawal (VPW)

Age-based withdrawal rates that increase over time.

```python
from fundedness.withdrawals import VPWPolicy

policy = VPWPolicy(
    current_age=65,
)

# Age 65: ~4.0%
# Age 75: ~5.5%
# Age 85: ~8.0%
```

**Rationale**: As you age, your remaining time horizon shrinks, so you can safely withdraw more.

**Best for**: Maximizing lifetime spending, those with flexibility.

## RMD-Style

Based on IRS Required Minimum Distribution tables.

```python
from fundedness.withdrawals import RMDPolicy

policy = RMDPolicy(
    current_age=72,
)

# Uses IRS Uniform Lifetime Table
# Age 72: 1/27.4 = 3.65%
# Age 80: 1/20.2 = 4.95%
```

**Best for**: Tax-deferred accounts, conservative early retirement.

## Comparing Strategies

Run a comparison across strategies:

```python
from fundedness import compare_strategies

results = compare_strategies(
    initial_portfolio=1_000_000,
    years=30,
    strategies=["fixed_swr", "guardrails", "vpw"],
    n_simulations=10_000,
)

for strategy, metrics in results.items():
    print(f"{strategy}:")
    print(f"  Success Rate: {metrics.success_rate:.1%}")
    print(f"  Avg Spending: ${metrics.avg_annual_spending:,.0f}")
```

## Choosing a Strategy

Consider these factors:

1. **Income stability needs**: Fixed SWR > Guardrails > VPW
2. **Spending flexibility**: VPW > Guardrails > Fixed SWR
3. **Risk tolerance**: Conservative → RMD, Aggressive → VPW
4. **Other income sources**: Social Security, pension reduce need for stability

## Hybrid Approaches

Many retirees use combinations:

- Fixed SWR for essential expenses
- % of Portfolio for discretionary
- Guardrails as overall framework
