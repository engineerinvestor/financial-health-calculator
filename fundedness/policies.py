"""Spending and allocation policy implementations."""

from dataclasses import dataclass

import numpy as np


@dataclass
class FixedRealSpending:
    """Fixed real (inflation-adjusted) spending policy."""

    annual_spending: float
    inflation_rate: float = 0.025

    def get_spending(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> np.ndarray:
        """Get spending, capped at available wealth."""
        nominal_spending = self.annual_spending * (1 + self.inflation_rate) ** year
        return np.minimum(nominal_spending, np.maximum(wealth, 0))


@dataclass
class PercentOfPortfolio:
    """Spend a fixed percentage of current portfolio value."""

    percentage: float = 0.04  # 4% rule
    floor: float | None = None
    ceiling: float | None = None

    def get_spending(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> np.ndarray:
        """Get spending as percentage of current wealth."""
        spending = wealth * self.percentage

        if self.floor is not None:
            spending = np.maximum(spending, self.floor)

        if self.ceiling is not None:
            spending = np.minimum(spending, self.ceiling)

        return np.minimum(spending, np.maximum(wealth, 0))


@dataclass
class ConstantAllocation:
    """Constant stock/bond allocation."""

    stock_weight: float = 0.6

    def get_allocation(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> float:
        """Return constant stock allocation."""
        return self.stock_weight


@dataclass
class AgeBasedGlidepath:
    """Age-based declining equity glidepath.

    Classic rule: stock_weight = 100 - age (or similar)
    """

    initial_stock_weight: float = 0.8
    final_stock_weight: float = 0.3
    years_to_final: int = 30
    starting_age: int = 65

    def get_allocation(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> float:
        """Calculate stock allocation based on years into retirement."""
        progress = min(year / self.years_to_final, 1.0)
        stock_weight = self.initial_stock_weight - progress * (
            self.initial_stock_weight - self.final_stock_weight
        )
        return stock_weight


@dataclass
class RisingEquityGlidepath:
    """Rising equity glidepath (bonds-first spending).

    Start conservative, increase equity over time as sequence risk decreases.
    """

    initial_stock_weight: float = 0.3
    final_stock_weight: float = 0.7
    years_to_final: int = 20

    def get_allocation(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> float:
        """Calculate stock allocation - increasing over time."""
        progress = min(year / self.years_to_final, 1.0)
        stock_weight = self.initial_stock_weight + progress * (
            self.final_stock_weight - self.initial_stock_weight
        )
        return stock_weight


@dataclass
class FundednessBasedAllocation:
    """Adjust allocation based on current fundedness level.

    Higher fundedness = can take more risk
    Lower fundedness = reduce risk to protect floor
    """

    target_fundedness: float = 1.2  # Target CEFR
    max_stock_weight: float = 0.8
    min_stock_weight: float = 0.2
    liability_pv: float = 1_000_000  # PV of future spending

    def get_allocation(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> np.ndarray:
        """Calculate allocation based on current fundedness."""
        # Simple fundedness estimate (wealth / liability PV)
        # In practice, would recalculate full CEFR
        fundedness = wealth / self.liability_pv

        # Linear interpolation based on fundedness
        # At target fundedness, use moderate allocation
        # Above target, can increase stocks
        # Below target, reduce stocks

        relative_fundedness = fundedness / self.target_fundedness

        # Map to allocation range
        stock_weight = self.min_stock_weight + (self.max_stock_weight - self.min_stock_weight) * (
            np.clip(relative_fundedness, 0.5, 1.5) - 0.5
        )

        return np.clip(stock_weight, self.min_stock_weight, self.max_stock_weight)


@dataclass
class FloorCeilingSpending:
    """Spending policy with floor and ceiling guardrails.

    Attempts to maintain target spending but:
    - Never spends below floor (essential spending)
    - Never spends above ceiling (luxury cap)
    - Adjusts based on portfolio performance
    """

    target_spending: float
    floor_spending: float
    ceiling_spending: float
    adjustment_rate: float = 0.05  # How fast to adjust toward target

    def __post_init__(self):
        self._previous_spending = None

    def get_spending(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> np.ndarray:
        """Calculate spending with guardrails."""
        if self._previous_spending is None:
            self._previous_spending = np.full_like(wealth, self.target_spending)

        # Calculate sustainable spending estimate (simplified)
        sustainable_rate = 0.04  # Simple 4% estimate
        sustainable_spending = wealth * sustainable_rate

        # Target is previous spending (smoothing)
        target = self._previous_spending

        # Adjust target toward sustainable level
        target = target + self.adjustment_rate * (sustainable_spending - target)

        # Apply floor and ceiling
        spending = np.clip(target, self.floor_spending, self.ceiling_spending)

        # Can't spend more than wealth
        spending = np.minimum(spending, np.maximum(wealth, 0))

        self._previous_spending = spending

        return spending
