# Monte Carlo Simulations

Monte Carlo simulations help you understand the range of possible retirement outcomes by running thousands of scenarios with randomized market returns.

## How It Works

1. Generate random market returns based on historical distributions
2. Simulate portfolio growth and withdrawals over time
3. Track which scenarios succeed (don't run out of money)
4. Analyze the distribution of outcomes

## Running a Basic Simulation

```python
from fundedness import run_simulation

results = run_simulation(
    initial_portfolio=1_000_000,
    annual_spending=40_000,
    years=30,
    n_simulations=10_000,
)

print(f"Success Rate: {results.success_rate:.1%}")
print(f"Median Final Value: ${results.median_final_value:,.0f}")
print(f"5th Percentile: ${results.percentile_5:,.0f}")
print(f"95th Percentile: ${results.percentile_95:,.0f}")
```

## Market Assumptions

Default assumptions are based on historical data:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Mean Return | 7% | Expected annual real return |
| Std Dev | 15% | Annual volatility |
| Inflation | 2.5% | Expected inflation rate |

### Custom Assumptions

```python
from fundedness import MarketAssumptions, run_simulation

assumptions = MarketAssumptions(
    mean_return=0.06,  # More conservative
    std_dev=0.18,      # Higher volatility
    inflation=0.03,    # Higher inflation
)

results = run_simulation(
    initial_portfolio=1_000_000,
    annual_spending=40_000,
    years=30,
    assumptions=assumptions,
)
```

## Understanding Results

### Success Rate

The percentage of simulations that didn't run out of money. Common targets:

- **95%**: Very conservative
- **90%**: Conservative
- **85%**: Moderate
- **80%**: Aggressive

### Percentiles

- **5th percentile**: Poor outcomes (bear markets, bad timing)
- **50th percentile (median)**: Typical outcome
- **95th percentile**: Favorable outcomes (bull markets)

## Visualizing Results

```python
from fundedness.viz import plot_simulation_fan_chart

fig = plot_simulation_fan_chart(results)
fig.show()
```

The fan chart shows:

- **Dark band**: 25th-75th percentile (likely outcomes)
- **Light band**: 5th-95th percentile (range of outcomes)
- **Line**: Median trajectory

## Sensitivity Analysis

Test how changes affect your success rate:

```python
from fundedness import compare_scenarios

scenarios = [
    {"spending": 35_000, "label": "Conservative"},
    {"spending": 40_000, "label": "Baseline"},
    {"spending": 45_000, "label": "Aggressive"},
]

comparison = compare_scenarios(
    initial_portfolio=1_000_000,
    years=30,
    scenarios=scenarios,
)
```

## Limitations

Monte Carlo simulations have limitations:

1. **Past performance**: Historical returns may not predict future results
2. **Model assumptions**: Normal distributions may underestimate tail risks
3. **Constant spending**: Real spending varies year to year
4. **No behavioral factors**: Doesn't account for panic selling

Use simulations as one input to your planning, not the sole decision tool.
