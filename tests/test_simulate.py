"""Tests for Monte Carlo simulation."""

import numpy as np
import pytest

from fundedness.models.market import MarketModel
from fundedness.models.simulation import SimulationConfig
from fundedness.simulate import SimulationResult, generate_returns, run_simulation


class TestReturnGeneration:
    """Tests for return generation."""

    def test_returns_shape(self, default_market_model):
        """Generated returns should have correct shape."""
        returns = generate_returns(
            n_simulations=100,
            n_years=30,
            market_model=default_market_model,
            stock_weight=0.6,
            random_seed=42,
        )

        assert returns.shape == (100, 30)

    def test_returns_reproducibility(self, default_market_model):
        """Same seed should produce same returns."""
        returns1 = generate_returns(
            n_simulations=50,
            n_years=20,
            market_model=default_market_model,
            stock_weight=0.6,
            random_seed=42,
        )
        returns2 = generate_returns(
            n_simulations=50,
            n_years=20,
            market_model=default_market_model,
            stock_weight=0.6,
            random_seed=42,
        )

        np.testing.assert_array_equal(returns1, returns2)

    def test_returns_statistics(self, default_market_model):
        """Generated returns should have reasonable statistics."""
        returns = generate_returns(
            n_simulations=10_000,
            n_years=30,
            market_model=default_market_model,
            stock_weight=0.6,
            random_seed=42,
        )

        # Mean should be close to expected portfolio return
        expected_return = default_market_model.expected_portfolio_return(0.6)
        actual_mean = np.mean(returns)

        # Allow for some variance
        assert abs(actual_mean - expected_return) < 0.01

    def test_fat_tails_option(self):
        """Fat tails option should increase extreme values."""
        normal_model = MarketModel(use_fat_tails=False)
        fat_tail_model = MarketModel(use_fat_tails=True, degrees_of_freedom=4)

        normal_returns = generate_returns(
            n_simulations=10_000,
            n_years=30,
            market_model=normal_model,
            stock_weight=0.6,
            random_seed=42,
        )
        fat_returns = generate_returns(
            n_simulations=10_000,
            n_years=30,
            market_model=fat_tail_model,
            stock_weight=0.6,
            random_seed=42,
        )

        # Fat tails should have more extreme values (higher kurtosis)
        normal_kurtosis = np.mean((normal_returns - normal_returns.mean()) ** 4) / (
            normal_returns.std() ** 4
        )
        fat_kurtosis = np.mean((fat_returns - fat_returns.mean()) ** 4) / (
            fat_returns.std() ** 4
        )

        # Fat tails should have higher kurtosis (normal is ~3)
        assert fat_kurtosis > normal_kurtosis


class TestSimulation:
    """Tests for run_simulation."""

    def test_simulation_result_structure(self, default_simulation_config):
        """Simulation should return correct result structure."""
        result = run_simulation(
            initial_wealth=1_000_000,
            annual_spending=40_000,
            config=default_simulation_config,
            stock_weight=0.6,
        )

        assert isinstance(result, SimulationResult)
        assert result.n_simulations == 100
        assert result.n_years == 30
        assert result.wealth_paths.shape == (100, 30)

    def test_simulation_reproducibility(self, default_market_model):
        """Same seed should produce same results."""
        config = SimulationConfig(
            n_simulations=100,
            n_years=20,
            random_seed=42,
            market_model=default_market_model,
        )

        result1 = run_simulation(
            initial_wealth=1_000_000,
            annual_spending=40_000,
            config=config,
            stock_weight=0.6,
        )
        result2 = run_simulation(
            initial_wealth=1_000_000,
            annual_spending=40_000,
            config=config,
            stock_weight=0.6,
        )

        np.testing.assert_array_equal(result1.wealth_paths, result2.wealth_paths)

    def test_wealth_decreases_with_spending(self, default_simulation_config):
        """Higher spending should lead to lower wealth."""
        result_low = run_simulation(
            initial_wealth=1_000_000,
            annual_spending=30_000,
            config=default_simulation_config,
            stock_weight=0.6,
        )
        result_high = run_simulation(
            initial_wealth=1_000_000,
            annual_spending=60_000,
            config=default_simulation_config,
            stock_weight=0.6,
        )

        assert result_low.median_terminal_wealth > result_high.median_terminal_wealth

    def test_success_rate_with_low_spending(self, default_simulation_config):
        """Very low spending should have high success rate."""
        result = run_simulation(
            initial_wealth=1_000_000,
            annual_spending=20_000,  # 2% withdrawal
            config=default_simulation_config,
            stock_weight=0.6,
        )

        # With 100 simulations there's variance; use 0.85 threshold
        assert result.success_rate >= 0.85

    def test_success_rate_with_high_spending(self, default_simulation_config):
        """Very high spending should have low success rate."""
        result = run_simulation(
            initial_wealth=1_000_000,
            annual_spending=100_000,  # 10% withdrawal
            config=default_simulation_config,
            stock_weight=0.6,
        )

        assert result.success_rate < 0.9

    def test_floor_breach_tracking(self, default_simulation_config):
        """Floor breach should be tracked correctly."""
        result = run_simulation(
            initial_wealth=1_000_000,
            annual_spending=50_000,
            config=default_simulation_config,
            stock_weight=0.6,
            spending_floor=40_000,
        )

        assert result.time_to_floor_breach is not None
        assert len(result.time_to_floor_breach) == 100

    def test_percentiles_calculated(self, default_simulation_config):
        """Percentiles should be calculated."""
        result = run_simulation(
            initial_wealth=1_000_000,
            annual_spending=40_000,
            config=default_simulation_config,
            stock_weight=0.6,
        )

        assert "P50" in result.wealth_percentiles
        assert len(result.wealth_percentiles["P50"]) == 30

    def test_survival_probability_decreasing(self, default_simulation_config):
        """Survival probability should decrease over time."""
        result = run_simulation(
            initial_wealth=1_000_000,
            annual_spending=50_000,
            config=default_simulation_config,
            stock_weight=0.6,
        )

        survival = result.get_survival_probability()

        # Should be weakly decreasing
        for i in range(1, len(survival)):
            assert survival[i] <= survival[i - 1] + 0.01  # Small tolerance


class TestSimulationPerformance:
    """Performance tests for simulation."""

    @pytest.mark.slow
    def test_large_simulation_performance(self, default_market_model):
        """Large simulation should complete in reasonable time."""
        import time

        config = SimulationConfig(
            n_simulations=10_000,
            n_years=60,
            random_seed=42,
            market_model=default_market_model,
        )

        start = time.time()
        result = run_simulation(
            initial_wealth=1_000_000,
            annual_spending=40_000,
            config=config,
            stock_weight=0.6,
        )
        elapsed = time.time() - start

        # Should complete in under 10 seconds
        assert elapsed < 10.0
        assert result.n_simulations == 10_000
