"""Pytest configuration and fixtures."""

import pytest

from fundedness.models.assets import (
    AccountType,
    Asset,
    AssetClass,
    BalanceSheet,
    ConcentrationLevel,
    LiquidityClass,
)
from fundedness.models.household import Household, Person
from fundedness.models.liabilities import InflationLinkage, Liability, LiabilityType
from fundedness.models.market import MarketModel
from fundedness.models.simulation import SimulationConfig
from fundedness.models.tax import TaxModel


@pytest.fixture
def sample_assets() -> list[Asset]:
    """Create sample assets for testing."""
    return [
        Asset(
            name="401(k)",
            value=500_000,
            account_type=AccountType.TAX_DEFERRED,
            asset_class=AssetClass.STOCKS,
            liquidity_class=LiquidityClass.RETIREMENT,
            concentration_level=ConcentrationLevel.DIVERSIFIED,
        ),
        Asset(
            name="Roth IRA",
            value=200_000,
            account_type=AccountType.TAX_EXEMPT,
            asset_class=AssetClass.STOCKS,
            liquidity_class=LiquidityClass.RETIREMENT,
            concentration_level=ConcentrationLevel.DIVERSIFIED,
        ),
        Asset(
            name="Taxable Brokerage",
            value=300_000,
            account_type=AccountType.TAXABLE,
            asset_class=AssetClass.STOCKS,
            liquidity_class=LiquidityClass.TAXABLE_INDEX,
            concentration_level=ConcentrationLevel.DIVERSIFIED,
            cost_basis=200_000,
        ),
    ]


@pytest.fixture
def sample_balance_sheet(sample_assets) -> BalanceSheet:
    """Create sample balance sheet."""
    return BalanceSheet(assets=sample_assets)


@pytest.fixture
def sample_liabilities() -> list[Liability]:
    """Create sample liabilities for testing."""
    return [
        Liability(
            name="Essential Expenses",
            liability_type=LiabilityType.ESSENTIAL_SPENDING,
            annual_amount=50_000,
            is_essential=True,
            inflation_linkage=InflationLinkage.CPI,
        ),
        Liability(
            name="Discretionary",
            liability_type=LiabilityType.DISCRETIONARY_SPENDING,
            annual_amount=20_000,
            is_essential=False,
            inflation_linkage=InflationLinkage.CPI,
        ),
    ]


@pytest.fixture
def sample_household(sample_balance_sheet, sample_liabilities) -> Household:
    """Create sample household for testing."""
    return Household(
        name="Test Household",
        members=[
            Person(
                name="Test Person",
                age=65,
                life_expectancy=95,
                social_security_age=67,
                social_security_annual=24_000,
                is_primary=True,
            )
        ],
        balance_sheet=sample_balance_sheet,
        liabilities=sample_liabilities,
    )


@pytest.fixture
def default_tax_model() -> TaxModel:
    """Create default tax model."""
    return TaxModel()


@pytest.fixture
def default_market_model() -> MarketModel:
    """Create default market model."""
    return MarketModel()


@pytest.fixture
def default_simulation_config(default_market_model) -> SimulationConfig:
    """Create default simulation config for fast tests."""
    return SimulationConfig(
        n_simulations=100,  # Small for fast tests
        n_years=30,
        random_seed=42,
        market_model=default_market_model,
    )
