"""Parametric policy optimization via Monte Carlo simulation.

This module provides tools for searching over policy parameters to find
configurations that maximize expected lifetime utility.
"""

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
from scipy import optimize

from fundedness.models.market import MarketModel
from fundedness.models.simulation import SimulationConfig
from fundedness.models.utility import UtilityModel
from fundedness.simulate import run_simulation_with_utility


@dataclass
class PolicyParameterSpec:
    """Specification for an optimizable policy parameter.

    Attributes:
        name: Parameter name (must match policy attribute)
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        initial_value: Starting value for optimization
        is_integer: Whether parameter should be rounded to integer
    """

    name: str
    min_value: float
    max_value: float
    initial_value: float | None = None
    is_integer: bool = False

    def get_initial(self) -> float:
        """Get initial value (midpoint if not specified)."""
        if self.initial_value is not None:
            return self.initial_value
        return (self.min_value + self.max_value) / 2

    def clip(self, value: float) -> float:
        """Clip value to bounds and optionally round."""
        clipped = max(self.min_value, min(self.max_value, value))
        if self.is_integer:
            return round(clipped)
        return clipped


@dataclass
class OptimizationResult:
    """Results from policy optimization.

    Attributes:
        optimal_params: Dictionary of optimal parameter values
        optimal_utility: Expected lifetime utility at optimum
        certainty_equivalent: Certainty equivalent consumption at optimum
        success_rate: Success rate at optimal parameters
        iterations: Number of optimization iterations
        convergence_history: Utility values during optimization
        final_simulation: Full simulation result at optimum
    """

    optimal_params: dict[str, float]
    optimal_utility: float
    certainty_equivalent: float
    success_rate: float
    iterations: int
    convergence_history: list[float] = field(default_factory=list)
    final_simulation: Any = None


def create_policy_with_params(
    policy_class: type,
    base_params: dict,
    param_specs: list[PolicyParameterSpec],
    param_values: np.ndarray,
) -> Any:
    """Create a policy instance with specified parameter values.

    Args:
        policy_class: Policy class to instantiate
        base_params: Fixed parameters for the policy
        param_specs: Specifications for optimizable parameters
        param_values: Current values for optimizable parameters

    Returns:
        Policy instance with combined parameters
    """
    params = dict(base_params)
    for spec, value in zip(param_specs, param_values):
        params[spec.name] = spec.clip(value)
    return policy_class(**params)


def optimize_spending_policy(
    policy_class: type,
    param_specs: list[PolicyParameterSpec],
    initial_wealth: float,
    allocation_policy: Any,
    config: SimulationConfig,
    utility_model: UtilityModel,
    base_params: dict | None = None,
    spending_floor: float | None = None,
    method: str = "nelder-mead",
    max_iterations: int = 50,
) -> OptimizationResult:
    """Optimize spending policy parameters to maximize utility.

    Uses scipy.optimize to search over policy parameters, evaluating
    each candidate via Monte Carlo simulation.

    Args:
        policy_class: Spending policy class to optimize
        param_specs: Parameters to optimize
        initial_wealth: Starting portfolio value
        allocation_policy: Fixed allocation policy to use
        config: Simulation configuration
        utility_model: Utility model for evaluation
        base_params: Fixed parameters for the policy
        spending_floor: Minimum spending floor
        method: Optimization method (nelder-mead, powell, etc.)
        max_iterations: Maximum optimization iterations

    Returns:
        OptimizationResult with optimal parameters and metrics
    """
    if base_params is None:
        base_params = {}

    convergence_history = []
    best_utility = -np.inf
    best_params = None
    best_result = None

    def objective(param_values: np.ndarray) -> float:
        """Negative utility (for minimization)."""
        nonlocal best_utility, best_params, best_result

        # Create policy with current parameters
        policy = create_policy_with_params(
            policy_class, base_params, param_specs, param_values
        )

        # Run simulation
        result = run_simulation_with_utility(
            initial_wealth=initial_wealth,
            spending_policy=policy,
            allocation_policy=allocation_policy,
            config=config,
            utility_model=utility_model,
            spending_floor=spending_floor,
        )

        utility = result.expected_lifetime_utility
        convergence_history.append(utility)

        # Track best
        if utility > best_utility:
            best_utility = utility
            best_params = {spec.name: spec.clip(v) for spec, v in zip(param_specs, param_values)}
            best_result = result

        return -utility  # Minimize negative utility

    # Initial values
    x0 = np.array([spec.get_initial() for spec in param_specs])

    # Bounds
    bounds = [(spec.min_value, spec.max_value) for spec in param_specs]

    # Run optimization
    if method.lower() in ("nelder-mead", "powell"):
        result = optimize.minimize(
            objective,
            x0,
            method=method,
            options={"maxiter": max_iterations, "disp": False},
        )
    else:
        result = optimize.minimize(
            objective,
            x0,
            method=method,
            bounds=bounds,
            options={"maxiter": max_iterations, "disp": False},
        )

    return OptimizationResult(
        optimal_params=best_params or {},
        optimal_utility=best_utility,
        certainty_equivalent=best_result.certainty_equivalent_consumption if best_result else 0.0,
        success_rate=best_result.success_rate if best_result else 0.0,
        iterations=result.nit if hasattr(result, "nit") else len(convergence_history),
        convergence_history=convergence_history,
        final_simulation=best_result,
    )


