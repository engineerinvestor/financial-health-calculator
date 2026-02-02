"""Merton optimal consumption and portfolio choice formulas.

Implements the analytical solutions from Robert Merton's continuous-time
portfolio optimization framework for retirement planning.

References:
- Merton, R.C. (1969). Lifetime Portfolio Selection under Uncertainty.
- Haghani, V. & White, J. (2023). The Missing Billionaires. Wiley.

Key formulas:
- Optimal equity allocation: k* = (mu - r) / (gamma * sigma^2)
- Certainty equivalent return: rce = r + k*(mu - r) - gamma*k^2*sigma^2/2
- Optimal spending rate: c* = rce - (rce - rtp) / gamma
"""

from dataclasses import dataclass

import numpy as np

from fundedness.models.market import MarketModel
from fundedness.models.utility import UtilityModel


@dataclass
class MertonOptimalResult:
    """Results from Merton optimal calculations."""

    optimal_equity_allocation: float
    certainty_equivalent_return: float
    optimal_spending_rate: float
    wealth_adjusted_allocation: float
    risk_premium: float
    portfolio_volatility: float


def merton_optimal_allocation(
    market_model: MarketModel,
    utility_model: UtilityModel,
) -> float:
    """Calculate Merton optimal equity allocation.

    The Merton formula gives the optimal fraction to invest in risky assets:
    k* = (mu - r) / (gamma * sigma^2)

    Args:
        market_model: Market return and risk assumptions
        utility_model: Utility parameters including risk aversion

    Returns:
        Optimal equity allocation as decimal (can exceed 1.0 for leveraged)
    """
    mu = market_model.stock_return
    r = market_model.bond_return
    gamma = utility_model.gamma
    sigma = market_model.stock_volatility

    if sigma == 0 or gamma == 0:
        return 0.0

    k_star = (mu - r) / (gamma * sigma**2)

    return k_star


def certainty_equivalent_return(
    market_model: MarketModel,
    utility_model: UtilityModel,
    equity_allocation: float | None = None,
) -> float:
    """Calculate certainty equivalent return for a portfolio.

    The certainty equivalent return is the guaranteed return that provides
    the same expected utility as the risky portfolio:
    rce = r + k*(mu - r) - gamma*k^2*sigma^2/2

    Args:
        market_model: Market return and risk assumptions
        utility_model: Utility parameters including risk aversion
        equity_allocation: Equity allocation (uses optimal if None)

    Returns:
        Certainty equivalent return as decimal
    """
    if equity_allocation is None:
        equity_allocation = merton_optimal_allocation(market_model, utility_model)

    mu = market_model.stock_return
    r = market_model.bond_return
    gamma = utility_model.gamma
    sigma = market_model.stock_volatility

    k = equity_allocation
    risk_premium = k * (mu - r)
    risk_penalty = gamma * k**2 * sigma**2 / 2

    rce = r + risk_premium - risk_penalty

    return rce


def merton_optimal_spending_rate(
    market_model: MarketModel,
    utility_model: UtilityModel,
    remaining_years: float | None = None,
) -> float:
    """Calculate Merton optimal spending rate.

    The optimal spending rate for an infinite horizon is:
    c* = rce - (rce - rtp) / gamma

    For finite horizons, the rate is adjusted upward as horizon shortens.

    Args:
        market_model: Market return and risk assumptions
        utility_model: Utility parameters including risk aversion and time preference
        remaining_years: Years until planning horizon ends (None for infinite)

    Returns:
        Optimal spending rate as decimal (e.g., 0.03 = 3%)
    """
    rce = certainty_equivalent_return(market_model, utility_model)
    rtp = utility_model.time_preference
    gamma = utility_model.gamma

    if gamma == 1.0:
        # Log utility special case
        c_star = rtp
    else:
        c_star = rce - (rce - rtp) / gamma

    # Finite horizon adjustment
    if remaining_years is not None and remaining_years > 0:
        # Use annuity factor to increase spending rate for finite horizon
        # c_finite = c_infinite + 1 / remaining_years (approximate)
        if rce > 0:
            # Annuity present value factor
            pv_factor = (1 - (1 + rce) ** (-remaining_years)) / rce
            if pv_factor > 0:
                annuity_rate = 1 / pv_factor
                c_star = max(c_star, annuity_rate)
        else:
            # With non-positive returns, simple 1/N rule
            c_star = max(c_star, 1 / remaining_years)

    return max(c_star, 0.0)  # Can't have negative spending


