"""Withdrawal strategy comparison framework."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from fundedness.models.simulation import SimulationConfig
from fundedness.simulate import SimulationResult, generate_returns
from fundedness.withdrawals.base import WithdrawalContext, WithdrawalPolicy


@dataclass
class StrategyComparisonResult:
    """Results from comparing multiple withdrawal strategies."""

    strategy_names: list[str]
    results: dict[str, SimulationResult]
    metrics: dict[str, dict[str, Any]]

    def get_summary_table(self) -> dict[str, list]:
        """Get a summary table of key metrics across strategies."""
        return {
            "Strategy": self.strategy_names,
            "Success Rate": [
                self.metrics[name]["success_rate"] for name in self.strategy_names
            ],
            "Median Terminal Wealth": [
                self.metrics[name]["median_terminal_wealth"] for name in self.strategy_names
            ],
            "Median Spending (Year 1)": [
                self.metrics[name]["median_initial_spending"] for name in self.strategy_names
            ],
            "Spending Volatility": [
                self.metrics[name]["spending_volatility"] for name in self.strategy_names
            ],
            "Floor Breach Rate": [
                self.metrics[name]["floor_breach_rate"] for name in self.strategy_names
            ],
        }


def run_strategy_simulation(
    policy: WithdrawalPolicy,
    initial_wealth: float,
    config: SimulationConfig,
    stock_weight: float = 0.6,
    starting_age: int = 65,
    spending_floor: float | None = None,
) -> SimulationResult:
    """Run a Monte Carlo simulation with a specific withdrawal strategy.

    Args:
        policy: Withdrawal policy to use
        initial_wealth: Starting portfolio value
        config: Simulation configuration
        stock_weight: Asset allocation to stocks
        starting_age: Starting age for age-based strategies
        spending_floor: Minimum acceptable spending

    Returns:
        SimulationResult with paths and metrics
    """
    n_sim = config.n_simulations
    n_years = config.n_years
    seed = config.random_seed

    # Generate returns
    returns = generate_returns(
        n_simulations=n_sim,
        n_years=n_years,
        market_model=config.market_model,
        stock_weight=stock_weight,
        random_seed=seed,
    )

    # Initialize paths
    wealth_paths = np.zeros((n_sim, n_years + 1))
    wealth_paths[:, 0] = initial_wealth
    spending_paths = np.zeros((n_sim, n_years))

    time_to_ruin = np.full(n_sim, np.inf)
    time_to_floor_breach = np.full(n_sim, np.inf) if spending_floor else None

    previous_spending = None

    # Simulate year by year
    for year in range(n_years):
        current_wealth = wealth_paths[:, year]

        # Create context
        context = WithdrawalContext(
            current_wealth=current_wealth,
            initial_wealth=initial_wealth,
            year=year,
            age=starting_age + year,
            previous_spending=previous_spending,
        )

        # Get withdrawal decision
        decision = policy.calculate_withdrawal(context)
        spending = decision.amount

        spending_paths[:, year] = spending
        previous_spending = spending

        # Track floor breach
        if time_to_floor_breach is not None and spending_floor:
            floor_breach_mask = (spending < spending_floor) & np.isinf(time_to_floor_breach)
            time_to_floor_breach[floor_breach_mask] = year

        # Update wealth
        wealth_after_spending = np.maximum(current_wealth - spending, 0)
        wealth_paths[:, year + 1] = wealth_after_spending * (1 + returns[:, year])

        # Track ruin
        ruin_mask = (wealth_paths[:, year + 1] <= 0) & np.isinf(time_to_ruin)
        time_to_ruin[ruin_mask] = year + 1

    # Calculate percentiles
    wealth_percentiles = {}
    spending_percentiles = {}

    for p in config.percentiles:
        key = f"P{p}"
        wealth_percentiles[key] = np.percentile(wealth_paths[:, 1:], p, axis=0)
        spending_percentiles[key] = np.percentile(spending_paths, p, axis=0)

    terminal_wealth = wealth_paths[:, -1]

    return SimulationResult(
        wealth_paths=wealth_paths[:, 1:],
        spending_paths=spending_paths,
        time_to_ruin=time_to_ruin,
        time_to_floor_breach=time_to_floor_breach,
        wealth_percentiles=wealth_percentiles,
        spending_percentiles=spending_percentiles,
        success_rate=np.mean(np.isinf(time_to_ruin)),
        floor_breach_rate=np.mean(~np.isinf(time_to_floor_breach)) if time_to_floor_breach is not None else 0.0,
        median_terminal_wealth=np.median(terminal_wealth),
        mean_terminal_wealth=np.mean(terminal_wealth),
        n_simulations=n_sim,
        n_years=n_years,
        random_seed=seed,
    )


def compare_strategies(
    policies: list[WithdrawalPolicy],
    initial_wealth: float,
    config: SimulationConfig,
    stock_weight: float = 0.6,
    starting_age: int = 65,
    spending_floor: float | None = None,
) -> StrategyComparisonResult:
    """Compare multiple withdrawal strategies using the same random draws.

    Args:
        policies: List of withdrawal policies to compare
        initial_wealth: Starting portfolio value
        config: Simulation configuration
        stock_weight: Asset allocation to stocks
        starting_age: Starting age for age-based strategies
        spending_floor: Minimum acceptable spending

    Returns:
        StrategyComparisonResult with all results and metrics
    """
    strategy_names = [p.name for p in policies]
    results = {}
    metrics = {}

    # Use same seed for all strategies for fair comparison
    base_seed = config.random_seed or 42

    for i, policy in enumerate(policies):
        # Use same seed for reproducibility
        config_copy = SimulationConfig(
            n_simulations=config.n_simulations,
            n_years=config.n_years,
            random_seed=base_seed,
            market_model=config.market_model,
            tax_model=config.tax_model,
            utility_model=config.utility_model,
            percentiles=config.percentiles,
        )

        result = run_strategy_simulation(
            policy=policy,
            initial_wealth=initial_wealth,
            config=config_copy,
            stock_weight=stock_weight,
            starting_age=starting_age,
            spending_floor=spending_floor,
        )

        results[policy.name] = result

        # Calculate additional metrics
        spending_paths = result.spending_paths
        if spending_paths is not None:
            # Spending volatility (coefficient of variation of spending changes)
            spending_changes = np.diff(spending_paths, axis=1) / spending_paths[:, :-1]
            spending_volatility = np.nanstd(spending_changes)

            # Median initial spending
            median_initial_spending = np.median(spending_paths[:, 0])

            # Average spending
            avg_spending = np.mean(spending_paths)
        else:
            spending_volatility = 0
            median_initial_spending = 0
            avg_spending = 0

        metrics[policy.name] = {
            "success_rate": result.success_rate,
            "floor_breach_rate": result.floor_breach_rate,
            "median_terminal_wealth": result.median_terminal_wealth,
            "mean_terminal_wealth": result.mean_terminal_wealth,
            "median_initial_spending": median_initial_spending,
            "average_spending": avg_spending,
            "spending_volatility": spending_volatility,
        }

    return StrategyComparisonResult(
        strategy_names=strategy_names,
        results=results,
        metrics=metrics,
    )
