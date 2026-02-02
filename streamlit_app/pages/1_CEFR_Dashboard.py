"""CEFR Dashboard page."""

import streamlit as st

from fundedness.cefr import compute_cefr
from fundedness.viz.waterfall import create_cefr_waterfall, create_haircut_breakdown_bar
from streamlit_app.components.metrics_display import render_cefr_metrics, render_funding_gap
from streamlit_app.utils.session_state import get_household, initialize_session_state

st.set_page_config(page_title="CEFR Dashboard", page_icon="📊", layout="wide")

initialize_session_state()

st.title("📊 CEFR Dashboard")

st.markdown("""
The **Certainty-Equivalent Funded Ratio (CEFR)** measures how well your assets can cover
your planned spending, after accounting for taxes, liquidity constraints, and concentration risk.
""")

# Get data from session state
household = get_household()
tax_model = st.session_state.tax_model
market_model = st.session_state.market_model

# Calculate CEFR
with st.spinner("Calculating CEFR..."):
    cefr_result = compute_cefr(
        household=household,
        tax_model=tax_model,
        real_discount_rate=market_model.real_discount_rate,
        base_inflation=market_model.inflation_mean,
    )
    st.session_state.cefr_result = cefr_result

# Display metrics
render_cefr_metrics(cefr_result)

st.divider()

# Visualizations
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("CEFR Waterfall")
    waterfall_fig = create_cefr_waterfall(cefr_result)
    st.plotly_chart(waterfall_fig, use_container_width=True)

with col2:
    st.subheader("Haircut Breakdown")
    bar_fig = create_haircut_breakdown_bar(cefr_result)
    st.plotly_chart(bar_fig, use_container_width=True)

st.divider()

# Funding gap analysis
st.subheader("Funding Analysis")
render_funding_gap(cefr_result)

st.divider()

# Asset detail breakdown
st.subheader("Asset Details")

if cefr_result.asset_details:
    # Create a dataframe for display
    import pandas as pd

    data = []
    for detail in cefr_result.asset_details:
        data.append({
            "Asset": detail.asset.name,
            "Gross Value": f"${detail.gross_value:,.0f}",
            "Tax Rate": f"{detail.tax_rate:.1%}",
            "Liquidity Factor": f"{detail.liquidity_factor:.0%}",
            "Reliability Factor": f"{detail.reliability_factor:.0%}",
            "Net Value": f"${detail.net_value:,.0f}",
            "Total Haircut": f"{detail.total_haircut:.1%}",
        })

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

# Interpretation help
with st.expander("Understanding CEFR"):
    st.markdown("""
    ### What CEFR Tells You

    - **CEFR ≥ 2.0**: Excellent - Very well-funded with significant buffer
    - **CEFR 1.5 - 2.0**: Strong - Well-funded with comfortable margin
    - **CEFR 1.0 - 1.5**: Adequate - Fully funded but limited cushion
    - **CEFR 0.8 - 1.0**: Marginal - Slightly underfunded
    - **CEFR < 0.8**: Concerning - Significantly underfunded

    ### The Three Haircuts

    1. **Tax Haircut**: Accounts for taxes owed when withdrawing from different account types
       - Tax-deferred (401k, Traditional IRA): Full ordinary income tax
       - Taxable: Capital gains tax on appreciation
       - Tax-exempt (Roth): No tax

    2. **Liquidity Haircut**: Accounts for difficulty accessing funds
       - Cash: No haircut (100% liquid)
       - Public securities: Small haircut for trading costs
       - Retirement accounts: Larger haircut for early withdrawal penalties
       - Real estate/business: Large haircut for illiquidity

    3. **Reliability Haircut**: Accounts for concentration risk
       - Diversified index funds: Small haircut
       - Single stocks: Large haircut
       - Startup equity: Very large haircut
    """)
