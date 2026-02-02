"""Variable Percentage Withdrawal (VPW) strategy."""

from dataclasses import dataclass

import numpy as np

from fundedness.withdrawals.base import (
    BaseWithdrawalPolicy,
    WithdrawalContext,
    WithdrawalDecision,
)


# VPW percentage table based on age and asset allocation
# Source: Bogleheads VPW methodology
# These are the percentages of portfolio to withdraw at each age
VPW_TABLE = {
    # Age: {stock_pct: withdrawal_pct}
    # Simplified table - in practice would interpolate
    60: {0: 0.037, 25: 0.039, 50: 0.042, 75: 0.046, 100: 0.051},
    65: {0: 0.041, 25: 0.044, 50: 0.047, 75: 0.052, 100: 0.058},
    70: {0: 0.047, 25: 0.050, 50: 0.054, 75: 0.060, 100: 0.068},
    75: {0: 0.054, 25: 0.058, 50: 0.064, 75: 0.071, 100: 0.081},
    80: {0: 0.064, 25: 0.069, 50: 0.076, 75: 0.086, 100: 0.099},
    85: {0: 0.078, 25: 0.084, 50: 0.093, 75: 0.106, 100: 0.124},
    90: {0: 0.097, 25: 0.106, 50: 0.118, 75: 0.135, 100: 0.160},
    95: {0: 0.127, 25: 0.139, 50: 0.156, 75: 0.180, 100: 0.214},
}


def get_vpw_rate(age: int, stock_allocation: int = 50) -> float:
    """Get VPW withdrawal rate for given age and allocation.

    Args:
        age: Current age
        stock_allocation: Stock allocation as integer percentage (0-100)

    Returns:
        Withdrawal rate as decimal
    """
    # Find bracketing ages
    ages = sorted(VPW_TABLE.keys())

    if age <= ages[0]:
        age_key = ages[0]
    elif age >= ages[-1]:
        age_key = ages[-1]
    else:
        # Find closest age
        age_key = min(ages, key=lambda x: abs(x - age))

    # Find closest allocation
    allocations = sorted(VPW_TABLE[age_key].keys())
    if stock_allocation <= allocations[0]:
        alloc_key = allocations[0]
    elif stock_allocation >= allocations[-1]:
        alloc_key = allocations[-1]
    else:
        alloc_key = min(allocations, key=lambda x: abs(x - stock_allocation))

    return VPW_TABLE[age_key][alloc_key]


@dataclass
class VPWPolicy(BaseWithdrawalPolicy):
    """Variable Percentage Withdrawal (VPW) strategy.

    Withdrawal rate varies based on age and remaining life expectancy.
    Uses actuarial tables to determine appropriate withdrawal percentage.
    """

    starting_age: int = 65
    stock_allocation: int = 50  # As integer percentage
    smoothing_factor: float = 0.0  # 0 = pure VPW, 1 = fully smoothed

    @property
    def name(self) -> str:
        return "VPW"

    @property
    def description(self) -> str:
        return (
            "Variable Percentage Withdrawal based on age and life expectancy. "
            "Withdrawal rate increases as you age."
        )

    def get_initial_withdrawal(self, initial_wealth: float) -> float:
        """Calculate first year withdrawal."""
        rate = get_vpw_rate(self.starting_age, self.stock_allocation)
        return initial_wealth * rate

    def calculate_withdrawal(self, context: WithdrawalContext) -> WithdrawalDecision:
        """Calculate VPW withdrawal.

        Args:
            context: Current state including age or year

        Returns:
            WithdrawalDecision based on VPW table
        """
        # Determine current age
        if context.age is not None:
            current_age = context.age
        else:
            current_age = self.starting_age + context.year

        # Get VPW rate for current age
        vpw_rate = get_vpw_rate(current_age, self.stock_allocation)

        # Calculate base withdrawal
        if isinstance(context.current_wealth, np.ndarray):
            base_amount = context.current_wealth * vpw_rate
        else:
            base_amount = context.current_wealth * vpw_rate

        # Apply smoothing if requested
        if self.smoothing_factor > 0 and context.previous_spending is not None:
            smoothed = (
                self.smoothing_factor * context.previous_spending
                + (1 - self.smoothing_factor) * base_amount
            )
            amount = smoothed
        else:
            amount = base_amount

        # Apply guardrails
        amount, is_floor_breach, is_ceiling_hit = self.apply_guardrails(
            amount, context.current_wealth
        )

        return WithdrawalDecision(
            amount=amount,
            is_floor_breach=is_floor_breach,
            is_ceiling_hit=is_ceiling_hit,
            notes=f"Age {current_age}, VPW rate: {vpw_rate:.2%}",
        )
