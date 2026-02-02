"""Tests for CEFR calculation."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fundedness.cefr import CEFRResult, compute_asset_haircuts, compute_cefr
from fundedness.models.assets import (
    AccountType,
    Asset,
    AssetClass,
    BalanceSheet,
    ConcentrationLevel,
    LiquidityClass,
)
from fundedness.models.liabilities import Liability, LiabilityType
from fundedness.models.tax import TaxModel


class TestCEFRCalculation:
    """Tests for CEFR computation."""

    def test_cefr_with_sample_data(self, sample_household, default_tax_model):
        """Test CEFR calculation with sample household."""
        result = compute_cefr(
            household=sample_household,
            tax_model=default_tax_model,
        )

        assert isinstance(result, CEFRResult)
        assert result.cefr > 0
        assert result.gross_assets == 1_000_000
        assert result.net_assets < result.gross_assets  # Haircuts reduce value
        assert result.liability_pv > 0

    def test_cefr_with_no_liabilities(self, sample_balance_sheet, default_tax_model):
        """CEFR should be infinite with no liabilities."""
        result = compute_cefr(
            balance_sheet=sample_balance_sheet,
            liabilities=[],
            tax_model=default_tax_model,
        )

        assert result.cefr == float("inf")
        assert result.is_funded is True

    def test_cefr_with_no_assets(self, sample_liabilities, default_tax_model):
        """CEFR should be zero with no assets."""
        result = compute_cefr(
            balance_sheet=BalanceSheet(assets=[]),
            liabilities=sample_liabilities,
            tax_model=default_tax_model,
        )

        assert result.cefr == 0.0
        assert result.is_funded is False

    def test_haircuts_applied_correctly(self, sample_balance_sheet, default_tax_model):
        """Verify haircuts are applied in correct order."""
        result = compute_cefr(
            balance_sheet=sample_balance_sheet,
            liabilities=[
                Liability(
                    name="Spending",
                    annual_amount=50_000,
                    liability_type=LiabilityType.ESSENTIAL_SPENDING,
                )
            ],
            tax_model=default_tax_model,
        )

        # Check decomposition adds up
        total_haircut = (
            result.total_tax_haircut
            + result.total_liquidity_haircut
            + result.total_reliability_haircut
        )
        assert abs(result.gross_assets - result.net_assets - total_haircut) < 0.01

    def test_cefr_interpretation(self):
        """Test CEFR interpretation messages."""
        result_excellent = CEFRResult(
            cefr=2.5,
            gross_assets=1_000_000,
            total_tax_haircut=100_000,
            total_liquidity_haircut=50_000,
            total_reliability_haircut=50_000,
            net_assets=800_000,
            liability_pv=320_000,
        )
        assert "Excellent" in result_excellent.get_interpretation()

        result_critical = CEFRResult(
            cefr=0.3,
            gross_assets=100_000,
            total_tax_haircut=10_000,
            total_liquidity_haircut=5_000,
            total_reliability_haircut=5_000,
            net_assets=80_000,
            liability_pv=270_000,
        )
        assert "Critical" in result_critical.get_interpretation()


class TestAssetHaircuts:
    """Tests for individual asset haircut calculations."""

    def test_tax_deferred_haircut(self, default_tax_model):
        """Tax-deferred accounts get full ordinary income tax haircut."""
        asset = Asset(
            name="401k",
            value=100_000,
            account_type=AccountType.TAX_DEFERRED,
            asset_class=AssetClass.STOCKS,
            liquidity_class=LiquidityClass.RETIREMENT,
            concentration_level=ConcentrationLevel.DIVERSIFIED,
        )

        detail = compute_asset_haircuts(asset, default_tax_model)

        # Should have significant tax haircut
        assert detail.tax_rate > 0.2
        assert detail.after_tax_value < detail.gross_value

    def test_roth_no_tax_haircut(self, default_tax_model):
        """Roth accounts should have no tax haircut."""
        asset = Asset(
            name="Roth IRA",
            value=100_000,
            account_type=AccountType.TAX_EXEMPT,
            asset_class=AssetClass.STOCKS,
            liquidity_class=LiquidityClass.RETIREMENT,
            concentration_level=ConcentrationLevel.DIVERSIFIED,
        )

        detail = compute_asset_haircuts(asset, default_tax_model)

        assert detail.tax_rate == 0.0
        assert detail.after_tax_value == detail.gross_value

    def test_liquidity_haircuts_ordering(self):
        """Test that liquidity haircuts are ordered correctly."""
        tax_model = TaxModel()

        # Cash should have highest liquidity factor
        cash = compute_asset_haircuts(
            Asset(
                name="Cash",
                value=100_000,
                account_type=AccountType.TAXABLE,
                asset_class=AssetClass.CASH,
                liquidity_class=LiquidityClass.CASH,
                concentration_level=ConcentrationLevel.DIVERSIFIED,
            ),
            tax_model,
        )

        # Home equity should have lower liquidity factor
        home = compute_asset_haircuts(
            Asset(
                name="Home Equity",
                value=100_000,
                account_type=AccountType.TAXABLE,
                asset_class=AssetClass.REAL_ESTATE,
                liquidity_class=LiquidityClass.HOME_EQUITY,
                concentration_level=ConcentrationLevel.DIVERSIFIED,
            ),
            tax_model,
        )

        assert cash.liquidity_factor > home.liquidity_factor

    def test_concentration_haircuts_ordering(self):
        """Test that concentration haircuts are ordered correctly."""
        tax_model = TaxModel()

        # Diversified should have highest reliability
        diversified = compute_asset_haircuts(
            Asset(
                name="Index Fund",
                value=100_000,
                account_type=AccountType.TAXABLE,
                asset_class=AssetClass.STOCKS,
                liquidity_class=LiquidityClass.TAXABLE_INDEX,
                concentration_level=ConcentrationLevel.DIVERSIFIED,
            ),
            tax_model,
        )

        # Single stock should have lower reliability
        single = compute_asset_haircuts(
            Asset(
                name="Company Stock",
                value=100_000,
                account_type=AccountType.TAXABLE,
                asset_class=AssetClass.STOCKS,
                liquidity_class=LiquidityClass.TAXABLE_INDEX,
                concentration_level=ConcentrationLevel.SINGLE_STOCK,
            ),
            tax_model,
        )

        assert diversified.reliability_factor > single.reliability_factor


class TestCEFRPropertyTests:
    """Property-based tests for CEFR monotonicity."""

    @given(
        asset_value=st.floats(min_value=10_000, max_value=10_000_000),
        spending=st.floats(min_value=10_000, max_value=200_000),
    )
    @settings(max_examples=50)
    def test_more_assets_higher_cefr(self, asset_value, spending):
        """Property: More assets should always increase CEFR."""
        assets_low = [
            Asset(
                name="Test",
                value=asset_value,
                account_type=AccountType.TAXABLE,
                liquidity_class=LiquidityClass.TAXABLE_INDEX,
                concentration_level=ConcentrationLevel.DIVERSIFIED,
            )
        ]
        assets_high = [
            Asset(
                name="Test",
                value=asset_value * 1.5,
                account_type=AccountType.TAXABLE,
                liquidity_class=LiquidityClass.TAXABLE_INDEX,
                concentration_level=ConcentrationLevel.DIVERSIFIED,
            )
        ]

        liabilities = [
            Liability(
                name="Spending",
                annual_amount=spending,
                liability_type=LiabilityType.ESSENTIAL_SPENDING,
            )
        ]

        result_low = compute_cefr(
            balance_sheet=BalanceSheet(assets=assets_low),
            liabilities=liabilities,
        )
        result_high = compute_cefr(
            balance_sheet=BalanceSheet(assets=assets_high),
            liabilities=liabilities,
        )

        assert result_high.cefr >= result_low.cefr

    @given(
        asset_value=st.floats(min_value=100_000, max_value=5_000_000),
        spending_low=st.floats(min_value=20_000, max_value=100_000),
    )
    @settings(max_examples=50)
    def test_more_spending_lower_cefr(self, asset_value, spending_low):
        """Property: More spending should always decrease CEFR."""
        spending_high = spending_low * 1.5

        assets = [
            Asset(
                name="Test",
                value=asset_value,
                account_type=AccountType.TAXABLE,
                liquidity_class=LiquidityClass.TAXABLE_INDEX,
                concentration_level=ConcentrationLevel.DIVERSIFIED,
            )
        ]

        result_low_spending = compute_cefr(
            balance_sheet=BalanceSheet(assets=assets),
            liabilities=[
                Liability(
                    name="Spending",
                    annual_amount=spending_low,
                    liability_type=LiabilityType.ESSENTIAL_SPENDING,
                )
            ],
        )
        result_high_spending = compute_cefr(
            balance_sheet=BalanceSheet(assets=assets),
            liabilities=[
                Liability(
                    name="Spending",
                    annual_amount=spending_high,
                    liability_type=LiabilityType.ESSENTIAL_SPENDING,
                )
            ],
        )

        assert result_low_spending.cefr >= result_high_spending.cefr
