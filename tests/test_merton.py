"""Tests for Merton optimal formulas."""

import numpy as np
import pytest

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
from fundedness.models.market import MarketModel
from fundedness.models.utility import UtilityModel


@pytest.fixture
def market_model() -> MarketModel:
    """Standard market model for testing."""
    return MarketModel(
        stock_return=0.05,
        bond_return=0.015,
        stock_volatility=0.16,
    )


@pytest.fixture
def utility_model() -> UtilityModel:
    """Standard utility model for testing."""
    return UtilityModel(
        gamma=3.0,
        subsistence_floor=30000,
        time_preference=0.02,
    )


class TestMertonOptimalAllocation:
    """Tests for merton_optimal_allocation function."""

    def test_basic_calculation(self, market_model, utility_model):
        """Test basic Merton allocation formula."""
        k_star = merton_optimal_allocation(market_model, utility_model)

        # k* = (mu - r) / (gamma * sigma^2)
        # k* = (0.05 - 0.015) / (3 * 0.16^2)
        # k* = 0.035 / (3 * 0.0256) = 0.035 / 0.0768 = 0.456
        expected = (0.05 - 0.015) / (3 * 0.16**2)
        assert abs(k_star - expected) < 0.001

    def test_higher_risk_aversion_lower_allocation(self, market_model):
        """Higher gamma should result in lower allocation."""
        low_gamma = UtilityModel(gamma=2.0)
        high_gamma = UtilityModel(gamma=5.0)

        k_low = merton_optimal_allocation(market_model, low_gamma)
        k_high = merton_optimal_allocation(market_model, high_gamma)

        assert k_low > k_high

    def test_higher_risk_premium_higher_allocation(self, utility_model):
        """Higher risk premium should increase allocation."""
        low_premium = MarketModel(stock_return=0.04, bond_return=0.02)
        high_premium = MarketModel(stock_return=0.08, bond_return=0.02)

        k_low = merton_optimal_allocation(low_premium, utility_model)
        k_high = merton_optimal_allocation(high_premium, utility_model)

        assert k_high > k_low

    def test_higher_volatility_lower_allocation(self, utility_model):
        """Higher volatility should reduce allocation."""
        low_vol = MarketModel(stock_volatility=0.12)
        high_vol = MarketModel(stock_volatility=0.20)

        k_low = merton_optimal_allocation(low_vol, utility_model)
        k_high = merton_optimal_allocation(high_vol, utility_model)

        assert k_low > k_high

    def test_zero_volatility_returns_zero(self, utility_model):
        """Zero volatility should return zero allocation (edge case)."""
        zero_vol = MarketModel(stock_volatility=0.0)
        k = merton_optimal_allocation(zero_vol, utility_model)
        assert k == 0.0

    def test_can_exceed_100_percent(self, utility_model):
        """With high risk premium, optimal can exceed 100%."""
        high_premium = MarketModel(
            stock_return=0.10,
            bond_return=0.01,
            stock_volatility=0.10,
        )
        low_gamma = UtilityModel(gamma=1.5)

        k = merton_optimal_allocation(high_premium, low_gamma)
        assert k > 1.0  # Leveraged position


class TestCertaintyEquivalentReturn:
    """Tests for certainty_equivalent_return function."""

    def test_basic_calculation(self, market_model, utility_model):
        """Test CE return formula."""
        rce = certainty_equivalent_return(market_model, utility_model)

        # Should be positive with typical parameters
        assert rce > 0

        # CE return should be between bond and stock return
        assert rce >= market_model.bond_return
        assert rce <= market_model.stock_return

    def test_ce_at_optimal_allocation(self, market_model, utility_model):
        """CE return is maximized at optimal allocation."""
        k_star = merton_optimal_allocation(market_model, utility_model)
        rce_optimal = certainty_equivalent_return(market_model, utility_model, k_star)

        # Try allocations around optimal
        rce_below = certainty_equivalent_return(market_model, utility_model, k_star * 0.5)
        rce_above = certainty_equivalent_return(market_model, utility_model, k_star * 1.5)

        assert rce_optimal >= rce_below
        assert rce_optimal >= rce_above

    def test_zero_allocation_equals_bond_return(self, market_model, utility_model):
        """Zero allocation should give bond return."""
        rce = certainty_equivalent_return(market_model, utility_model, 0.0)
        assert abs(rce - market_model.bond_return) < 0.001


class TestMertonOptimalSpendingRate:
    """Tests for merton_optimal_spending_rate function."""

    def test_basic_calculation(self, market_model, utility_model):
        """Test spending rate calculation."""
        rate = merton_optimal_spending_rate(market_model, utility_model)

        # Should be reasonable (1-10%)
        assert 0.01 <= rate <= 0.10

    def test_finite_horizon_increases_rate(self, market_model, utility_model):
        """Shorter horizon should increase spending rate."""
        infinite_rate = merton_optimal_spending_rate(market_model, utility_model)
        finite_rate = merton_optimal_spending_rate(market_model, utility_model, 20)

        assert finite_rate >= infinite_rate

    def test_shorter_horizon_higher_rate(self, market_model, utility_model):
        """Shorter horizon = higher spending rate."""
        rate_30y = merton_optimal_spending_rate(market_model, utility_model, 30)
        rate_10y = merton_optimal_spending_rate(market_model, utility_model, 10)

        assert rate_10y > rate_30y

    def test_never_negative(self, market_model, utility_model):
        """Spending rate should never be negative."""
        # Try various parameter combinations
        for gamma in [1.0, 2.0, 5.0]:
            for rtp in [0.0, 0.02, 0.05]:
                um = UtilityModel(gamma=gamma, time_preference=rtp)
                rate = merton_optimal_spending_rate(market_model, um)
                assert rate >= 0


