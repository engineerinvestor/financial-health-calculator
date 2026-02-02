"""Session state management for Streamlit app."""

import streamlit as st

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


def initialize_session_state():
    """Initialize all session state variables with defaults."""
    if "initialized" in st.session_state:
        return

    # Default person
    if "household" not in st.session_state:
        st.session_state.household = Household(
            name="My Household",
            members=[
                Person(
                    name="Primary",
                    age=65,
                    retirement_age=None,  # Already retired
                    life_expectancy=95,
                    social_security_age=67,
                    social_security_annual=24000,
                    is_primary=True,
                )
            ],
            balance_sheet=BalanceSheet(
                assets=[
                    Asset(
                        name="401(k)",
                        value=800000,
                        account_type=AccountType.TAX_DEFERRED,
                        asset_class=AssetClass.STOCKS,
                        liquidity_class=LiquidityClass.RETIREMENT,
                        concentration_level=ConcentrationLevel.DIVERSIFIED,
                    ),
                    Asset(
                        name="Roth IRA",
                        value=200000,
                        account_type=AccountType.TAX_EXEMPT,
                        asset_class=AssetClass.STOCKS,
                        liquidity_class=LiquidityClass.RETIREMENT,
                        concentration_level=ConcentrationLevel.DIVERSIFIED,
                    ),
                    Asset(
                        name="Taxable Brokerage",
                        value=300000,
                        account_type=AccountType.TAXABLE,
                        asset_class=AssetClass.STOCKS,
                        liquidity_class=LiquidityClass.TAXABLE_INDEX,
                        concentration_level=ConcentrationLevel.DIVERSIFIED,
                        cost_basis=200000,
                    ),
                    Asset(
                        name="Cash Savings",
                        value=50000,
                        account_type=AccountType.TAXABLE,
                        asset_class=AssetClass.CASH,
                        liquidity_class=LiquidityClass.CASH,
                        concentration_level=ConcentrationLevel.DIVERSIFIED,
                    ),
                ]
            ),
            liabilities=[
                Liability(
                    name="Essential Living Expenses",
                    liability_type=LiabilityType.ESSENTIAL_SPENDING,
                    annual_amount=50000,
                    is_essential=True,
                    inflation_linkage=InflationLinkage.CPI,
                ),
                Liability(
                    name="Discretionary Spending",
                    liability_type=LiabilityType.DISCRETIONARY_SPENDING,
                    annual_amount=20000,
                    is_essential=False,
                    inflation_linkage=InflationLinkage.CPI,
                ),
            ],
        )

    # Market assumptions
    if "market_model" not in st.session_state:
        st.session_state.market_model = MarketModel()

    # Tax assumptions
    if "tax_model" not in st.session_state:
        st.session_state.tax_model = TaxModel()

    # Simulation config
    if "simulation_config" not in st.session_state:
        st.session_state.simulation_config = SimulationConfig(
            n_simulations=5000,
            n_years=40,
        )

    # CEFR result cache
    if "cefr_result" not in st.session_state:
        st.session_state.cefr_result = None

    # Simulation result cache
    if "simulation_result" not in st.session_state:
        st.session_state.simulation_result = None

    # Strategy comparison cache
    if "comparison_result" not in st.session_state:
        st.session_state.comparison_result = None

    st.session_state.initialized = True


def get_household() -> Household:
    """Get the current household from session state."""
    initialize_session_state()
    return st.session_state.household


def update_household(household: Household):
    """Update the household in session state and clear caches."""
    st.session_state.household = household
    st.session_state.cefr_result = None
    st.session_state.simulation_result = None


def get_market_model() -> MarketModel:
    """Get the current market model from session state."""
    initialize_session_state()
    return st.session_state.market_model


def update_market_model(market_model: MarketModel):
    """Update market model and clear caches."""
    st.session_state.market_model = market_model
    st.session_state.simulation_result = None


def get_simulation_config() -> SimulationConfig:
    """Get the current simulation config from session state."""
    initialize_session_state()
    return st.session_state.simulation_config


def clear_all_caches():
    """Clear all cached results."""
    st.session_state.cefr_result = None
    st.session_state.simulation_result = None
    st.session_state.comparison_result = None