def optimize_allocation_policy(
    policy_class: type,
    param_specs: list[PolicyParameterSpec],
    initial_wealth: float,
    spending_policy: Any,
    config: SimulationConfig,
    utility_model: UtilityModel,
    base_params: dict | None = None,
    spending_floor: float | None = None,
    method: str = "nelder-mead",
    max_iterations: int = 50,
) -> OptimizationResult:
    """Optimize allocation policy parameters to maximize utility.

    Args:
        policy_class: Allocation policy class to optimize
        param_specs: Parameters to optimize
        initial_wealth: Starting portfolio value
        spending_policy: Fixed spending policy to use
        config: Simulation configuration
        utility_model: Utility model for evaluation
        base_params: Fixed parameters for the policy
        spending_floor: Minimum spending floor
        method: Optimization method
        max_iterations: Maximum iterations

    Returns:
        OptimizationResult with optimal parameters and metrics
    """
    if base_params is None:
        base_params = {}

    convergence_history = []
    best_utility = -np.inf
    best_params = None
    best_result = None

    def objective(param_values: np.ndarray) -> float:
        nonlocal best_utility, best_params, best_result

        policy = create_policy_with_params(
            policy_class, base_params, param_specs, param_values
        )

        result = run_simulation_with_utility(
            initial_wealth=initial_wealth,
            spending_policy=spending_policy,
            allocation_policy=policy,
            config=config,
            utility_model=utility_model,
            spending_floor=spending_floor,
        )

        utility = result.expected_lifetime_utility
        convergence_history.append(utility)

        if utility > best_utility:
            best_utility = utility
            best_params = {spec.name: spec.clip(v) for spec, v in zip(param_specs, param_values)}
            best_result = result

        return -utility

    x0 = np.array([spec.get_initial() for spec in param_specs])
    bounds = [(spec.min_value, spec.max_value) for spec in param_specs]

    if method.lower() in ("nelder-mead", "powell"):
        result = optimize.minimize(
            objective,
            x0,
            method=method,
            options={"maxiter": max_iterations, "disp": False},
        )
    else:
        result = optimize.minimize(
            objective,
            x0,
            method=method,
            bounds=bounds,
            options={"maxiter": max_iterations, "disp": False},
        )

    return OptimizationResult(
        optimal_params=best_params or {},
        optimal_utility=best_utility,
        certainty_equivalent=best_result.certainty_equivalent_consumption if best_result else 0.0,
        success_rate=best_result.success_rate if best_result else 0.0,
        iterations=result.nit if hasattr(result, "nit") else len(convergence_history),
        convergence_history=convergence_history,
        final_simulation=best_result,
    )


