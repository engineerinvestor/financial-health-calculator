# Utility Optimization

This guide covers the utility-optimal spending and allocation framework based on Merton's continuous-time portfolio optimization theory.

## Overview

Traditional retirement planning often uses rules of thumb like the "4% rule." While simple, these approaches don't account for individual preferences about risk and the trade-off between spending now versus later.

Utility optimization provides a rigorous framework for finding the **optimal** spending rate and asset allocation based on:

- **Risk aversion (gamma)**: How much you dislike uncertainty
- **Time preference**: How much you prefer spending now vs. later
- **Subsistence floor**: Minimum spending you need to survive

## Key Formulas

### Optimal Equity Allocation

The Merton formula gives the optimal fraction to invest in risky assets:

\[
k^* = \frac{\mu - r}{\gamma \cdot \sigma^2}
\]

Where:

- \(\mu\) = expected stock return
- \(r\) = bond/risk-free return
- \(\gamma\) = risk aversion coefficient
- \(\sigma\) = stock volatility

### Certainty Equivalent Return

The guaranteed return that provides the same utility as the risky portfolio:

\[
r_{CE} = r + k^*(\mu - r) - \frac{\gamma \cdot (k^*)^2 \cdot \sigma^2}{2}
\]

### Optimal Spending Rate

For an infinite horizon:

\[
c^* = r_{CE} - \frac{r_{CE} - \rho}{\gamma}
\]

Where \(\rho\) is your time preference (discount rate).

## Quick Start

```python
from fundedness import (
    calculate_merton_optimal,
    MarketModel,
    UtilityModel,
)

# Define market assumptions
market = MarketModel(
    stock_return=0.05,      # 5% expected real return
    bond_return=0.015,      # 1.5% risk-free rate
    stock_volatility=0.16,  # 16% annual volatility
)

# Define your preferences
utility = UtilityModel(
    gamma=3.0,              # Risk aversion (typical: 2-5)
    subsistence_floor=30000,  # Minimum annual spending
    time_preference=0.02,   # 2% discount rate
)

# Calculate optimal policy
result = calculate_merton_optimal(
    wealth=1_000_000,
    market_model=market,
    utility_model=utility,
    remaining_years=30,
)

print(f"Optimal equity allocation: {result.optimal_equity_allocation:.1%}")
print(f"Wealth-adjusted allocation: {result.wealth_adjusted_allocation:.1%}")
print(f"Optimal spending rate: {result.optimal_spending_rate:.1%}")
print(f"Year 1 spending: ${1_000_000 * result.optimal_spending_rate:,.0f}")
```

## Wealth-Adjusted Allocation

Near the subsistence floor, you can't afford to take risk. The wealth-adjusted allocation accounts for this:

\[
k_{adj} = k^* \cdot \frac{W - F}{W}
\]

Where \(W\) is wealth and \(F\) is the subsistence floor.

As wealth approaches the floor, allocation approaches zero. As wealth rises far above the floor, allocation approaches the unconstrained optimal.

```python
from fundedness import wealth_adjusted_optimal_allocation

# Near the floor: low allocation
k_low = wealth_adjusted_optimal_allocation(
    wealth=50_000,  # Just above $30k floor
    market_model=market,
    utility_model=utility,
)
print(f"Allocation at $50k: {k_low:.1%}")  # ~18%

# Well above floor: approaches optimal
k_high = wealth_adjusted_optimal_allocation(
    wealth=2_000_000,
    market_model=market,
    utility_model=utility,
)
print(f"Allocation at $2M: {k_high:.1%}")  # ~44%
```

## Spending Rate by Age

Optimal spending rate increases with age as the remaining horizon shortens:

```python
from fundedness import optimal_spending_by_age

rates = optimal_spending_by_age(
    market_model=market,
    utility_model=utility,
    starting_age=65,
    end_age=95,
)

for age in [65, 75, 85, 95]:
    print(f"Age {age}: {rates[age]:.1%}")
```

Example output:
```
Age 65: 3.8%
Age 75: 5.2%
Age 85: 7.8%
Age 95: 100.0%
```

## Using Merton Policies in Simulation

### Merton Spending Policy

```python
from fundedness.withdrawals import MertonOptimalSpendingPolicy
from fundedness.allocation import MertonOptimalAllocationPolicy
from fundedness import run_simulation_with_utility, SimulationConfig

# Create policies
spending_policy = MertonOptimalSpendingPolicy(
    market_model=market,
    utility_model=utility,
    starting_age=65,
    end_age=95,
)

allocation_policy = MertonOptimalAllocationPolicy(
    market_model=market,
    utility_model=utility,
)

# Run simulation with utility tracking
config = SimulationConfig(
    n_simulations=5000,
    n_years=30,
    market_model=market,
)

result = run_simulation_with_utility(
    initial_wealth=1_000_000,
    spending_policy=spending_policy,
    allocation_policy=allocation_policy,
    config=config,
    utility_model=utility,
)

print(f"Expected lifetime utility: {result.expected_lifetime_utility:.2e}")
print(f"Certainty equivalent: ${result.certainty_equivalent_consumption:,.0f}/year")
print(f"Success rate: {result.success_rate:.1%}")
```

## Key Insights

1. **Spending rate increases with age** - As the horizon shortens, you should spend more
2. **Allocation decreases near the floor** - You can't afford risk when close to subsistence
3. **Risk aversion (gamma) is critical** - Higher gamma means lower allocation and spending
4. **The 4% rule is often suboptimal** - Merton optimal typically starts lower and ends higher

## Choosing Your Risk Aversion

Risk aversion (gamma) is the most important input. Guidelines:

| Gamma | Risk Tolerance | Profile |
|-------|----------------|---------|
| 1-2 | High | Comfortable with volatility |
| 2-3 | Moderate | Typical investor |
| 3-5 | Low | Prefers stability |
| 5+ | Very low | Strong loss aversion |

## References

- Merton, R. C. (1969). Lifetime Portfolio Selection under Uncertainty: The Continuous-Time Case. *The Review of Economics and Statistics*, 51(3), 247-257.
- Haghani, V., & White, J. (2023). *The Missing Billionaires: A Guide to Better Financial Decisions*. Wiley.
