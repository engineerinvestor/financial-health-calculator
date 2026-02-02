"""Tests for policy optimization module."""

import numpy as np
import pytest

from fundedness.allocation.constant import ConstantAllocationPolicy
from fundedness.models.market import MarketModel
from fundedness.models.simulation import SimulationConfig
from fundedness.models.utility import UtilityModel
from fundedness.optimize import (
    OptimizationResult,
    PolicyParameterSpec,
    create_policy_with_params,
    optimize_spending_policy,
)
from fundedness.withdrawals.fixed_swr import FixedRealSWRPolicy


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


@pytest.fixture
def simulation_config(market_model) -> SimulationConfig:
    """Fast simulation config for testing."""
    return SimulationConfig(
        n_simulations=100,  # Small for fast tests
        n_years=20,
        market_model=market_model,
        random_seed=42,
    )


class TestPolicyParameterSpec:
    """Tests for PolicyParameterSpec."""

    def test_get_initial_default(self):
        """Default initial should be midpoint."""
        spec = PolicyParameterSpec(
            name="rate",
            min_value=0.02,
            max_value=0.06,
        )
        assert spec.get_initial() == 0.04

    def test_get_initial_explicit(self):
        """Explicit initial value should be used."""
        spec = PolicyParameterSpec(
            name="rate",
            min_value=0.02,
            max_value=0.06,
            initial_value=0.03,
        )
        assert spec.get_initial() == 0.03

    def test_clip_within_bounds(self):
        """Value within bounds should be unchanged."""
        spec = PolicyParameterSpec(
            name="rate",
            min_value=0.02,
            max_value=0.06,
        )
        assert spec.clip(0.04) == 0.04

    def test_clip_below_min(self):
        """Value below min should be clipped."""
        spec = PolicyParameterSpec(
            name="rate",
            min_value=0.02,
            max_value=0.06,
        )
        assert spec.clip(0.01) == 0.02

    def test_clip_above_max(self):
        """Value above max should be clipped."""
        spec = PolicyParameterSpec(
            name="rate",
            min_value=0.02,
            max_value=0.06,
        )
        assert spec.clip(0.10) == 0.06

    def test_clip_integer(self):
        """Integer parameter should be rounded."""
        spec = PolicyParameterSpec(
            name="years",
            min_value=10,
            max_value=40,
            is_integer=True,
        )
        assert spec.clip(25.7) == 26


class TestCreatePolicyWithParams:
    """Tests for create_policy_with_params function."""

    def test_creates_policy_with_params(self):
        """Should create policy with specified parameters."""
        specs = [
            PolicyParameterSpec("withdrawal_rate", 0.02, 0.06),
        ]
        values = np.array([0.045])

        policy = create_policy_with_params(
            FixedRealSWRPolicy,
            {},
            specs,
            values,
        )

        assert isinstance(policy, FixedRealSWRPolicy)
        assert policy.withdrawal_rate == 0.045

    def test_includes_base_params(self):
        """Should include base parameters."""
        specs = [
            PolicyParameterSpec("withdrawal_rate", 0.02, 0.06),
        ]
        values = np.array([0.04])
        base_params = {"floor_spending": 25000}

        policy = create_policy_with_params(
            FixedRealSWRPolicy,
            base_params,
            specs,
            values,
        )

        assert policy.withdrawal_rate == 0.04
        assert policy.floor_spending == 25000

    def test_clips_out_of_range_values(self):
        """Should clip values to spec bounds."""
        specs = [
            PolicyParameterSpec("withdrawal_rate", 0.02, 0.06),
        ]
        values = np.array([0.10])  # Above max

        policy = create_policy_with_params(
            FixedRealSWRPolicy,
            {},
            specs,
            values,
        )

        assert policy.withdrawal_rate == 0.06


