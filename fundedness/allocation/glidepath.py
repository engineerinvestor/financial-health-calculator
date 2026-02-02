"""Glidepath allocation policies."""

from dataclasses import dataclass

import numpy as np


@dataclass
class AgeBasedGlidepathPolicy:
    """Traditional declining equity glidepath based on age.

    Classic approach: reduce equity allocation as you age to reduce
    sequence-of-returns risk.
    """

    initial_stock_weight: float = 0.7
    final_stock_weight: float = 0.3
    years_to_final: int = 30

    @property
    def name(self) -> str:
        return f"Glidepath ({self.initial_stock_weight:.0%} → {self.final_stock_weight:.0%})"

    def get_allocation(
        self,
        wealth: float | np.ndarray,
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
class RisingEquityGlidepathPolicy:
    """Rising equity glidepath (bonds-first approach).

    Start conservative, increase equity over time as sequence-of-returns
    risk decreases and remaining lifespan shortens.

    Based on research by Wade Pfau and Michael Kitces showing that
    rising equity glidepaths can improve outcomes in some scenarios.
    """

    initial_stock_weight: float = 0.3
    final_stock_weight: float = 0.7
    years_to_final: int = 20

    @property
    def name(self) -> str:
        return f"Rising Equity ({self.initial_stock_weight:.0%} → {self.final_stock_weight:.0%})"

    def get_allocation(
        self,
        wealth: float | np.ndarray,
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
class VShapedGlidepathPolicy:
    """V-shaped glidepath: reduce then increase equity.

    Start moderate, reduce equity in early retirement (highest sequence risk),
    then increase equity as the portfolio stabilizes and remaining horizon shortens.
    """

    initial_stock_weight: float = 0.5
    minimum_stock_weight: float = 0.3
    final_stock_weight: float = 0.6
    years_to_minimum: int = 10
    years_to_final: int = 30

    @property
    def name(self) -> str:
        return "V-Shaped Glidepath"

    def get_allocation(
        self,
        wealth: float | np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> float:
        """Calculate V-shaped stock allocation."""
        if year <= self.years_to_minimum:
            # Declining phase
            progress = year / self.years_to_minimum
            stock_weight = self.initial_stock_weight - progress * (
                self.initial_stock_weight - self.minimum_stock_weight
            )
        else:
            # Rising phase
            years_in_rising = year - self.years_to_minimum
            years_remaining = self.years_to_final - self.years_to_minimum
            progress = min(years_in_rising / years_remaining, 1.0)
            stock_weight = self.minimum_stock_weight + progress * (
                self.final_stock_weight - self.minimum_stock_weight
            )

        return stock_weight