def optimize_combined_policy(
    spending_policy_class: type,
    allocation_policy_class: type,
    spending_param_specs: list[PolicyParameterSpec],
    allocation_param_specs: list[PolicyParameterSpec],
    initial_wealth: float,
    config: SimulationConfig,
    utility_model: UtilityModel,
    spending_base_params: dict | None = None,
    allocation_base_params: dict | None = None,
    spending_floor: float | None = None,
    method: str = "nelder-mead",
    max_iterations: int = 100,
) -> OptimizationResult:
    """Jointly optimize spending and allocation policy parameters.

    Args:
        spending_policy_class: Spending policy class
        allocation_policy_class: Allocation policy class
        spending_param_specs: Spending parameters to optimize
        allocation_param_specs: Allocation parameters to optimize
        initial_wealth: Starting portfolio value
        config: Simulation configuration
        utility_model: Utility model for evaluation
        spending_base_params: Fixed spending policy parameters
        allocation_base_params: Fixed allocation policy parameters
        spending_floor: Minimum spending floor
        method: Optimization method
        max_iterations: Maximum iterations

    Returns:
        OptimizationResult with optimal parameters for both policies
    """
    if spending_base_params is None:
        spending_base_params = {}
    if allocation_base_params is None:
        allocation_base_params = {}

    all_specs = spending_param_specs + allocation_param_specs
    n_spending = len(spending_param_specs)

    convergence_history = []
    best_utility = -np.inf
    best_params = None
    best_result = None

    def objective(param_values: np.ndarray) -> float:
        nonlocal best_utility, best_params, best_result

        spending_values = param_values[:n_spending]
        allocation_values = param_values[n_spending:]

        spending_policy = create_policy_with_params(
            spending_policy_class,
            spending_base_params,
            spending_param_specs,
            spending_values,
        )
        allocation_policy = create_policy_with_params(
            allocation_policy_class,
            allocation_base_params,
            allocation_param_specs,
            allocation_values,
        )

        result = run_simulation_with_utility(
            initial_wealth=initial_wealth,
            spending_policy=spending_policy,
            allocation_policy=allocation_policy,
            config=config,
            utility_model=utility_model,
            spending_floor=spending_floor,
        )

        utility = result.expected_lifetime_utility
        convergence_history.append(utility)

        if utility > best_utility:
            best_utility = utility
            best_params = {}
            for spec, v in zip(spending_param_specs, spending_values):
                best_params[f"spending_{spec.name}"] = spec.clip(v)
            for spec, v in zip(allocation_param_specs, allocation_values):
                best_params[f"allocation_{spec.name}"] = spec.clip(v)
            best_result = result

        return -utility

    x0 = np.array([spec.get_initial() for spec in all_specs])
    bounds = [(spec.min_value, spec.max_value) for spec in all_specs]

    if method.lower() in ("nelder-mead", "powell"):
        result = optimize.minimize(
            objective,
            x0,
            method=method,
            options={"maxiter": max_iterations, "disp": False},
        )
    else:
        result = optimize.minimize(
            objective,
            x0,
            method=method,
            bounds=bounds,
            options={"maxiter": max_iterations, "disp": False},
        )

    return OptimizationResult(
        optimal_params=best_params or {},
        optimal_utility=best_utility,
        certainty_equivalent=best_result.certainty_equivalent_consumption if best_result else 0.0,
        success_rate=best_result.success_rate if best_result else 0.0,
        iterations=result.nit if hasattr(result, "nit") else len(convergence_history),
        convergence_history=convergence_history,
        final_simulation=best_result,
    )


def grid_search_policy(
    policy_class: type,
    param_specs: list[PolicyParameterSpec],
    grid_points: int,
    evaluate_fn: Callable[[Any], float],
    base_params: dict | None = None,
) -> tuple[dict[str, float], float, np.ndarray]:
    """Exhaustive grid search over policy parameters.

    Useful for visualizing the utility surface or when the parameter
    space is small enough for exhaustive search.

    Args:
        policy_class: Policy class to optimize
        param_specs: Parameters to search over
        grid_points: Number of points per dimension
        evaluate_fn: Function that takes a policy and returns utility
        base_params: Fixed parameters for the policy

    Returns:
        Tuple of (best_params, best_utility, utility_grid)
    """
    if base_params is None:
        base_params = {}

    # Create grid
    grids = [
        np.linspace(spec.min_value, spec.max_value, grid_points)
        for spec in param_specs
    ]

    # Create meshgrid for all combinations
    mesh = np.meshgrid(*grids, indexing="ij")
    shape = mesh[0].shape

    utilities = np.zeros(shape)
    best_utility = -np.inf
    best_params = {}

    # Iterate over all grid points
    it = np.nditer(mesh[0], flags=["multi_index"])
    while not it.finished:
        idx = it.multi_index
        param_values = np.array([m[idx] for m in mesh])

        policy = create_policy_with_params(
            policy_class, base_params, param_specs, param_values
        )

        utility = evaluate_fn(policy)
        utilities[idx] = utility

        if utility > best_utility:
            best_utility = utility
            best_params = {
                spec.name: spec.clip(v)
                for spec, v in zip(param_specs, param_values)
            }

        it.iternext()

    return best_params, best_utility, utilities
