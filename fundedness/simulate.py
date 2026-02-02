"""Monte Carlo simulation engine for retirement projections."""

from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from fundedness.models.market import MarketModel
from fundedness.models.simulation import SimulationConfig


@dataclass
class SimulationResult:
    """Results from a Monte Carlo simulation."""

    # Core paths (shape: n_simulations x n_years)
    wealth_paths: np.ndarray
    spending_paths: np.ndarray | None = None

    # Time metrics (shape: n_simulations)
    time_to_ruin: np.ndarray | None = None
    time_to_floor_breach: np.ndarray | None = None

    # Percentile summaries (shape: n_percentiles x n_years)
    wealth_percentiles: dict[str, np.ndarray] = field(default_factory=dict)
    spending_percentiles: dict[str, np.ndarray] = field(default_factory=dict)

    # Aggregate metrics
    success_rate: float = 0.0  # % of paths that never hit ruin
    floor_breach_rate: float = 0.0  # % of paths that breach spending floor
    median_terminal_wealth: float = 0.0
    mean_terminal_wealth: float = 0.0

    # Utility metrics (for utility-integrated simulation)
    utility_paths: np.ndarray | None = None  # shape: n_simulations x n_years
    expected_lifetime_utility: float | None = None
    certainty_equivalent_consumption: float | None = None
    utility_percentiles: dict[str, np.ndarray] = field(default_factory=dict)

    # Configuration
    n_simulations: int = 0
    n_years: int = 0
    random_seed: int | None = None

    def get_survival_probability(self) -> np.ndarray:
        """Calculate survival probability at each year.

        Returns:
            Array of shape (n_years,) with P(not ruined) at each year
        """
        if self.time_to_ruin is None:
            return np.ones(self.n_years)

        survival = np.zeros(self.n_years)
        for year in range(self.n_years):
            survival[year] = np.mean(self.time_to_ruin > year)
        return survival

    def get_floor_survival_probability(self) -> np.ndarray:
        """Calculate probability of being above spending floor at each year.

        Returns:
            Array of shape (n_years,) with P(above floor) at each year
        """
        if self.time_to_floor_breach is None:
            return np.ones(self.n_years)

        survival = np.zeros(self.n_years)
        for year in range(self.n_years):
            survival[year] = np.mean(self.time_to_floor_breach > year)
        return survival

    def get_percentile(self, percentile: int, metric: str = "wealth") -> np.ndarray:
        """Get a specific percentile path.

        Args:
            percentile: Percentile value (0-100)
            metric: "wealth" or "spending"

        Returns:
            Array of shape (n_years,) with percentile values
        """
        key = f"P{percentile}"
        if metric == "wealth":
            return self.wealth_percentiles.get(key, np.zeros(self.n_years))
        else:
            return self.spending_percentiles.get(key, np.zeros(self.n_years))


def generate_returns(
    n_simulations: int,
    n_years: int,
    market_model: MarketModel,
    stock_weight: float,
    bond_weight: float | None = None,
    random_seed: int | None = None,
) -> np.ndarray:
    """Generate correlated portfolio returns.

    Args:
        n_simulations: Number of simulation paths
        n_years: Number of years to simulate
        market_model: Market assumptions
        stock_weight: Portfolio weight in stocks
        bond_weight: Portfolio weight in bonds (rest is cash if None)
        random_seed: Random seed for reproducibility

    Returns:
        Array of shape (n_simulations, n_years) with portfolio returns
    """
    rng = np.random.default_rng(random_seed)

    if bond_weight is None:
        bond_weight = 1 - stock_weight
    cash_weight = max(0, 1 - stock_weight - bond_weight)

    # Portfolio expected return and volatility
    portfolio_return = market_model.expected_portfolio_return(stock_weight, bond_weight)
    portfolio_vol = market_model.portfolio_volatility(stock_weight, bond_weight)

    # Generate returns
    if market_model.use_fat_tails:
        # Use t-distribution for fatter tails
        z = stats.t.rvs(
            df=market_model.degrees_of_freedom,
            size=(n_simulations, n_years),
            random_state=rng,
        )
        # Scale t-distribution to have unit variance
        scale_factor = np.sqrt(market_model.degrees_of_freedom / (market_model.degrees_of_freedom - 2))
        z = z / scale_factor
    else:
        # Standard normal
        z = rng.standard_normal((n_simulations, n_years))

    # Convert to returns (log-normal model)
    # r = μ - σ²/2 + σ*z  (continuous compounding adjustment)
    returns = portfolio_return - portfolio_vol**2 / 2 + portfolio_vol * z

    return returns


