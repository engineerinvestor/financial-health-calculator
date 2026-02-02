"""Metrics display components for Streamlit."""

import streamlit as st

from fundedness.cefr import CEFRResult
from fundedness.simulate import SimulationResult


def render_cefr_metrics(result: CEFRResult):
    """Render CEFR metrics in a dashboard format.

    Args:
        result: CEFR calculation result
    """
    # Main CEFR metric with color coding
    cefr_color = "normal"
    if result.cefr >= 1.5:
        cefr_color = "off"  # Green-ish
    elif result.cefr < 1.0:
        cefr_color = "inverse"  # Red

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="CEFR",
            value=f"{result.cefr:.2f}",
            delta=f"{'Funded' if result.is_funded else 'Underfunded'}",
            delta_color=cefr_color,
        )

    with col2:
        st.metric(
            label="Net Assets",
            value=f"${result.net_assets:,.0f}",
        )

    with col3:
        st.metric(
            label="Liability PV",
            value=f"${result.liability_pv:,.0f}",
        )

    # Interpretation
    st.info(result.get_interpretation())

    # Haircut breakdown
    st.subheader("Haircut Breakdown")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Gross Assets",
            value=f"${result.gross_assets:,.0f}",
        )

    with col2:
        pct = result.total_tax_haircut / result.gross_assets * 100 if result.gross_assets > 0 else 0
        st.metric(
            label="Tax Haircut",
            value=f"${result.total_tax_haircut:,.0f}",
            delta=f"-{pct:.1f}%",
            delta_color="inverse",
        )

    with col3:
        pct = result.total_liquidity_haircut / result.gross_assets * 100 if result.gross_assets > 0 else 0
        st.metric(
            label="Liquidity Haircut",
            value=f"${result.total_liquidity_haircut:,.0f}",
            delta=f"-{pct:.1f}%",
            delta_color="inverse",
        )

    with col4:
        pct = result.total_reliability_haircut / result.gross_assets * 100 if result.gross_assets > 0 else 0
        st.metric(
            label="Reliability Haircut",
            value=f"${result.total_reliability_haircut:,.0f}",
            delta=f"-{pct:.1f}%",
            delta_color="inverse",
        )


def render_simulation_metrics(result: SimulationResult):
    """Render simulation metrics in a dashboard format.

    Args:
        result: Simulation result
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        color = "off" if result.success_rate >= 0.9 else "normal" if result.success_rate >= 0.75 else "inverse"
        st.metric(
            label="Success Rate",
            value=f"{result.success_rate:.1%}",
            delta="Low Risk" if result.success_rate >= 0.9 else "Moderate Risk" if result.success_rate >= 0.75 else "High Risk",
            delta_color=color,
        )

    with col2:
        st.metric(
            label="Median Terminal Wealth",
            value=f"${result.median_terminal_wealth:,.0f}",
        )

    with col3:
        st.metric(
            label="Floor Breach Rate",
            value=f"{result.floor_breach_rate:.1%}",
        )

    with col4:
        st.metric(
            label="Simulations",
            value=f"{result.n_simulations:,}",
        )


def render_funding_gap(result: CEFRResult):
    """Render funding gap analysis.

    Args:
        result: CEFR calculation result
    """
    gap = result.funding_gap

    if gap > 0:
        st.warning(f"**Funding Gap:** ${gap:,.0f}")
        st.write("Options to close the gap:")
        st.write("- Increase savings / delay retirement")
        st.write("- Reduce spending targets")
        st.write("- Delay Social Security claiming")
        st.write("- Consider part-time work in early retirement")
    else:
        surplus = -gap
        st.success(f"**Funding Surplus:** ${surplus:,.0f}")
        st.write("You have flexibility to:")
        st.write("- Increase discretionary spending")
        st.write("- Retire earlier")
        st.write("- Leave a larger legacy")
        st.write("- Take a more conservative investment approach")
