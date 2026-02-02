"""RMD-style withdrawal strategy."""

from dataclasses import dataclass

import numpy as np

from fundedness.withdrawals.base import (
    BaseWithdrawalPolicy,
    WithdrawalContext,
    WithdrawalDecision,
)


# IRS Uniform Lifetime Table (2024)
# Maps age to distribution period (divisor)
RMD_TABLE = {
    72: 27.4, 73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7,
    77: 22.9, 78: 22.0, 79: 21.1, 80: 20.2, 81: 19.4,
    82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2,
    87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5,
    92: 10.8, 93: 10.1, 94: 9.5, 95: 8.9, 96: 8.4,
    97: 7.8, 98: 7.3, 99: 6.8, 100: 6.4, 101: 6.0,
    102: 5.6, 103: 5.2, 104: 4.9, 105: 4.6, 106: 4.3,
    107: 4.1, 108: 3.9, 109: 3.7, 110: 3.5, 111: 3.4,
    112: 3.3, 113: 3.1, 114: 3.0, 115: 2.9, 116: 2.8,
    117: 2.7, 118: 2.5, 119: 2.3, 120: 2.0,
}


def get_rmd_divisor(age: int) -> float:
    """Get RMD distribution period for given age.

    Args:
        age: Current age

    Returns:
        Distribution period (divisor)
    """
    if age < 72:
        # Extrapolate backwards (not actual RMD, but useful for strategy)
        return 27.4 + (72 - age) * 1.0  # Approximate slope
    elif age > 120:
        return 2.0
    else:
        return RMD_TABLE.get(age, 2.0)


@dataclass
class RMDStylePolicy(BaseWithdrawalPolicy):
    """RMD-style withdrawal strategy.

    Uses IRS Required Minimum Distribution table to determine withdrawals.
    Withdrawal = Portfolio Value / Distribution Period

    This approach automatically increases withdrawal rate as you age,
    similar to how RMDs work for tax-deferred accounts.
    """

    starting_age: int = 65
    multiplier: float = 1.0  # Scale factor (1.0 = exact RMD, 1.5 = 150% of RMD)
    start_before_72: bool = True  # Apply RMD-style before actual RMD age

    @property
    def name(self) -> str:
        mult_str = f" × {self.multiplier}" if self.multiplier != 1.0 else ""
        return f"RMD-Style{mult_str}"

    @property
    def description(self) -> str:
        return (
            "Withdraw based on IRS RMD table divisors. "
            "Withdrawal rate automatically increases with age."
        )

    def get_initial_withdrawal(self, initial_wealth: float) -> float:
        """Calculate first year withdrawal."""
        divisor = get_rmd_divisor(self.starting_age)
        return (initial_wealth / divisor) * self.multiplier

    def calculate_withdrawal(self, context: WithdrawalContext) -> WithdrawalDecision:
        """Calculate RMD-style withdrawal.

        Args:
            context: Current state including age or year

        Returns:
            WithdrawalDecision based on RMD table
        """
        # Determine current age
        if context.age is not None:
            current_age = context.age
        else:
            current_age = self.starting_age + context.year

        # Get divisor
        divisor = get_rmd_divisor(current_age)

        # Calculate withdrawal
        if isinstance(context.current_wealth, np.ndarray):
            amount = (context.current_wealth / divisor) * self.multiplier
        else:
            amount = (context.current_wealth / divisor) * self.multiplier

        # Apply guardrails
        amount, is_floor_breach, is_ceiling_hit = self.apply_guardrails(
            amount, context.current_wealth
        )

        withdrawal_rate = 1 / divisor * self.multiplier

        return WithdrawalDecision(
            amount=amount,
            is_floor_breach=is_floor_breach,
            is_ceiling_hit=is_ceiling_hit,
            notes=f"Age {current_age}, divisor: {divisor:.1f}, rate: {withdrawal_rate:.2%}",
        )


@dataclass
class AmortizationPolicy(BaseWithdrawalPolicy):
    """Amortization-based withdrawal strategy.

    Treats the portfolio like a mortgage in reverse - calculates the level
    payment that would exhaust the portfolio over the planning horizon
    given expected returns.
    """

    starting_age: int = 65
    planning_age: int = 95  # Age to plan to
    expected_return: float = 0.04  # Expected real return
    recalculate_annually: bool = True  # Recalculate each year

    @property
    def name(self) -> str:
        return "Amortization"

    @property
    def description(self) -> str:
        return (
            f"Calculate level payment to exhaust portfolio by age {self.planning_age} "
            f"assuming {self.expected_return:.1%} real return."
        )

    def _calculate_pmt(self, wealth: float, years_remaining: int) -> float:
        """Calculate amortization payment.

        PMT = PV * r / (1 - (1+r)^-n)
        """
        if years_remaining <= 0:
            return wealth  # Spend it all

        r = self.expected_return
        n = years_remaining

        if r == 0:
            return wealth / n

        # Standard amortization formula
        pmt = wealth * r / (1 - (1 + r) ** (-n))
        return pmt

    def get_initial_withdrawal(self, initial_wealth: float) -> float:
        """Calculate first year withdrawal."""
        years = self.planning_age - self.starting_age
        return self._calculate_pmt(initial_wealth, years)

    def calculate_withdrawal(self, context: WithdrawalContext) -> WithdrawalDecision:
        """Calculate amortization-based withdrawal.

        Args:
            context: Current state

        Returns:
            WithdrawalDecision based on amortization formula
        """
        # Determine current age and years remaining
        if context.age is not None:
            current_age = context.age
        else:
            current_age = self.starting_age + context.year

        years_remaining = max(1, self.planning_age - current_age)

        # Calculate payment
        if isinstance(context.current_wealth, np.ndarray):
            amount = np.array([
                self._calculate_pmt(w, years_remaining)
                for w in context.current_wealth
            ])
        else:
            amount = self._calculate_pmt(context.current_wealth, years_remaining)

        # Apply guardrails
        amount, is_floor_breach, is_ceiling_hit = self.apply_guardrails(
            amount, context.current_wealth
        )

        return WithdrawalDecision(
            amount=amount,
            is_floor_breach=is_floor_breach,
            is_ceiling_hit=is_ceiling_hit,
            notes=f"Years remaining: {years_remaining}",
        )
