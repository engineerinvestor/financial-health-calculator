"""Base classes for withdrawal strategies."""

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass
class WithdrawalContext:
    """Context information for making a withdrawal decision."""

    current_wealth: float | np.ndarray
    initial_wealth: float
    year: int
    age: int | None = None
    inflation_cumulative: float = 1.0  # Cumulative inflation since start
    previous_spending: float | np.ndarray | None = None
    market_return_ytd: float | None = None  # Year-to-date market return


@dataclass
class WithdrawalDecision:
    """Result of a withdrawal decision."""

    amount: float | np.ndarray
    is_floor_breach: bool | np.ndarray = False
    is_ceiling_hit: bool | np.ndarray = False
    notes: str = ""


class WithdrawalPolicy(Protocol):
    """Protocol defining the interface for withdrawal strategies."""

    @property
    def name(self) -> str:
        """Human-readable name for the strategy."""
        ...

    @property
    def description(self) -> str:
        """Brief description of how the strategy works."""
        ...

    def calculate_withdrawal(self, context: WithdrawalContext) -> WithdrawalDecision:
        """Calculate the withdrawal amount for the given context.

        Args:
            context: Current state information

        Returns:
            WithdrawalDecision with amount and metadata
        """
        ...

    def get_initial_withdrawal(self, initial_wealth: float) -> float:
        """Calculate the first year's withdrawal.

        Args:
            initial_wealth: Starting portfolio value

        Returns:
            First year withdrawal amount
        """
        ...


@dataclass
class BaseWithdrawalPolicy:
    """Base class with common functionality for withdrawal policies."""

    floor_spending: float | None = None
    ceiling_spending: float | None = None

    def apply_guardrails(
        self,
        amount: float | np.ndarray,
        wealth: float | np.ndarray,
    ) -> tuple[float | np.ndarray, bool | np.ndarray, bool | np.ndarray]:
        """Apply floor and ceiling guardrails to withdrawal amount.

        Args:
            amount: Proposed withdrawal amount
            wealth: Current wealth

        Returns:
            Tuple of (adjusted_amount, is_floor_breach, is_ceiling_hit)
        """
        is_floor_breach = False
        is_ceiling_hit = False

        # Apply floor
        if self.floor_spending is not None:
            if isinstance(amount, np.ndarray):
                is_floor_breach = amount < self.floor_spending
                amount = np.maximum(amount, self.floor_spending)
            else:
                is_floor_breach = amount < self.floor_spending
                amount = max(amount, self.floor_spending)

        # Apply ceiling
        if self.ceiling_spending is not None:
            if isinstance(amount, np.ndarray):
                is_ceiling_hit = amount > self.ceiling_spending
                amount = np.minimum(amount, self.ceiling_spending)
            else:
                is_ceiling_hit = amount > self.ceiling_spending
                amount = min(amount, self.ceiling_spending)

        # Can't withdraw more than we have
        if isinstance(amount, np.ndarray) or isinstance(wealth, np.ndarray):
            amount = np.minimum(amount, np.maximum(wealth, 0))
        else:
            amount = min(amount, max(wealth, 0))

        return amount, is_floor_breach, is_ceiling_hit