def wealth_adjusted_optimal_allocation(
    wealth: float,
    market_model: MarketModel,
    utility_model: UtilityModel,
    min_allocation: float = 0.0,
    max_allocation: float = 1.0,
) -> float:
    """Calculate wealth-adjusted optimal equity allocation.

    Near the subsistence floor, the optimal allocation approaches zero
    because the investor cannot afford to take risk. As wealth rises
    above the floor, allocation approaches the unconstrained Merton optimal.

    The formula is:
    k_adjusted = k* * (W - F) / W

    Where W is wealth and F is the subsistence floor.

    Args:
        wealth: Current portfolio value
        market_model: Market return and risk assumptions
        utility_model: Utility parameters
        min_allocation: Minimum equity allocation (floor)
        max_allocation: Maximum equity allocation (ceiling)

    Returns:
        Adjusted equity allocation as decimal, bounded by min/max
    """
    k_star = merton_optimal_allocation(market_model, utility_model)
    floor = utility_model.subsistence_floor

    if wealth <= floor:
        return min_allocation

    # Scale by distance from floor
    wealth_ratio = (wealth - floor) / wealth
    k_adjusted = k_star * wealth_ratio

    # Apply bounds
    return np.clip(k_adjusted, min_allocation, max_allocation)


def calculate_merton_optimal(
    wealth: float,
    market_model: MarketModel,
    utility_model: UtilityModel,
    remaining_years: float | None = None,
) -> MertonOptimalResult:
    """Calculate all Merton optimal values for given wealth.

    This is the main entry point for getting all optimal policy parameters.

    Args:
        wealth: Current portfolio value
        market_model: Market return and risk assumptions
        utility_model: Utility parameters
        remaining_years: Years until planning horizon ends

    Returns:
        MertonOptimalResult with all optimal values
    """
    k_star = merton_optimal_allocation(market_model, utility_model)
    rce = certainty_equivalent_return(market_model, utility_model)
    c_star = merton_optimal_spending_rate(market_model, utility_model, remaining_years)
    k_adjusted = wealth_adjusted_optimal_allocation(wealth, market_model, utility_model)

    risk_premium = market_model.stock_return - market_model.bond_return
    portfolio_vol = k_star * market_model.stock_volatility

    return MertonOptimalResult(
        optimal_equity_allocation=k_star,
        certainty_equivalent_return=rce,
        optimal_spending_rate=c_star,
        wealth_adjusted_allocation=k_adjusted,
        risk_premium=risk_premium,
        portfolio_volatility=portfolio_vol,
    )


def optimal_spending_by_age(
    market_model: MarketModel,
    utility_model: UtilityModel,
    starting_age: int,
    end_age: int = 100,
) -> dict[int, float]:
    """Calculate optimal spending rates for each age.

    Spending rate increases with age as the remaining horizon shortens.

    Args:
        market_model: Market return and risk assumptions
        utility_model: Utility parameters
        starting_age: Current age
        end_age: Assumed maximum age

    Returns:
        Dictionary mapping age to optimal spending rate
    """
    rates = {}
    for age in range(starting_age, end_age + 1):
        remaining_years = end_age - age
        if remaining_years <= 0:
            rates[age] = 1.0  # Spend everything at end
        else:
            rates[age] = merton_optimal_spending_rate(
                market_model, utility_model, remaining_years
            )
    return rates


def optimal_allocation_by_wealth(
    market_model: MarketModel,
    utility_model: UtilityModel,
    wealth_levels: np.ndarray,
    min_allocation: float = 0.0,
    max_allocation: float = 1.0,
) -> np.ndarray:
    """Calculate optimal allocation for a range of wealth levels.

    Useful for generating allocation curves showing how equity percentage
    should vary with distance from subsistence floor.

    Args:
        market_model: Market return and risk assumptions
        utility_model: Utility parameters
        wealth_levels: Array of wealth values to calculate for
        min_allocation: Minimum equity allocation
        max_allocation: Maximum equity allocation

    Returns:
        Array of optimal allocations corresponding to wealth_levels
    """
    allocations = np.zeros_like(wealth_levels, dtype=float)
    for i, wealth in enumerate(wealth_levels):
        allocations[i] = wealth_adjusted_optimal_allocation(
            wealth=wealth,
            market_model=market_model,
            utility_model=utility_model,
            min_allocation=min_allocation,
            max_allocation=max_allocation,
        )
    return allocations
