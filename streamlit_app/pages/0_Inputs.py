"""Inputs page for asset, liability, and assumption entry."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from fundedness.models.household import Household, Person
from fundedness.models.market import MarketModel
from fundedness.models.tax import TaxModel
from streamlit_app.components.asset_editor import render_asset_editor
from streamlit_app.components.liability_editor import render_liability_editor
from streamlit_app.utils.session_state import (
    get_household,
    get_market_model,
    initialize_session_state,
    update_household,
    update_market_model,
)

st.set_page_config(page_title="Inputs", page_icon="📝", layout="wide")

initialize_session_state()

st.title("📝 Inputs")

st.markdown("""
Enter your financial information below. Changes are automatically saved.
""")

# Tabs for different input sections
tab1, tab2, tab3, tab4 = st.tabs([
    "👤 Personal Info",
    "💰 Assets",
    "📋 Spending",
    "⚙️ Assumptions",
])

household = get_household()

# Personal Info Tab
with tab1:
    st.subheader("Personal Information")

    if household.members:
        member = household.members[0]

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Name", value=member.name)
            age = st.number_input(
                "Current Age",
                value=member.age,
                min_value=25,
                max_value=100,
            )
            life_expectancy = st.number_input(
                "Planning Life Expectancy",
                value=member.life_expectancy,
                min_value=member.age + 1,
                max_value=120,
            )

        with col2:
            ss_age = st.number_input(
                "Social Security Claiming Age",
                value=member.social_security_age,
                min_value=62,
                max_value=70,
            )
            ss_annual = st.number_input(
                "Expected Annual Social Security ($)",
                value=int(member.social_security_annual),
                min_value=0,
                step=1000,
            )
            pension = st.number_input(
                "Annual Pension ($)",
                value=int(member.pension_annual),
                min_value=0,
                step=1000,
            )

        # Update member
        updated_member = Person(
            name=name,
            age=age,
            life_expectancy=life_expectancy,
            social_security_age=ss_age,
            social_security_annual=float(ss_annual),
            pension_annual=float(pension),
            is_primary=True,
        )

        if updated_member != member:
            household.members[0] = updated_member
            update_household(household)

# Assets Tab
with tab2:
    new_balance_sheet = render_asset_editor(household.balance_sheet)

    if new_balance_sheet != household.balance_sheet:
        household.balance_sheet = new_balance_sheet
        update_household(household)

# Spending Tab
with tab3:
    new_liabilities = render_liability_editor(household.liabilities)

    if new_liabilities != household.liabilities:
        household.liabilities = new_liabilities
        update_household(household)

# Assumptions Tab
with tab4:
    st.subheader("Market Assumptions")

    market_model = get_market_model()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Expected Returns (Real)**")
        stock_return = st.slider(
            "Stocks",
            min_value=0.0,
            max_value=0.10,
            value=market_model.stock_return,
            step=0.005,
            format="%.1f%%",
        )
        bond_return = st.slider(
            "Bonds",
            min_value=-0.02,
            max_value=0.05,
            value=market_model.bond_return,
            step=0.005,
            format="%.1f%%",
        )

        st.markdown("**Volatility**")
        stock_vol = st.slider(
            "Stock Volatility",
            min_value=0.10,
            max_value=0.25,
            value=market_model.stock_volatility,
            step=0.01,
            format="%.0f%%",
        )

    with col2:
        st.markdown("**Inflation**")
        inflation = st.slider(
            "Expected Inflation",
            min_value=0.01,
            max_value=0.05,
            value=market_model.inflation_mean,
            step=0.005,
            format="%.1f%%",
        )

        st.markdown("**Discount Rate**")
        discount = st.slider(
            "Real Discount Rate",
            min_value=0.0,
            max_value=0.05,
            value=market_model.real_discount_rate,
            step=0.005,
            format="%.1f%%",
        )

        use_fat_tails = st.checkbox(
            "Use Fat Tails (t-distribution)",
            value=market_model.use_fat_tails,
        )

    # Update market model
    new_market_model = MarketModel(
        stock_return=stock_return,
        bond_return=bond_return,
        stock_volatility=stock_vol,
        inflation_mean=inflation,
        real_discount_rate=discount,
        use_fat_tails=use_fat_tails,
    )

    if new_market_model != market_model:
        update_market_model(new_market_model)

    st.divider()

    st.subheader("Tax Assumptions")

    tax_model = st.session_state.tax_model

    col1, col2 = st.columns(2)

    with col1:
        federal_rate = st.slider(
            "Federal Marginal Rate",
            min_value=0.0,
            max_value=0.40,
            value=tax_model.federal_ordinary_rate,
            step=0.01,
            format="%.0f%%",
        )
        ltcg_rate = st.slider(
            "Federal LTCG Rate",
            min_value=0.0,
            max_value=0.25,
            value=tax_model.federal_ltcg_rate,
            step=0.01,
            format="%.0f%%",
        )

    with col2:
        state_rate = st.slider(
            "State Tax Rate",
            min_value=0.0,
            max_value=0.15,
            value=tax_model.state_ordinary_rate,
            step=0.01,
            format="%.1f%%",
        )

    st.session_state.tax_model = TaxModel(
        federal_ordinary_rate=federal_rate,
        federal_ltcg_rate=ltcg_rate,
        federal_stcg_rate=federal_rate,
        state_ordinary_rate=state_rate,
        state_ltcg_rate=state_rate,
    )

# Summary
st.divider()
st.subheader("Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Assets", f"${household.total_assets:,.0f}")
col2.metric("Annual Spending", f"${household.total_spending:,.0f}")
col3.metric("Planning Horizon", f"{household.planning_horizon} years")
col4.metric("Withdrawal Rate", f"{household.total_spending / household.total_assets * 100:.1f}%" if household.total_assets > 0 else "N/A")
