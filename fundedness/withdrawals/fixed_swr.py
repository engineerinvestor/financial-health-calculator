"""Fixed Safe Withdrawal Rate (SWR) policy."""

from dataclasses import dataclass

import numpy as np

from fundedness.withdrawals.base import (
    BaseWithdrawalPolicy,
    WithdrawalContext,
    WithdrawalDecision,
)


@dataclass
class FixedRealSWRPolicy(BaseWithdrawalPolicy):
    """Classic fixed real (inflation-adjusted) withdrawal strategy.

    The "4% rule" approach: withdraw a fixed percentage of initial portfolio,
    then adjust for inflation each year.
    """

    withdrawal_rate: float = 0.04  # 4% default
    inflation_rate: float = 0.025  # 2.5% expected inflation

    @property
    def name(self) -> str:
        return f"Fixed {self.withdrawal_rate:.1%} SWR"

    @property
    def description(self) -> str:
        return (
            f"Withdraw {self.withdrawal_rate:.1%} of initial portfolio in year 1, "
            f"then adjust for {self.inflation_rate:.1%} inflation annually."
        )

    def get_initial_withdrawal(self, initial_wealth: float) -> float:
        """Calculate first year withdrawal."""
        return initial_wealth * self.withdrawal_rate

    def calculate_withdrawal(self, context: WithdrawalContext) -> WithdrawalDecision:
        """Calculate inflation-adjusted withdrawal.

        Args:
            context: Current state including initial wealth and year

        Returns:
            WithdrawalDecision with fixed real amount
        """
        # Base withdrawal from initial wealth
        base_amount = context.initial_wealth * self.withdrawal_rate

        # Adjust for cumulative inflation
        inflation_factor = (1 + self.inflation_rate) ** context.year
        nominal_amount = base_amount * inflation_factor

        # Apply guardrails and wealth cap
        amount, is_floor_breach, is_ceiling_hit = self.apply_guardrails(
            nominal_amount, context.current_wealth
        )

        return WithdrawalDecision(
            amount=amount,
            is_floor_breach=is_floor_breach,
            is_ceiling_hit=is_ceiling_hit,
            notes=f"Year {context.year}: base ${base_amount:,.0f} × {inflation_factor:.3f} inflation",
        )

    def get_spending(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> np.ndarray:
        """Get spending for simulation (vectorized interface).

        Args:
            wealth: Current portfolio values (n_simulations,)
            year: Current simulation year
            initial_wealth: Starting portfolio value

        Returns:
            Spending amounts for each simulation path
        """
        # Base withdrawal from initial wealth
        base_amount = initial_wealth * self.withdrawal_rate

        # Adjust for cumulative inflation
        inflation_factor = (1 + self.inflation_rate) ** year
        spending = np.full_like(wealth, base_amount * inflation_factor)

        # Apply floor if set
        if self.floor_spending is not None:
            spending = np.maximum(spending, self.floor_spending)

        # Can't spend more than we have
        spending = np.minimum(spending, np.maximum(wealth, 0))

        return spending


@dataclass
class PercentOfPortfolioPolicy(BaseWithdrawalPolicy):
    """Withdraw a fixed percentage of current portfolio value each year.

    More volatile than fixed SWR but automatically adjusts to portfolio performance.
    """

    withdrawal_rate: float = 0.04
    floor: float | None = None

    @property
    def name(self) -> str:
        return f"{self.withdrawal_rate:.1%} of Portfolio"

    @property
    def description(self) -> str:
        return f"Withdraw {self.withdrawal_rate:.1%} of current portfolio value each year."

    def get_initial_withdrawal(self, initial_wealth: float) -> float:
        """Calculate first year withdrawal."""
        return initial_wealth * self.withdrawal_rate

    def calculate_withdrawal(self, context: WithdrawalContext) -> WithdrawalDecision:
        """Calculate percentage-of-portfolio withdrawal.

        Args:
            context: Current state including current wealth

        Returns:
            WithdrawalDecision based on current portfolio value
        """
        if isinstance(context.current_wealth, np.ndarray):
            amount = context.current_wealth * self.withdrawal_rate
        else:
            amount = context.current_wealth * self.withdrawal_rate

        # Apply guardrails
        amount, is_floor_breach, is_ceiling_hit = self.apply_guardrails(
            amount, context.current_wealth
        )

        return WithdrawalDecision(
            amount=amount,
            is_floor_breach=is_floor_breach,
            is_ceiling_hit=is_ceiling_hit,
        )

    def get_spending(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> np.ndarray:
        """Get spending for simulation (vectorized interface).

        Args:
            wealth: Current portfolio values (n_simulations,)
            year: Current simulation year
            initial_wealth: Starting portfolio value

        Returns:
            Spending amounts for each simulation path
        """
        spending = wealth * self.withdrawal_rate

        # Apply floor if set
        floor = self.floor or self.floor_spending
        if floor is not None:
            spending = np.maximum(spending, floor)

        # Can't spend more than we have
        spending = np.minimum(spending, np.maximum(wealth, 0))

        return spending
