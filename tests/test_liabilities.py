"""Tests for liability calculations."""

import pytest

from fundedness.liabilities import (
    calculate_annuity_pv,
    calculate_liability_pv,
    calculate_total_liability_pv,
    generate_liability_schedule,
)
from fundedness.models.liabilities import InflationLinkage, Liability, LiabilityType


class TestAnnuityPV:
    """Tests for annuity present value calculations."""

    def test_simple_annuity(self):
        """Test simple fixed annuity PV."""
        # $10,000/year for 10 years at 5% discount
        pv = calculate_annuity_pv(
            annual_payment=10_000,
            n_years=10,
            discount_rate=0.05,
            growth_rate=0.0,
        )

        # Expected PV = 10000 * (1 - 1.05^-10) / 0.05 ≈ 77,217
        assert pv == pytest.approx(77_217, rel=0.01)

    def test_zero_years(self):
        """Zero years should return zero PV."""
        pv = calculate_annuity_pv(
            annual_payment=10_000,
            n_years=0,
            discount_rate=0.05,
        )
        assert pv == 0.0

    def test_growing_annuity(self):
        """Growing annuity should have higher PV."""
        pv_fixed = calculate_annuity_pv(
            annual_payment=10_000,
            n_years=20,
            discount_rate=0.05,
            growth_rate=0.0,
        )
        pv_growing = calculate_annuity_pv(
            annual_payment=10_000,
            n_years=20,
            discount_rate=0.05,
            growth_rate=0.02,
        )

        assert pv_growing > pv_fixed

    def test_delayed_start(self):
        """Delayed start should reduce PV."""
        pv_immediate = calculate_annuity_pv(
            annual_payment=10_000,
            n_years=10,
            discount_rate=0.05,
            start_year=0,
        )
        pv_delayed = calculate_annuity_pv(
            annual_payment=10_000,
            n_years=10,
            discount_rate=0.05,
            start_year=5,
        )

        assert pv_delayed < pv_immediate


class TestLiabilityPV:
    """Tests for single liability PV calculations."""

    def test_essential_liability(self):
        """Test PV of essential spending liability."""
        liability = Liability(
            name="Living Expenses",
            liability_type=LiabilityType.ESSENTIAL_SPENDING,
            annual_amount=50_000,
            is_essential=True,
            inflation_linkage=InflationLinkage.CPI,
        )

        result = calculate_liability_pv(
            liability=liability,
            planning_horizon=30,
            real_discount_rate=0.02,
            base_inflation=0.025,
        )

        assert result.present_value > 0
        assert result.present_value < liability.annual_amount * 30  # Discounting effect

    def test_time_limited_liability(self):
        """Test PV of liability with specific end date."""
        liability = Liability(
            name="Mortgage",
            liability_type=LiabilityType.MORTGAGE,
            annual_amount=24_000,
            start_year=0,
            end_year=10,
            inflation_linkage=InflationLinkage.NONE,  # Fixed payments
        )

        result = calculate_liability_pv(
            liability=liability,
            planning_horizon=30,
            real_discount_rate=0.02,
        )

        # Should be less than 10 * 24,000 = 240,000 due to discounting
        assert result.present_value < 240_000
        assert result.present_value > 0

    def test_probability_adjustment(self):
        """Probability < 1 should reduce PV."""
        liability_certain = Liability(
            name="Certain",
            annual_amount=10_000,
            probability=1.0,
        )
        liability_uncertain = Liability(
            name="Uncertain",
            annual_amount=10_000,
            probability=0.5,
        )

        pv_certain = calculate_liability_pv(
            liability=liability_certain,
            planning_horizon=20,
        )
        pv_uncertain = calculate_liability_pv(
            liability=liability_uncertain,
            planning_horizon=20,
        )

        assert pv_uncertain.present_value == pytest.approx(
            pv_certain.present_value * 0.5, rel=0.01
        )


class TestTotalLiabilityPV:
    """Tests for total liability PV calculations."""

    def test_sum_of_liabilities(self):
        """Total PV should be sum of individual PVs."""
        liabilities = [
            Liability(name="Essential", annual_amount=50_000, is_essential=True),
            Liability(name="Discretionary", annual_amount=20_000, is_essential=False),
        ]

        total_pv, details = calculate_total_liability_pv(
            liabilities=liabilities,
            planning_horizon=30,
        )

        sum_of_details = sum(d.present_value for d in details)
        assert total_pv == pytest.approx(sum_of_details, rel=0.01)

    def test_empty_liabilities(self):
        """Empty liabilities should return zero."""
        total_pv, details = calculate_total_liability_pv(
            liabilities=[],
            planning_horizon=30,
        )

        assert total_pv == 0.0
        assert len(details) == 0


class TestLiabilitySchedule:
    """Tests for liability schedule generation."""

    def test_schedule_shape(self):
        """Schedule should have correct shape."""
        liabilities = [
            Liability(name="Spending", annual_amount=50_000),
        ]

        schedule = generate_liability_schedule(
            liabilities=liabilities,
            n_years=30,
        )

        assert len(schedule) == 30

    def test_schedule_inflation(self):
        """Schedule should increase with inflation."""
        liabilities = [
            Liability(
                name="Spending",
                annual_amount=50_000,
                inflation_linkage=InflationLinkage.CPI,
            ),
        ]

        schedule = generate_liability_schedule(
            liabilities=liabilities,
            n_years=30,
            base_inflation=0.025,
        )

        # Year 0 should be base amount
        assert schedule[0] == pytest.approx(50_000, rel=0.01)

        # Year 29 should be inflated
        expected_y29 = 50_000 * (1.025 ** 29)
        assert schedule[29] == pytest.approx(expected_y29, rel=0.01)

    def test_schedule_with_delayed_start(self):
        """Delayed liability should show zeros early."""
        liabilities = [
            Liability(
                name="Future Expense",
                annual_amount=10_000,
                start_year=5,
                end_year=15,
            ),
        ]

        schedule = generate_liability_schedule(
            liabilities=liabilities,
            n_years=20,
        )

        # Years 0-4 should be zero
        for i in range(5):
            assert schedule[i] == 0.0

        # Years 5-14 should have spending
        for i in range(5, 15):
            assert schedule[i] > 0

        # Years 15-19 should be zero
        for i in range(15, 20):
            assert schedule[i] == 0.0
