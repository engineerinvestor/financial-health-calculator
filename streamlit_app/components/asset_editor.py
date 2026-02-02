"""Asset editor component for Streamlit."""

import streamlit as st

from fundedness.models.assets import (
    AccountType,
    Asset,
    AssetClass,
    BalanceSheet,
    ConcentrationLevel,
    LiquidityClass,
)


def render_asset_editor(balance_sheet: BalanceSheet) -> BalanceSheet:
    """Render an editable table of assets.

    Args:
        balance_sheet: Current balance sheet

    Returns:
        Updated balance sheet
    """
    st.subheader("Assets")

    # Display current assets
    assets = balance_sheet.assets.copy()

    if assets:
        for i, asset in enumerate(assets):
            with st.expander(f"{asset.name} - ${asset.value:,.0f}", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    new_name = st.text_input(
                        "Name",
                        value=asset.name,
                        key=f"asset_name_{i}",
                    )
                    new_value = st.number_input(
                        "Value ($)",
                        value=int(asset.value),
                        min_value=0,
                        step=10000,
                        key=f"asset_value_{i}",
                    )
                    new_account_type = st.selectbox(
                        "Account Type",
                        options=list(AccountType),
                        index=list(AccountType).index(asset.account_type),
                        format_func=lambda x: x.value.replace("_", " ").title(),
                        key=f"asset_account_{i}",
                    )

                with col2:
                    new_asset_class = st.selectbox(
                        "Asset Class",
                        options=list(AssetClass),
                        index=list(AssetClass).index(asset.asset_class),
                        format_func=lambda x: x.value.replace("_", " ").title(),
                        key=f"asset_class_{i}",
                    )
                    new_liquidity = st.selectbox(
                        "Liquidity",
                        options=list(LiquidityClass),
                        index=list(LiquidityClass).index(asset.liquidity_class),
                        format_func=lambda x: x.value.replace("_", " ").title(),
                        key=f"asset_liquidity_{i}",
                    )
                    new_concentration = st.selectbox(
                        "Concentration",
                        options=list(ConcentrationLevel),
                        index=list(ConcentrationLevel).index(asset.concentration_level),
                        format_func=lambda x: x.value.replace("_", " ").title(),
                        key=f"asset_concentration_{i}",
                    )

                # Cost basis for taxable accounts
                new_cost_basis = None
                if new_account_type == AccountType.TAXABLE:
                    new_cost_basis = st.number_input(
                        "Cost Basis ($)",
                        value=int(asset.cost_basis or asset.value * 0.5),
                        min_value=0,
                        step=10000,
                        key=f"asset_basis_{i}",
                    )

                # Update asset
                assets[i] = Asset(
                    name=new_name,
                    value=float(new_value),
                    account_type=new_account_type,
                    asset_class=new_asset_class,
                    liquidity_class=new_liquidity,
                    concentration_level=new_concentration,
                    cost_basis=float(new_cost_basis) if new_cost_basis else None,
                )

                # Delete button
                if st.button("Delete Asset", key=f"delete_asset_{i}"):
                    assets.pop(i)
                    st.rerun()

    # Add new asset
    st.divider()
    if st.button("Add New Asset"):
        assets.append(
            Asset(
                name="New Asset",
                value=100000,
                account_type=AccountType.TAXABLE,
                asset_class=AssetClass.STOCKS,
                liquidity_class=LiquidityClass.TAXABLE_INDEX,
                concentration_level=ConcentrationLevel.DIVERSIFIED,
            )
        )
        st.rerun()

    # Summary
    new_balance_sheet = BalanceSheet(assets=assets)
    st.metric("Total Assets", f"${new_balance_sheet.total_value:,.0f}")

    return new_balance_sheet