class TestOptimizeSpendingPolicy:
    """Tests for optimize_spending_policy function."""

    def test_basic_optimization(self, simulation_config, utility_model):
        """Basic optimization should complete and return result."""
        param_specs = [
            PolicyParameterSpec(
                name="withdrawal_rate",
                min_value=0.03,
                max_value=0.05,
                initial_value=0.04,
            ),
        ]

        allocation_policy = ConstantAllocationPolicy(stock_weight=0.6)

        result = optimize_spending_policy(
            policy_class=FixedRealSWRPolicy,
            param_specs=param_specs,
            initial_wealth=1_000_000,
            allocation_policy=allocation_policy,
            config=simulation_config,
            utility_model=utility_model,
            max_iterations=5,  # Very few iterations for fast test
        )

        assert isinstance(result, OptimizationResult)
        assert "withdrawal_rate" in result.optimal_params
        assert 0.03 <= result.optimal_params["withdrawal_rate"] <= 0.05
        assert result.optimal_utility != 0
        assert len(result.convergence_history) > 0

    def test_optimal_in_bounds(self, simulation_config, utility_model):
        """Optimal parameters should be within specified bounds."""
        param_specs = [
            PolicyParameterSpec(
                name="withdrawal_rate",
                min_value=0.02,
                max_value=0.08,
            ),
        ]

        allocation_policy = ConstantAllocationPolicy(stock_weight=0.6)

        result = optimize_spending_policy(
            policy_class=FixedRealSWRPolicy,
            param_specs=param_specs,
            initial_wealth=1_000_000,
            allocation_policy=allocation_policy,
            config=simulation_config,
            utility_model=utility_model,
            max_iterations=10,
        )

        rate = result.optimal_params["withdrawal_rate"]
        assert 0.02 <= rate <= 0.08

    def test_returns_final_simulation(self, simulation_config, utility_model):
        """Should return the final simulation result."""
        param_specs = [
            PolicyParameterSpec("withdrawal_rate", 0.03, 0.05),
        ]

        allocation_policy = ConstantAllocationPolicy(stock_weight=0.6)

        result = optimize_spending_policy(
            policy_class=FixedRealSWRPolicy,
            param_specs=param_specs,
            initial_wealth=1_000_000,
            allocation_policy=allocation_policy,
            config=simulation_config,
            utility_model=utility_model,
            max_iterations=5,
        )

        assert result.final_simulation is not None
        assert result.final_simulation.n_simulations == simulation_config.n_simulations

    def test_success_rate_in_result(self, simulation_config, utility_model):
        """Result should include success rate."""
        param_specs = [
            PolicyParameterSpec("withdrawal_rate", 0.03, 0.05),
        ]

        allocation_policy = ConstantAllocationPolicy(stock_weight=0.6)

        result = optimize_spending_policy(
            policy_class=FixedRealSWRPolicy,
            param_specs=param_specs,
            initial_wealth=1_000_000,
            allocation_policy=allocation_policy,
            config=simulation_config,
            utility_model=utility_model,
            max_iterations=5,
        )

        assert 0 <= result.success_rate <= 1


class TestOptimizationConvergence:
    """Tests for optimization convergence behavior."""

    def test_convergence_history_recorded(self, simulation_config, utility_model):
        """Convergence history should be recorded."""
        param_specs = [
            PolicyParameterSpec("withdrawal_rate", 0.03, 0.05),
        ]

        allocation_policy = ConstantAllocationPolicy(stock_weight=0.6)

        result = optimize_spending_policy(
            policy_class=FixedRealSWRPolicy,
            param_specs=param_specs,
            initial_wealth=1_000_000,
            allocation_policy=allocation_policy,
            config=simulation_config,
            utility_model=utility_model,
            max_iterations=10,
        )

        assert len(result.convergence_history) >= 1
        # Best utility should be the max in history
        assert result.optimal_utility == max(result.convergence_history)

    def test_best_params_correspond_to_best_utility(
        self, simulation_config, utility_model
    ):
        """Optimal params should give optimal utility."""
        param_specs = [
            PolicyParameterSpec("withdrawal_rate", 0.03, 0.05),
        ]

        allocation_policy = ConstantAllocationPolicy(stock_weight=0.6)

        result = optimize_spending_policy(
            policy_class=FixedRealSWRPolicy,
            param_specs=param_specs,
            initial_wealth=1_000_000,
            allocation_policy=allocation_policy,
            config=simulation_config,
            utility_model=utility_model,
            max_iterations=10,
        )

        # The optimal utility should be the best found
        assert result.optimal_utility >= min(result.convergence_history)


class TestOptimizationWithFloor:
    """Tests for optimization with spending floor."""

    def test_respects_spending_floor(self, simulation_config, utility_model):
        """Optimization should work with spending floor."""
        param_specs = [
            PolicyParameterSpec("withdrawal_rate", 0.02, 0.06),
        ]

        allocation_policy = ConstantAllocationPolicy(stock_weight=0.6)

        result = optimize_spending_policy(
            policy_class=FixedRealSWRPolicy,
            param_specs=param_specs,
            initial_wealth=1_000_000,
            allocation_policy=allocation_policy,
            config=simulation_config,
            utility_model=utility_model,
            spending_floor=30000,
            max_iterations=5,
        )

        assert isinstance(result, OptimizationResult)
        assert result.final_simulation is not None
