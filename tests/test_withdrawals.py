"""Tests for withdrawal strategies."""

import numpy as np
import pytest

from fundedness.withdrawals.base import WithdrawalContext
from fundedness.withdrawals.fixed_swr import FixedRealSWRPolicy, PercentOfPortfolioPolicy
from fundedness.withdrawals.guardrails import GuardrailsPolicy
from fundedness.withdrawals.rmd_style import RMDStylePolicy
from fundedness.withdrawals.vpw import VPWPolicy, get_vpw_rate


class TestFixedSWRPolicy:
    """Tests for fixed SWR withdrawal policy."""

    def test_initial_withdrawal(self):
        """Initial withdrawal should be rate * initial_wealth."""
        policy = FixedRealSWRPolicy(withdrawal_rate=0.04)
        initial = policy.get_initial_withdrawal(1_000_000)
        assert initial == 40_000

    def test_inflation_adjustment(self):
        """Withdrawal should increase with inflation."""
        policy = FixedRealSWRPolicy(withdrawal_rate=0.04, inflation_rate=0.03)

        context_y0 = WithdrawalContext(
            current_wealth=1_000_000,
            initial_wealth=1_000_000,
            year=0,
        )
        context_y10 = WithdrawalContext(
            current_wealth=1_000_000,
            initial_wealth=1_000_000,
            year=10,
        )

        result_y0 = policy.calculate_withdrawal(context_y0)
        result_y10 = policy.calculate_withdrawal(context_y10)

        # Year 10 should be higher due to inflation
        assert result_y10.amount > result_y0.amount
        # Should be approximately (1.03)^10 higher
        expected_ratio = (1.03) ** 10
        actual_ratio = result_y10.amount / result_y0.amount
        assert abs(actual_ratio - expected_ratio) < 0.01

    def test_floor_applied(self):
        """Floor should prevent spending below minimum."""
        policy = FixedRealSWRPolicy(
            withdrawal_rate=0.04,
            floor_spending=50_000,
        )

        context = WithdrawalContext(
            current_wealth=1_000_000,
            initial_wealth=1_000_000,
            year=0,
        )

        result = policy.calculate_withdrawal(context)
        # 4% of 1M = 40k, but floor is 50k
        assert result.amount == 50_000
        assert result.is_floor_breach

    def test_wealth_cap(self):
        """Can't spend more than available wealth."""
        policy = FixedRealSWRPolicy(withdrawal_rate=0.04)

        context = WithdrawalContext(
            current_wealth=10_000,  # Only 10k available
            initial_wealth=1_000_000,
            year=0,
        )

        result = policy.calculate_withdrawal(context)
        assert result.amount == 10_000


class TestPercentOfPortfolioPolicy:
    """Tests for percent of portfolio policy."""

    def test_spending_scales_with_wealth(self):
        """Spending should scale with current wealth."""
        policy = PercentOfPortfolioPolicy(withdrawal_rate=0.04)

        context_low = WithdrawalContext(
            current_wealth=500_000,
            initial_wealth=1_000_000,
            year=5,
        )
        context_high = WithdrawalContext(
            current_wealth=1_500_000,
            initial_wealth=1_000_000,
            year=5,
        )

        result_low = policy.calculate_withdrawal(context_low)
        result_high = policy.calculate_withdrawal(context_high)

        assert result_low.amount == 20_000  # 4% of 500k
        assert result_high.amount == 60_000  # 4% of 1.5M


class TestGuardrailsPolicy:
    """Tests for guardrails withdrawal policy."""

    def test_initial_withdrawal(self):
        """Initial withdrawal at higher rate."""
        policy = GuardrailsPolicy(initial_rate=0.05)
        initial = policy.get_initial_withdrawal(1_000_000)
        assert initial == 50_000

    def test_spending_cut_when_rate_high(self):
        """Spending should be cut when withdrawal rate exceeds upper guardrail."""
        policy = GuardrailsPolicy(
            initial_rate=0.05,
            upper_guardrail=0.06,
            cut_amount=0.10,
        )

        # Wealth dropped significantly, rate would be high
        context = WithdrawalContext(
            current_wealth=700_000,
            initial_wealth=1_000_000,
            year=1,
            previous_spending=50_000,
        )

        result = policy.calculate_withdrawal(context)

        # Base would be 50k * 1.025 = 51,250
        # Rate = 51,250 / 700,000 = 7.3% > 6% upper guardrail
        # Should cut by 10%
        assert result.amount < 51_250  # Cut was applied

    def test_spending_raise_when_rate_low(self):
        """Spending should increase when withdrawal rate falls below lower guardrail."""
        policy = GuardrailsPolicy(
            initial_rate=0.05,
            lower_guardrail=0.04,
            raise_amount=0.10,
            no_raise_in_down_year=False,
        )

        # Wealth increased significantly
        context = WithdrawalContext(
            current_wealth=1_500_000,
            initial_wealth=1_000_000,
            year=1,
            previous_spending=50_000,
        )

        result = policy.calculate_withdrawal(context)

        # Base would be 50k * 1.025 = 51,250
        # Rate = 51,250 / 1,500,000 = 3.4% < 4% lower guardrail
        # Should raise by 10%
        assert result.amount > 51_250  # Raise was applied


