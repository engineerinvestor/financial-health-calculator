"""Fundedness: A Python financial planning toolkit.

This package provides tools for:
- CEFR (Certainty-Equivalent Funded Ratio) calculations
- Monte Carlo retirement simulations
- Withdrawal strategy comparison
- Utility-optimal spending and allocation (Merton framework)
- Beautiful Plotly visualizations
"""

__version__ = "0.2.2"

from fundedness.cefr import CEFRResult, compute_cefr
from fundedness.merton import (
    MertonOptimalResult,
    calculate_merton_optimal,
    certainty_equivalent_return,
    merton_optimal_allocation,
    merton_optimal_spending_rate,
    optimal_allocation_by_wealth,
    optimal_spending_by_age,
    wealth_adjusted_optimal_allocation,
)
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
from fundedness.simulate import (
    SimulationResult,
    run_simulation,
    run_simulation_with_policy,
    run_simulation_with_utility,
)

__all__ = [
    "__version__",
    # CEFR
    "compute_cefr",
    "CEFRResult",
    # Merton optimal
    "calculate_merton_optimal",
    "certainty_equivalent_return",
    "merton_optimal_allocation",
    "merton_optimal_spending_rate",
    "MertonOptimalResult",
    "optimal_allocation_by_wealth",
    "optimal_spending_by_age",
    "wealth_adjusted_optimal_allocation",
    # Simulation
    "run_simulation",
    "run_simulation_with_policy",
    "run_simulation_with_utility",
    "SimulationResult",
    # Models
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
