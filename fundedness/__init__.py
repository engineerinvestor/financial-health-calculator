"""Fundedness: A Python financial planning toolkit.

This package provides tools for:
- CEFR (Certainty-Equivalent Funded Ratio) calculations
- Monte Carlo retirement simulations
- Withdrawal strategy comparison
- Beautiful Plotly visualizations
"""

__version__ = "0.1.0"

from fundedness.cefr import CEFRResult, compute_cefr
from fundedness.models import (
    Asset,
    BalanceSheet,
    Household,
    Liability,
    MarketModel,
    Person,
    SimulationConfig,
    TaxModel,
    UtilityModel,
)

__all__ = [
    "__version__",
    "compute_cefr",
    "CEFRResult",
    "Asset",
    "BalanceSheet",
    "Household",
    "Liability",
    "MarketModel",
    "Person",
    "SimulationConfig",
    "TaxModel",
    "UtilityModel",
]
