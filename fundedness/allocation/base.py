"""Base class for allocation policies."""

from typing import Protocol

import numpy as np


class AllocationPolicy(Protocol):
    """Protocol defining the interface for allocation strategies."""

    @property
    def name(self) -> str:
        """Human-readable name for the strategy."""
        ...

    def get_allocation(
        self,
        wealth: float | np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> float | np.ndarray:
        """Get the stock allocation for the given context.

        Args:
            wealth: Current portfolio value(s)
            year: Current year in simulation
            initial_wealth: Starting portfolio value

        Returns:
            Stock allocation as decimal (0-1)
        """
        ...
