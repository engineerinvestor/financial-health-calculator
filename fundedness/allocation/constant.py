"""Constant allocation policy."""

from dataclasses import dataclass

import numpy as np


@dataclass
class ConstantAllocationPolicy:
    """Maintain a constant stock/bond allocation."""

    stock_weight: float = 0.6

    @property
    def name(self) -> str:
        return f"{self.stock_weight:.0%} Stocks"

    def get_allocation(
        self,
        wealth: float | np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> float:
        """Return constant stock allocation."""
        return self.stock_weight
