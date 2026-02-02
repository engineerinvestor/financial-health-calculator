"""Main Streamlit application entry point.

Financial Health Calculator - A comprehensive retirement planning toolkit.
"""

import streamlit as st

# Page config must be first Streamlit command
st.set_page_config(
    page_title="Financial Health Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys
from pathlib import Path

# Add parent directory to path for imports when running on Streamlit Cloud
sys.path.insert(0, str(Path(__file__).parent.parent))

from streamlit_app.utils.session_state import initialize_session_state

# Initialize session state
initialize_session_state()

# Main page content
st.title("📊 Financial Health Calculator")

st.markdown("""
Welcome to the **Financial Health Calculator**, a comprehensive retirement planning toolkit.

This application helps you:
- **Calculate your CEFR** (Certainty-Equivalent Funded Ratio) - understand how well-funded your retirement is
- **Run Monte Carlo simulations** - see the range of possible outcomes
- **Compare withdrawal strategies** - find the approach that works best for you
- **Analyze sensitivity** - understand which factors matter most

## Getting Started

Use the sidebar to navigate between pages:

1. **📝 Inputs** - Enter your assets, spending, and assumptions
2. **📊 CEFR Dashboard** - See your fundedness ratio and breakdown
3. **📈 Time Runway** - View Monte Carlo projections
4. **💰 Withdrawal Lab** - Compare withdrawal strategies
5. **🎯 Sensitivity** - Understand key risk factors

## Quick Overview

""")

# Show quick summary from session state
household = st.session_state.household

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Assets",
        f"${household.total_assets:,.0f}",
    )

with col2:
    st.metric(
        "Annual Spending Target",
        f"${household.total_spending:,.0f}",
    )

with col3:
    if household.primary_member:
        st.metric(
            "Planning Horizon",
            f"{household.planning_horizon} years",
        )

st.markdown("---")

st.markdown("""
## Key Concepts

### CEFR (Certainty-Equivalent Funded Ratio)

CEFR measures how well-funded your retirement is after accounting for:
- **Taxes** - What you'll owe when withdrawing from different accounts
- **Liquidity** - How easily you can access your assets
- **Reliability** - Risk from concentrated positions

**CEFR ≥ 1.0** means your assets can cover your planned spending.

### Monte Carlo Simulation

Instead of assuming fixed returns, we simulate thousands of possible market scenarios to show:
- The range of possible outcomes (P10, P50, P90)
- Probability of running out of money
- Probability of falling below essential spending

### Withdrawal Strategies

Different approaches to deciding how much to spend each year:
- **Fixed SWR** - Traditional 4% rule
- **Guardrails** - Adjust spending based on portfolio performance
- **VPW** - Variable percentage based on age
- **RMD-Style** - Following IRS distribution tables
""")

# Footer
st.markdown("---")
st.markdown(
    "*Built with [Streamlit](https://streamlit.io) and "
    "[Plotly](https://plotly.com). "
    "This tool is for educational purposes only and does not constitute financial advice.*"
)
