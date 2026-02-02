"""Guardrails withdrawal strategy (Guyton-Klinger style)."""

from dataclasses import dataclass, field

import numpy as np

from fundedness.withdrawals.base import (
    BaseWithdrawalPolicy,
    WithdrawalContext,
    WithdrawalDecision,
)


@dataclass
class GuardrailsPolicy(BaseWithdrawalPolicy):
    """Guyton-Klinger style guardrails withdrawal strategy.

    Start with initial withdrawal rate, then adjust based on portfolio performance:
    - If withdrawal rate rises above upper guardrail, cut spending
    - If withdrawal rate falls below lower guardrail, increase spending
    - Otherwise, adjust previous spending for inflation
    """

    initial_rate: float = 0.05  # Starting withdrawal rate (5%)
    upper_guardrail: float = 0.06  # Cut spending if rate exceeds this
    lower_guardrail: float = 0.04  # Raise spending if rate falls below this
    cut_amount: float = 0.10  # Cut spending by 10% when hitting upper rail
    raise_amount: float = 0.10  # Raise spending by 10% when hitting lower rail
    inflation_rate: float = 0.025
    no_raise_in_down_year: bool = True  # Don't raise spending after negative returns

    _initial_spending: float = field(default=0.0, init=False, repr=False)

    @property
    def name(self) -> str:
        return "Guardrails"

    @property
    def description(self) -> str:
        return (
            f"Start at {self.initial_rate:.1%}, adjust for inflation, but cut by "
            f"{self.cut_amount:.0%} if rate > {self.upper_guardrail:.1%} or raise by "
            f"{self.raise_amount:.0%} if rate < {self.lower_guardrail:.1%}."
        )

    def get_initial_withdrawal(self, initial_wealth: float) -> float:
        """Calculate first year withdrawal."""
        self._initial_spending = initial_wealth * self.initial_rate
        return self._initial_spending

    def calculate_withdrawal(self, context: WithdrawalContext) -> WithdrawalDecision:
        """Calculate guardrails-adjusted withdrawal.

        Args:
            context: Current state including previous spending and market returns

        Returns:
            WithdrawalDecision with guardrail-adjusted amount
        """
        # Get previous spending (or calculate initial)
        if context.previous_spending is None or context.year == 0:
            if isinstance(context.current_wealth, np.ndarray):
                base_spending = np.full_like(
                    context.current_wealth,
                    context.initial_wealth * self.initial_rate,
                )
            else:
                base_spending = context.initial_wealth * self.initial_rate
        else:
            # Inflation-adjust previous spending
            base_spending = context.previous_spending * (1 + self.inflation_rate)

        # Calculate current withdrawal rate
        if isinstance(context.current_wealth, np.ndarray):
            current_rate = np.where(
                context.current_wealth > 0,
                base_spending / context.current_wealth,
                np.inf,
            )
        else:
            current_rate = (
                base_spending / context.current_wealth
                if context.current_wealth > 0
                else float("inf")
            )

        # Apply guardrails
        amount = base_spending

        if isinstance(current_rate, np.ndarray):
            # Vectorized guardrail logic
            # Cut spending if above upper guardrail
            above_upper = current_rate > self.upper_guardrail
            amount = np.where(above_upper, amount * (1 - self.cut_amount), amount)

            # Raise spending if below lower guardrail (unless down year rule)
            below_lower = current_rate < self.lower_guardrail
            if self.no_raise_in_down_year and context.market_return_ytd is not None:
                below_lower = below_lower & (context.market_return_ytd >= 0)
            amount = np.where(below_lower, amount * (1 + self.raise_amount), amount)

            is_ceiling_hit = below_lower  # Hit ceiling = spending was raised
            is_floor_breach = above_upper  # Hit floor = spending was cut
        else:
            is_floor_breach = False
            is_ceiling_hit = False

            if current_rate > self.upper_guardrail:
                amount = amount * (1 - self.cut_amount)
                is_floor_breach = True
            elif current_rate < self.lower_guardrail:
                can_raise = True
                if self.no_raise_in_down_year and context.market_return_ytd is not None:
                    can_raise = context.market_return_ytd >= 0
                if can_raise:
                    amount = amount * (1 + self.raise_amount)
                    is_ceiling_hit = True

        # Apply absolute floor/ceiling
        amount, floor_breach, ceiling_hit = self.apply_guardrails(
            amount, context.current_wealth
        )

        if isinstance(is_floor_breach, np.ndarray):
            is_floor_breach = is_floor_breach | floor_breach
            is_ceiling_hit = is_ceiling_hit | ceiling_hit
        else:
            is_floor_breach = is_floor_breach or floor_breach
            is_ceiling_hit = is_ceiling_hit or ceiling_hit

        return WithdrawalDecision(
            amount=amount,
            is_floor_breach=is_floor_breach,
            is_ceiling_hit=is_ceiling_hit,
            notes=f"Current rate: {np.mean(current_rate) if isinstance(current_rate, np.ndarray) else current_rate:.2%}",
        )