def run_simulation(
    initial_wealth: float,
    annual_spending: float | np.ndarray,
    config: SimulationConfig,
    stock_weight: float | np.ndarray = 0.6,
    spending_floor: float | None = None,
    inflation_rate: float = 0.025,
) -> SimulationResult:
    """Run Monte Carlo simulation of retirement portfolio.

    Args:
        initial_wealth: Starting portfolio value
        annual_spending: Annual spending (constant or array by year)
        config: Simulation configuration
        stock_weight: Allocation to stocks (constant or array by year)
        spending_floor: Minimum acceptable spending (for floor breach tracking)
        inflation_rate: Annual inflation rate for real spending

    Returns:
        SimulationResult with all paths and metrics
    """
    n_sim = config.n_simulations
    n_years = config.n_years
    seed = config.random_seed

    # Handle spending as array
    if isinstance(annual_spending, (int, float)):
        spending_schedule = np.full(n_years, annual_spending)
    else:
        spending_schedule = np.array(annual_spending)[:n_years]
        if len(spending_schedule) < n_years:
            # Extend with last value
            spending_schedule = np.pad(
                spending_schedule,
                (0, n_years - len(spending_schedule)),
                mode="edge",
            )

    # Handle stock weight as array
    if isinstance(stock_weight, (int, float)):
        stock_weights = np.full(n_years, stock_weight)
    else:
        stock_weights = np.array(stock_weight)[:n_years]
        if len(stock_weights) < n_years:
            stock_weights = np.pad(
                stock_weights,
                (0, n_years - len(stock_weights)),
                mode="edge",
            )

    # Generate returns for each year's allocation
    # For simplicity, use average allocation for return generation
    avg_stock_weight = np.mean(stock_weights)
    returns = generate_returns(
        n_simulations=n_sim,
        n_years=n_years,
        market_model=config.market_model,
        stock_weight=avg_stock_weight,
        random_seed=seed,
    )

    # Initialize paths
    wealth_paths = np.zeros((n_sim, n_years + 1))
    wealth_paths[:, 0] = initial_wealth

    spending_paths = np.zeros((n_sim, n_years)) if config.track_spending else None

    time_to_ruin = np.full(n_sim, np.inf)
    time_to_floor_breach = np.full(n_sim, np.inf) if spending_floor else None

    # Simulate year by year
    for year in range(n_years):
        # Current wealth
        current_wealth = wealth_paths[:, year]

        # Spending (adjusted for inflation)
        real_spending = spending_schedule[year]
        nominal_spending = real_spending * (1 + inflation_rate) ** year

        # Actual spending (can't spend more than we have)
        actual_spending = np.minimum(nominal_spending, np.maximum(current_wealth, 0))

        if spending_paths is not None:
            spending_paths[:, year] = actual_spending

        # Track floor breach
        if time_to_floor_breach is not None and spending_floor:
            floor_breach_mask = (actual_spending < spending_floor * (1 + inflation_rate) ** year)
            floor_breach_mask &= np.isinf(time_to_floor_breach)
            time_to_floor_breach[floor_breach_mask] = year

        # Wealth after spending
        wealth_after_spending = current_wealth - actual_spending

        # Apply returns (only on positive wealth)
        wealth_with_returns = wealth_after_spending * (1 + returns[:, year])
        wealth_with_returns = np.maximum(wealth_with_returns, 0)  # Can't go negative

        wealth_paths[:, year + 1] = wealth_with_returns

        # Track ruin (wealth hits zero)
        ruin_mask = (wealth_paths[:, year + 1] <= 0) & np.isinf(time_to_ruin)
        time_to_ruin[ruin_mask] = year + 1

    # Calculate percentiles
    wealth_percentiles = {}
    spending_percentiles = {}

    for p in config.percentiles:
        key = f"P{p}"
        wealth_percentiles[key] = np.percentile(wealth_paths[:, 1:], p, axis=0)
        if spending_paths is not None:
            spending_percentiles[key] = np.percentile(spending_paths, p, axis=0)

    # Aggregate metrics
    terminal_wealth = wealth_paths[:, -1]
    success_rate = np.mean(np.isinf(time_to_ruin))
    floor_breach_rate = 0.0
    if time_to_floor_breach is not None:
        floor_breach_rate = np.mean(~np.isinf(time_to_floor_breach))

    return SimulationResult(
        wealth_paths=wealth_paths[:, 1:],  # Exclude initial wealth
        spending_paths=spending_paths,
        time_to_ruin=time_to_ruin,
        time_to_floor_breach=time_to_floor_breach,
        wealth_percentiles=wealth_percentiles,
        spending_percentiles=spending_percentiles,
        success_rate=success_rate,
        floor_breach_rate=floor_breach_rate,
        median_terminal_wealth=np.median(terminal_wealth),
        mean_terminal_wealth=np.mean(terminal_wealth),
        n_simulations=n_sim,
        n_years=n_years,
        random_seed=seed,
    )


