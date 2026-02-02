# Merton Optimal API Reference

This module provides Merton's optimal consumption and portfolio choice formulas.

## Core Functions

::: fundedness.merton.merton_optimal_allocation
    options:
      show_root_heading: true

::: fundedness.merton.certainty_equivalent_return
    options:
      show_root_heading: true

::: fundedness.merton.merton_optimal_spending_rate
    options:
      show_root_heading: true

::: fundedness.merton.wealth_adjusted_optimal_allocation
    options:
      show_root_heading: true

::: fundedness.merton.calculate_merton_optimal
    options:
      show_root_heading: true

## Helper Functions

::: fundedness.merton.optimal_spending_by_age
    options:
      show_root_heading: true

::: fundedness.merton.optimal_allocation_by_wealth
    options:
      show_root_heading: true

## Data Classes

::: fundedness.merton.MertonOptimalResult
    options:
      show_root_heading: true

## Spending Policies

::: fundedness.withdrawals.merton_optimal.MertonOptimalSpendingPolicy
    options:
      show_root_heading: true

::: fundedness.withdrawals.merton_optimal.SmoothedMertonPolicy
    options:
      show_root_heading: true

::: fundedness.withdrawals.merton_optimal.FloorAdjustedMertonPolicy
    options:
      show_root_heading: true

## Allocation Policies

::: fundedness.allocation.merton_optimal.MertonOptimalAllocationPolicy
    options:
      show_root_heading: true

::: fundedness.allocation.merton_optimal.WealthBasedAllocationPolicy
    options:
      show_root_heading: true

::: fundedness.allocation.merton_optimal.FloorProtectionAllocationPolicy
    options:
      show_root_heading: true

## Policy Optimization

::: fundedness.optimize.PolicyParameterSpec
    options:
      show_root_heading: true

::: fundedness.optimize.OptimizationResult
    options:
      show_root_heading: true

::: fundedness.optimize.optimize_spending_policy
    options:
      show_root_heading: true

::: fundedness.optimize.optimize_allocation_policy
    options:
      show_root_heading: true

::: fundedness.optimize.optimize_combined_policy
    options:
      show_root_heading: true