class TestVPWPolicy:
    """Tests for VPW withdrawal policy."""

    def test_vpw_rate_increases_with_age(self):
        """VPW rate should increase as age increases."""
        rate_65 = get_vpw_rate(65)
        rate_75 = get_vpw_rate(75)
        rate_85 = get_vpw_rate(85)

        assert rate_65 < rate_75 < rate_85

    def test_vpw_withdrawal_increases_rate_with_age(self):
        """VPW withdrawal rate should increase with age."""
        policy = VPWPolicy(starting_age=65)

        context_65 = WithdrawalContext(
            current_wealth=1_000_000,
            initial_wealth=1_000_000,
            year=0,
            age=65,
        )
        context_80 = WithdrawalContext(
            current_wealth=1_000_000,
            initial_wealth=1_000_000,
            year=15,
            age=80,
        )

        result_65 = policy.calculate_withdrawal(context_65)
        result_80 = policy.calculate_withdrawal(context_80)

        # Same wealth but higher rate at 80
        assert result_80.amount > result_65.amount


class TestRMDStylePolicy:
    """Tests for RMD-style withdrawal policy."""

    def test_rmd_rate_increases_with_age(self):
        """RMD rate should increase with age."""
        policy = RMDStylePolicy(starting_age=72)

        context_72 = WithdrawalContext(
            current_wealth=1_000_000,
            initial_wealth=1_000_000,
            year=0,
            age=72,
        )
        context_85 = WithdrawalContext(
            current_wealth=1_000_000,
            initial_wealth=1_000_000,
            year=13,
            age=85,
        )

        result_72 = policy.calculate_withdrawal(context_72)
        result_85 = policy.calculate_withdrawal(context_85)

        # Same wealth but higher withdrawal at 85
        assert result_85.amount > result_72.amount

    def test_rmd_multiplier(self):
        """Multiplier should scale withdrawals."""
        policy_1x = RMDStylePolicy(starting_age=72, multiplier=1.0)
        policy_15x = RMDStylePolicy(starting_age=72, multiplier=1.5)

        context = WithdrawalContext(
            current_wealth=1_000_000,
            initial_wealth=1_000_000,
            year=0,
            age=72,
        )

        result_1x = policy_1x.calculate_withdrawal(context)
        result_15x = policy_15x.calculate_withdrawal(context)

        assert result_15x.amount == pytest.approx(result_1x.amount * 1.5, rel=0.01)


class TestVectorizedWithdrawals:
    """Test that policies work with vectorized inputs."""

    def test_fixed_swr_vectorized(self):
        """Fixed SWR should work with array inputs."""
        policy = FixedRealSWRPolicy(withdrawal_rate=0.04)

        wealth_array = np.array([500_000, 1_000_000, 1_500_000])
        context = WithdrawalContext(
            current_wealth=wealth_array,
            initial_wealth=1_000_000,
            year=0,
        )

        result = policy.calculate_withdrawal(context)

        # All should get same amount (4% of initial)
        expected = np.array([40_000, 40_000, 40_000])
        np.testing.assert_array_almost_equal(result.amount, expected)

    def test_percent_portfolio_vectorized(self):
        """Percent of portfolio should work with array inputs."""
        policy = PercentOfPortfolioPolicy(withdrawal_rate=0.04)

        wealth_array = np.array([500_000, 1_000_000, 1_500_000])
        context = WithdrawalContext(
            current_wealth=wealth_array,
            initial_wealth=1_000_000,
            year=0,
        )

        result = policy.calculate_withdrawal(context)

        # Each should get 4% of current wealth
        expected = np.array([20_000, 40_000, 60_000])
        np.testing.assert_array_almost_equal(result.amount, expected)