class TestWealthAdjustedAllocation:
    """Tests for wealth_adjusted_optimal_allocation function."""

    def test_below_floor_returns_min(self, market_model, utility_model):
        """Wealth below floor should return minimum allocation."""
        k = wealth_adjusted_optimal_allocation(
            wealth=20000,  # Below $30k floor
            market_model=market_model,
            utility_model=utility_model,
        )
        assert k == 0.0

    def test_at_floor_returns_min(self, market_model, utility_model):
        """Wealth at floor should return minimum allocation."""
        k = wealth_adjusted_optimal_allocation(
            wealth=30000,  # At floor
            market_model=market_model,
            utility_model=utility_model,
        )
        assert k == 0.0

    def test_high_wealth_approaches_optimal(self, market_model, utility_model):
        """Very high wealth should approach unconstrained optimal."""
        k_star = merton_optimal_allocation(market_model, utility_model)
        k_adjusted = wealth_adjusted_optimal_allocation(
            wealth=10_000_000,  # Very high wealth
            market_model=market_model,
            utility_model=utility_model,
        )

        # Should be close to k_star (within 1%)
        assert abs(k_adjusted - k_star) / k_star < 0.01

    def test_monotonically_increasing(self, market_model, utility_model):
        """Allocation should increase monotonically with wealth."""
        floor = utility_model.subsistence_floor
        wealth_levels = [floor + 10000 * i for i in range(1, 20)]

        allocations = [
            wealth_adjusted_optimal_allocation(w, market_model, utility_model)
            for w in wealth_levels
        ]

        for i in range(len(allocations) - 1):
            assert allocations[i] <= allocations[i + 1]

    def test_respects_bounds(self, market_model, utility_model):
        """Should respect min/max allocation bounds."""
        k = wealth_adjusted_optimal_allocation(
            wealth=1_000_000,
            market_model=market_model,
            utility_model=utility_model,
            min_allocation=0.2,
            max_allocation=0.8,
        )
        assert 0.2 <= k <= 0.8


class TestCalculateMertonOptimal:
    """Tests for calculate_merton_optimal function."""

    def test_returns_complete_result(self, market_model, utility_model):
        """Should return all expected fields."""
        result = calculate_merton_optimal(
            wealth=1_000_000,
            market_model=market_model,
            utility_model=utility_model,
        )

        assert isinstance(result, MertonOptimalResult)
        assert result.optimal_equity_allocation > 0
        assert result.certainty_equivalent_return > 0
        assert result.optimal_spending_rate > 0
        assert result.wealth_adjusted_allocation > 0
        assert result.risk_premium > 0
        assert result.portfolio_volatility > 0

    def test_with_finite_horizon(self, market_model, utility_model):
        """Should handle finite horizon."""
        result = calculate_merton_optimal(
            wealth=1_000_000,
            market_model=market_model,
            utility_model=utility_model,
            remaining_years=25,
        )

        assert result.optimal_spending_rate > 0


class TestOptimalSpendingByAge:
    """Tests for optimal_spending_by_age function."""

    def test_returns_dict_for_all_ages(self, market_model, utility_model):
        """Should return rates for all ages in range."""
        rates = optimal_spending_by_age(
            market_model=market_model,
            utility_model=utility_model,
            starting_age=65,
            end_age=95,
        )

        assert len(rates) == 31  # 65 to 95 inclusive
        assert 65 in rates
        assert 95 in rates

    def test_increases_with_age(self, market_model, utility_model):
        """Spending rate should increase with age."""
        rates = optimal_spending_by_age(
            market_model=market_model,
            utility_model=utility_model,
            starting_age=65,
            end_age=95,
        )

        # General trend should be increasing
        assert rates[65] < rates[85]
        assert rates[85] < rates[95]


class TestOptimalAllocationByWealth:
    """Tests for optimal_allocation_by_wealth function."""

    def test_returns_array(self, market_model, utility_model):
        """Should return array of same size as input."""
        wealth_levels = np.linspace(50000, 2000000, 20)
        allocations = optimal_allocation_by_wealth(
            market_model=market_model,
            utility_model=utility_model,
            wealth_levels=wealth_levels,
        )

        assert allocations.shape == wealth_levels.shape

    def test_monotonically_increasing(self, market_model, utility_model):
        """Allocations should increase monotonically."""
        wealth_levels = np.linspace(50000, 2000000, 50)
        allocations = optimal_allocation_by_wealth(
            market_model=market_model,
            utility_model=utility_model,
            wealth_levels=wealth_levels,
        )

        diffs = np.diff(allocations)
        assert np.all(diffs >= -1e-10)  # Allow tiny numerical errors
