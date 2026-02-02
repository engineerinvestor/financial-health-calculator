"""Liability editor component for Streamlit."""

import streamlit as st

from fundedness.models.liabilities import InflationLinkage, Liability, LiabilityType


def render_liability_editor(liabilities: list[Liability]) -> list[Liability]:
    """Render an editable list of liabilities.

    Args:
        liabilities: Current list of liabilities

    Returns:
        Updated list of liabilities
    """
    st.subheader("Spending & Liabilities")

    updated_liabilities = liabilities.copy()

    if updated_liabilities:
        for i, liability in enumerate(updated_liabilities):
            with st.expander(
                f"{liability.name} - ${liability.annual_amount:,.0f}/year",
                expanded=False,
            ):
                col1, col2 = st.columns(2)

                with col1:
                    new_name = st.text_input(
                        "Name",
                        value=liability.name,
                        key=f"liability_name_{i}",
                    )
                    new_amount = st.number_input(
                        "Annual Amount ($)",
                        value=int(liability.annual_amount),
                        min_value=0,
                        step=1000,
                        key=f"liability_amount_{i}",
                    )
                    new_type = st.selectbox(
                        "Type",
                        options=list(LiabilityType),
                        index=list(LiabilityType).index(liability.liability_type),
                        format_func=lambda x: x.value.replace("_", " ").title(),
                        key=f"liability_type_{i}",
                    )

                with col2:
                    new_start = st.number_input(
                        "Start Year",
                        value=liability.start_year,
                        min_value=0,
                        max_value=50,
                        key=f"liability_start_{i}",
                    )
                    new_end = st.number_input(
                        "End Year (0 = until death)",
                        value=liability.end_year or 0,
                        min_value=0,
                        max_value=100,
                        key=f"liability_end_{i}",
                    )
                    new_inflation = st.selectbox(
                        "Inflation Linkage",
                        options=list(InflationLinkage),
                        index=list(InflationLinkage).index(liability.inflation_linkage),
                        format_func=lambda x: x.value.upper(),
                        key=f"liability_inflation_{i}",
                    )

                new_essential = st.checkbox(
                    "Essential (Floor) Spending",
                    value=liability.is_essential,
                    key=f"liability_essential_{i}",
                )

                # Update liability
                updated_liabilities[i] = Liability(
                    name=new_name,
                    liability_type=new_type,
                    annual_amount=float(new_amount),
                    start_year=new_start,
                    end_year=new_end if new_end > 0 else None,
                    inflation_linkage=new_inflation,
                    is_essential=new_essential,
                )

                # Delete button
                if st.button("Delete Liability", key=f"delete_liability_{i}"):
                    updated_liabilities.pop(i)
                    st.rerun()

    # Add new liability
    st.divider()
    if st.button("Add New Liability"):
        updated_liabilities.append(
            Liability(
                name="New Expense",
                liability_type=LiabilityType.ESSENTIAL_SPENDING,
                annual_amount=10000,
                is_essential=True,
            )
        )
        st.rerun()

    # Summary
    essential = sum(l.annual_amount for l in updated_liabilities if l.is_essential)
    discretionary = sum(l.annual_amount for l in updated_liabilities if not l.is_essential)

    col1, col2, col3 = st.columns(3)
    col1.metric("Essential Spending", f"${essential:,.0f}/year")
    col2.metric("Discretionary", f"${discretionary:,.0f}/year")
    col3.metric("Total Spending", f"${essential + discretionary:,.0f}/year")

    return updated_liabilities