def run_simulation_with_policy(
    initial_wealth: float,
    spending_policy: "SpendingPolicy",
    allocation_policy: "AllocationPolicy",
    config: SimulationConfig,
    spending_floor: float | None = None,
) -> SimulationResult:
    """Run simulation with dynamic spending and allocation policies.

    Args:
        initial_wealth: Starting portfolio value
        spending_policy: Policy determining annual spending
        allocation_policy: Policy determining asset allocation
        config: Simulation configuration
        spending_floor: Minimum acceptable spending

    Returns:
        SimulationResult with all paths and metrics
    """
    n_sim = config.n_simulations
    n_years = config.n_years
    seed = config.random_seed

    rng = np.random.default_rng(seed)

    # Initialize paths
    wealth_paths = np.zeros((n_sim, n_years + 1))
    wealth_paths[:, 0] = initial_wealth
    spending_paths = np.zeros((n_sim, n_years))

    time_to_ruin = np.full(n_sim, np.inf)
    time_to_floor_breach = np.full(n_sim, np.inf) if spending_floor else None

    # Generate all random draws upfront
    z = rng.standard_normal((n_sim, n_years))

    # Simulate year by year
    for year in range(n_years):
        current_wealth = wealth_paths[:, year]

        # Get spending from policy (vectorized)
        spending = spending_policy.get_spending(
            wealth=current_wealth,
            year=year,
            initial_wealth=initial_wealth,
        )
        spending_paths[:, year] = spending

        # Track floor breach
        if time_to_floor_breach is not None and spending_floor:
            floor_breach_mask = (spending < spending_floor) & np.isinf(time_to_floor_breach)
            time_to_floor_breach[floor_breach_mask] = year

        # Get allocation from policy
        stock_weight = allocation_policy.get_allocation(
            wealth=current_wealth,
            year=year,
            initial_wealth=initial_wealth,
        )

        # Calculate returns for this allocation
        # Handle both scalar and array allocations
        if isinstance(stock_weight, np.ndarray):
            # Array allocation: compute returns inline for each path
            bond_weight = 1 - stock_weight
            portfolio_return = (
                stock_weight * config.market_model.stock_return
                + bond_weight * config.market_model.bond_return
            )
            portfolio_vol = np.sqrt(
                stock_weight**2 * config.market_model.stock_volatility**2
                + bond_weight**2 * config.market_model.bond_volatility**2
                + 2 * stock_weight * bond_weight
                * config.market_model.stock_volatility
                * config.market_model.bond_volatility
                * config.market_model.stock_bond_correlation
            )
        else:
            # Scalar allocation: use market model methods
            portfolio_return = config.market_model.expected_portfolio_return(stock_weight)
            portfolio_vol = config.market_model.portfolio_volatility(stock_weight)

        returns = portfolio_return - portfolio_vol**2 / 2 + portfolio_vol * z[:, year]

        # Update wealth
        wealth_after_spending = np.maximum(current_wealth - spending, 0)
        wealth_paths[:, year + 1] = wealth_after_spending * (1 + returns)

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


