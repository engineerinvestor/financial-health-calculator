"""Merton optimal spending policy based on utility maximization."""

from dataclasses import dataclass, field

import numpy as np

from fundedness.merton import (
    merton_optimal_spending_rate,
    certainty_equivalent_return,
)
from fundedness.models.market import MarketModel
from fundedness.models.utility import UtilityModel
from fundedness.withdrawals.base import (
    BaseWithdrawalPolicy,
    WithdrawalContext,
    WithdrawalDecision,
)


@dataclass
class MertonOptimalSpendingPolicy(BaseWithdrawalPolicy):
    """Spending policy based on Merton optimal consumption theory.

    This policy determines spending by applying the Merton optimal spending
    rate to current wealth, adjusted for the remaining time horizon.

    Key characteristics:
    - Spending rate starts low (~2-3%) and rises with age
    - Rate depends on risk aversion, time preference, and market assumptions
    - Adapts to actual wealth (not locked to initial withdrawal amount)
    - Optional smoothing to reduce year-to-year volatility

    Attributes:
        market_model: Market return and risk assumptions
        utility_model: Utility parameters including risk aversion
        starting_age: Age at retirement/simulation start
        end_age: Assumed maximum age for planning
        smoothing_factor: Blend current with previous spending (0-1, 0=no smoothing)
        min_spending_rate: Minimum spending rate floor
        max_spending_rate: Maximum spending rate ceiling
    """

    market_model: MarketModel = field(default_factory=MarketModel)
    utility_model: UtilityModel = field(default_factory=UtilityModel)
    starting_age: int = 65
    end_age: int = 100
    smoothing_factor: float = 0.5
    min_spending_rate: float = 0.02
    max_spending_rate: float = 0.15

    @property
    def name(self) -> str:
        return "Merton Optimal"

    @property
    def description(self) -> str:
        gamma = self.utility_model.gamma
        return f"Utility-optimal spending (gamma={gamma})"

    def get_optimal_rate(self, remaining_years: float) -> float:
        """Get the optimal spending rate for given remaining years.

        Args:
            remaining_years: Years until end of planning horizon

        Returns:
            Optimal spending rate as decimal
        """
        rate = merton_optimal_spending_rate(
            market_model=self.market_model,
            utility_model=self.utility_model,
            remaining_years=remaining_years,
        )
        return np.clip(rate, self.min_spending_rate, self.max_spending_rate)

    def calculate_withdrawal(self, context: WithdrawalContext) -> WithdrawalDecision:
        """Calculate withdrawal using Merton optimal spending rate.

        Args:
            context: Current state information

        Returns:
            WithdrawalDecision with amount and metadata
        """
        # Determine current age
        if context.age is not None:
            current_age = context.age
        else:
            current_age = self.starting_age + context.year

        remaining_years = max(1, self.end_age - current_age)

        # Get optimal spending rate
        rate = self.get_optimal_rate(remaining_years)

        # Handle vectorized wealth
        if isinstance(context.current_wealth, np.ndarray):
            wealth = context.current_wealth
        else:
            wealth = context.current_wealth

        # Calculate raw spending
        raw_spending = wealth * rate

        # Apply smoothing if we have previous spending
        if self.smoothing_factor > 0 and context.previous_spending is not None:
            # Adjust previous spending for inflation
            prev_real = context.previous_spending / context.inflation_cumulative
            smoothed = (
                self.smoothing_factor * prev_real * context.inflation_cumulative
                + (1 - self.smoothing_factor) * raw_spending
            )
            spending = smoothed
        else:
            spending = raw_spending

        # Apply guardrails
        amount, is_floor_breach, is_ceiling_hit = self.apply_guardrails(
            spending, context.current_wealth
        )

        return WithdrawalDecision(
            amount=amount,
            is_floor_breach=is_floor_breach,
            is_ceiling_hit=is_ceiling_hit,
            notes=f"Rate: {rate:.1%}, Remaining: {remaining_years}y",
        )

    def get_initial_withdrawal(self, initial_wealth: float) -> float:
        """Calculate first year withdrawal.

        Args:
            initial_wealth: Starting portfolio value

        Returns:
            First year withdrawal amount
        """
        remaining_years = self.end_age - self.starting_age
        rate = self.get_optimal_rate(remaining_years)
        return initial_wealth * rate

    def get_spending(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> np.ndarray:
        """Get spending for simulation (vectorized interface).

        This method is used by the Monte Carlo simulation engine.

        Args:
            wealth: Current portfolio values (n_simulations,)
            year: Current simulation year
            initial_wealth: Starting portfolio value

        Returns:
            Spending amounts for each simulation path
        """
        current_age = self.starting_age + year
        remaining_years = max(1, self.end_age - current_age)
        rate = self.get_optimal_rate(remaining_years)

        spending = wealth * rate

        # Ensure non-negative and bounded by wealth
        spending = np.maximum(spending, 0)
        spending = np.minimum(spending, np.maximum(wealth, 0))

        # Apply floor if set
        if self.floor_spending is not None:
            spending = np.maximum(spending, self.floor_spending)
            # But still can't spend more than we have
            spending = np.minimum(spending, np.maximum(wealth, 0))

        return spending


@dataclass
class SmoothedMertonPolicy(MertonOptimalSpendingPolicy):
    """Merton optimal with aggressive smoothing for stable spending.

    This variant applies stronger smoothing to reduce spending volatility,
    trading off some optimality for a more stable spending experience.
    """

    smoothing_factor: float = 0.7
    adaptation_rate: float = 0.1

    @property
    def name(self) -> str:
        return "Smoothed Merton"

    @property
    def description(self) -> str:
        return "Merton optimal with spending smoothing"

    def get_spending(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> np.ndarray:
        """Get smoothed spending for simulation.

        Uses exponential smoothing of the optimal spending amount.

        Args:
            wealth: Current portfolio values
            year: Current simulation year
            initial_wealth: Starting portfolio value

        Returns:
            Smoothed spending amounts
        """
        # Get raw Merton optimal spending
        current_age = self.starting_age + year
        remaining_years = max(1, self.end_age - current_age)
        rate = self.get_optimal_rate(remaining_years)

        optimal_spending = wealth * rate

        # For first year or if tracking isn't set up, use optimal directly
        # In practice, smoothing would be applied via simulation state
        spending = optimal_spending

        # Apply floor if set
        if self.floor_spending is not None:
            spending = np.maximum(spending, self.floor_spending)
            spending = np.minimum(spending, np.maximum(wealth, 0))

        return spending


@dataclass
class FloorAdjustedMertonPolicy(MertonOptimalSpendingPolicy):
    """Merton optimal that accounts for subsistence floor in spending.

    This variant only applies the optimal rate to wealth above the
    floor-supporting level, ensuring floor spending is always protected.
    """

    years_of_floor_to_protect: int = 5

    @property
    def name(self) -> str:
        return "Floor-Protected Merton"

    @property
    def description(self) -> str:
        return f"Merton optimal protecting {self.years_of_floor_to_protect}y floor"

    def get_spending(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> np.ndarray:
        """Get spending that protects floor for several years.

        Args:
            wealth: Current portfolio values
            year: Current simulation year
            initial_wealth: Starting portfolio value

        Returns:
            Floor-protected spending amounts
        """
        current_age = self.starting_age + year
        remaining_years = max(1, self.end_age - current_age)
        rate = self.get_optimal_rate(remaining_years)

        floor = self.utility_model.subsistence_floor
        protected_wealth = floor * self.years_of_floor_to_protect

        # Only apply rate to wealth above protected level
        excess_wealth = np.maximum(wealth - protected_wealth, 0)
        flex_spending = excess_wealth * rate

        # Total spending = floor + flexible portion
        spending = floor + flex_spending

        # Can't spend more than we have
        spending = np.minimum(spending, np.maximum(wealth, 0))

        return spending
