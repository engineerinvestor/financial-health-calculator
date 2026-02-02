"""Merton optimal allocation policy based on utility maximization."""

from dataclasses import dataclass, field

import numpy as np

from fundedness.merton import (
    merton_optimal_allocation,
    wealth_adjusted_optimal_allocation,
)
from fundedness.models.market import MarketModel
from fundedness.models.utility import UtilityModel


@dataclass
class MertonOptimalAllocationPolicy:
    """Allocation policy based on Merton optimal portfolio theory.

    This policy determines equity allocation using the Merton formula,
    with adjustments for wealth level relative to subsistence floor.

    Key characteristics:
    - Base allocation from Merton: k* = (mu - r) / (gamma * sigma^2)
    - Allocation decreases as wealth approaches subsistence floor
    - Configurable bounds to prevent extreme positions

    Attributes:
        market_model: Market return and risk assumptions
        utility_model: Utility parameters including risk aversion
        min_equity: Minimum equity allocation
        max_equity: Maximum equity allocation
        use_wealth_adjustment: Whether to reduce allocation near floor
    """

    market_model: MarketModel = field(default_factory=MarketModel)
    utility_model: UtilityModel = field(default_factory=UtilityModel)
    min_equity: float = 0.0
    max_equity: float = 1.0
    use_wealth_adjustment: bool = True

    @property
    def name(self) -> str:
        k_star = merton_optimal_allocation(self.market_model, self.utility_model)
        return f"Merton Optimal ({k_star:.0%})"

    def get_unconstrained_allocation(self) -> float:
        """Get the unconstrained Merton optimal allocation.

        Returns:
            Optimal equity allocation (may exceed bounds)
        """
        return merton_optimal_allocation(self.market_model, self.utility_model)

    def get_allocation(
        self,
        wealth: float | np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> float | np.ndarray:
        """Get the optimal stock allocation.

        Args:
            wealth: Current portfolio value(s)
            year: Current year in simulation (not used but required by interface)
            initial_wealth: Starting portfolio value (not used but required)

        Returns:
            Stock allocation as decimal (0-1), scalar or array matching wealth
        """
        if not self.use_wealth_adjustment:
            # Use fixed Merton optimal allocation
            k_star = merton_optimal_allocation(self.market_model, self.utility_model)
            return np.clip(k_star, self.min_equity, self.max_equity)

        # Apply wealth-adjusted allocation
        if isinstance(wealth, np.ndarray):
            allocations = np.zeros_like(wealth, dtype=float)
            for i, w in enumerate(wealth):
                allocations[i] = wealth_adjusted_optimal_allocation(
                    wealth=w,
                    market_model=self.market_model,
                    utility_model=self.utility_model,
                    min_allocation=self.min_equity,
                    max_allocation=self.max_equity,
                )
            return allocations
        else:
            return wealth_adjusted_optimal_allocation(
                wealth=wealth,
                market_model=self.market_model,
                utility_model=self.utility_model,
                min_allocation=self.min_equity,
                max_allocation=self.max_equity,
            )


@dataclass
class WealthBasedAllocationPolicy:
    """Allocation that varies with wealth relative to floor.

    This is a simplified version that linearly interpolates between
    a minimum allocation at the floor and maximum at a target wealth.

    More intuitive than full Merton but captures the key insight that
    risk capacity depends on distance from subsistence.

    Attributes:
        floor_wealth: Wealth level at which equity is at minimum
        target_wealth: Wealth level at which equity reaches maximum
        min_equity: Equity allocation at floor
        max_equity: Equity allocation at target and above
    """

    floor_wealth: float = 500_000
    target_wealth: float = 2_000_000
    min_equity: float = 0.2
    max_equity: float = 0.8

    @property
    def name(self) -> str:
        return f"Wealth-Based ({self.min_equity:.0%}-{self.max_equity:.0%})"

    def get_allocation(
        self,
        wealth: float | np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> float | np.ndarray:
        """Get allocation based on current wealth level.

        Args:
            wealth: Current portfolio value(s)
            year: Current year (not used)
            initial_wealth: Starting value (not used)

        Returns:
            Stock allocation interpolated by wealth
        """
        # Linear interpolation between floor and target
        wealth_range = self.target_wealth - self.floor_wealth
        equity_range = self.max_equity - self.min_equity

        if isinstance(wealth, np.ndarray):
            progress = (wealth - self.floor_wealth) / wealth_range
            progress = np.clip(progress, 0, 1)
            return self.min_equity + progress * equity_range
        else:
            progress = (wealth - self.floor_wealth) / wealth_range
            progress = max(0, min(1, progress))
            return self.min_equity + progress * equity_range


@dataclass
class FloorProtectionAllocationPolicy:
    """Allocation that increases equity as wealth grows above floor.

    Inspired by CPPI (Constant Proportion Portfolio Insurance), this
    policy allocates equity as a multiple of the "cushion" (wealth above
    the floor-protection level).

    Attributes:
        utility_model: For subsistence floor value
        multiplier: Equity = multiplier * (wealth - floor_reserve) / wealth
        floor_years: Years of floor spending to protect
        min_equity: Minimum equity allocation
        max_equity: Maximum equity allocation
    """

    utility_model: UtilityModel = field(default_factory=UtilityModel)
    multiplier: float = 3.0
    floor_years: int = 10
    min_equity: float = 0.1
    max_equity: float = 0.9

    @property
    def name(self) -> str:
        return f"Floor Protection (m={self.multiplier})"

    def get_floor_reserve(self) -> float:
        """Get the wealth level that protects floor spending.

        Returns:
            Wealth needed to fund floor spending for floor_years
        """
        return self.utility_model.subsistence_floor * self.floor_years

    def get_allocation(
        self,
        wealth: float | np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> float | np.ndarray:
        """Get allocation based on cushion above floor reserve.

        Args:
            wealth: Current portfolio value(s)
            year: Current year (not used)
            initial_wealth: Starting value (not used)

        Returns:
            Stock allocation based on cushion
        """
        floor_reserve = self.get_floor_reserve()

        if isinstance(wealth, np.ndarray):
            cushion = np.maximum(wealth - floor_reserve, 0)
            # Equity = multiplier * cushion / wealth
            # But avoid division by zero
            allocation = np.where(
                wealth > 0,
                self.multiplier * cushion / wealth,
                0.0,
            )
            return np.clip(allocation, self.min_equity, self.max_equity)
        else:
            if wealth <= 0:
                return self.min_equity
            cushion = max(wealth - floor_reserve, 0)
            allocation = self.multiplier * cushion / wealth
            return max(self.min_equity, min(self.max_equity, allocation))