# Type hints for policies (avoid circular imports)
class SpendingPolicy:
    """Protocol for spending policies."""

    def get_spending(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> np.ndarray:
        """Get spending amount for each simulation path."""
        raise NotImplementedError


class AllocationPolicy:
    """Protocol for allocation policies."""

    def get_allocation(
        self,
        wealth: np.ndarray,
        year: int,
        initial_wealth: float,
    ) -> float | np.ndarray:
        """Get stock allocation (can be constant or per-path)."""
        raise NotImplementedError


def run_simulation_with_utility(
    initial_wealth: float,
    spending_policy: "SpendingPolicy",
    allocation_policy: "AllocationPolicy",
    config: SimulationConfig,
    utility_model: "UtilityModel",
    spending_floor: float | None = None,
    survival_probabilities: np.ndarray | None = None,
) -> SimulationResult:
    """Run simulation tracking lifetime utility.

    This function extends run_simulation_with_policy to also track utility
    at each time step, calculate expected lifetime utility, and compute
    the certainty equivalent consumption.

    Args:
        initial_wealth: Starting portfolio value
        spending_policy: Policy determining annual spending
        allocation_policy: Policy determining asset allocation
        config: Simulation configuration
        utility_model: Utility model for calculating period utility
        spending_floor: Minimum acceptable spending
        survival_probabilities: P(alive) at each year (optional)

    Returns:
        SimulationResult with utility metrics populated
    """
    # Import here to avoid circular imports
    from fundedness.models.utility import UtilityModel

    n_sim = config.n_simulations
    n_years = config.n_years
    seed = config.random_seed

    rng = np.random.default_rng(seed)

    # Initialize paths
    wealth_paths = np.zeros((n_sim, n_years + 1))
    wealth_paths[:, 0] = initial_wealth
    spending_paths = np.zeros((n_sim, n_years))
    utility_paths = np.zeros((n_sim, n_years))

    time_to_ruin = np.full(n_sim, np.inf)
    time_to_floor_breach = np.full(n_sim, np.inf) if spending_floor else None

    # Default survival probabilities (all survive)
    if survival_probabilities is None:
        survival_probabilities = np.ones(n_years)

    # Generate all random draws upfront
    z = rng.standard_normal((n_sim, n_years))

    # Simulate year by year
    for year in range(n_years):
        current_wealth = wealth_paths[:, year]

        # Get spending from policy
        spending = spending_policy.get_spending(
            wealth=current_wealth,
            year=year,
            initial_wealth=initial_wealth,
        )
        spending_paths[:, year] = spending

        # Calculate utility for this period's consumption
        for i in range(n_sim):
            utility_paths[i, year] = utility_model.utility(spending[i])

        # Track floor breach
        if time_to_floor_breach is not None and spending_floor:
            floor_breach_mask = (spending < spending_floor) & np.isinf(time_to_floor_breach)
            time_to_floor_breach[floor_breach_mask] = year

        # Get allocation from policy
        stock_weight = allocation_policy.get_allocation(
            wealth=current_wealth,
            year=year,
            initial_wealth=initial_wealth,
        )

        # Calculate returns for this allocation
        # Handle both scalar and array allocations
        if isinstance(stock_weight, np.ndarray):
            # Array allocation: compute returns inline for each path
            bond_weight = 1 - stock_weight
            portfolio_return = (
                stock_weight * config.market_model.stock_return
                + bond_weight * config.market_model.bond_return
            )
            portfolio_vol = np.sqrt(
                stock_weight**2 * config.market_model.stock_volatility**2
                + bond_weight**2 * config.market_model.bond_volatility**2
                + 2 * stock_weight * bond_weight
                * config.market_model.stock_volatility
                * config.market_model.bond_volatility
                * config.market_model.stock_bond_correlation
            )
        else:
            # Scalar allocation: use market model methods
            portfolio_return = config.market_model.expected_portfolio_return(stock_weight)
            portfolio_vol = config.market_model.portfolio_volatility(stock_weight)

        returns = portfolio_return - portfolio_vol**2 / 2 + portfolio_vol * z[:, year]

        # Update wealth
        wealth_after_spending = np.maximum(current_wealth - spending, 0)
        wealth_paths[:, year + 1] = wealth_after_spending * (1 + returns)

        # Track ruin
        ruin_mask = (wealth_paths[:, year + 1] <= 0) & np.isinf(time_to_ruin)
        time_to_ruin[ruin_mask] = year + 1

    # Calculate discounted lifetime utility for each path
    discount_factors = np.array([
        (1 + utility_model.time_preference) ** (-t) * survival_probabilities[t]
        for t in range(n_years)
    ])

    # Lifetime utility per path
    discounted_utilities = utility_paths * discount_factors
    lifetime_utilities = np.sum(discounted_utilities, axis=1)

    # Expected lifetime utility (mean across paths)
    expected_lifetime_utility = np.mean(lifetime_utilities)

    # Certainty equivalent consumption
    # Find the constant consumption that gives same expected utility
    mean_spending = np.mean(spending_paths)
    ce_consumption = utility_model.certainty_equivalent(
        np.mean(spending_paths, axis=1)  # Average spending per path
    )

    # Calculate percentiles
    wealth_percentiles = {}
    spending_percentiles = {}
    utility_percentiles = {}

    for p in config.percentiles:
        key = f"P{p}"
        wealth_percentiles[key] = np.percentile(wealth_paths[:, 1:], p, axis=0)
        spending_percentiles[key] = np.percentile(spending_paths, p, axis=0)
        utility_percentiles[key] = np.percentile(utility_paths, p, axis=0)

    terminal_wealth = wealth_paths[:, -1]

    return SimulationResult(
        wealth_paths=wealth_paths[:, 1:],
        spending_paths=spending_paths,
        utility_paths=utility_paths,
        time_to_ruin=time_to_ruin,
        time_to_floor_breach=time_to_floor_breach,
        wealth_percentiles=wealth_percentiles,
        spending_percentiles=spending_percentiles,
        utility_percentiles=utility_percentiles,
        success_rate=np.mean(np.isinf(time_to_ruin)),
        floor_breach_rate=np.mean(~np.isinf(time_to_floor_breach)) if time_to_floor_breach is not None else 0.0,
        median_terminal_wealth=np.median(terminal_wealth),
        mean_terminal_wealth=np.mean(terminal_wealth),
        expected_lifetime_utility=expected_lifetime_utility,
        certainty_equivalent_consumption=ce_consumption,
        n_simulations=n_sim,
        n_years=n_years,
        random_seed=seed,
    )


# Type alias for UtilityModel (to avoid import issues)
UtilityModel = "UtilityModel"
