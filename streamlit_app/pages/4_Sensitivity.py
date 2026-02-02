"""Sensitivity Analysis page."""

import streamlit as st

from fundedness.cefr import compute_cefr
from fundedness.models.market import MarketModel
from fundedness.viz.tornado import create_scenario_comparison_chart, create_tornado_chart
from streamlit_app.utils.session_state import (
    get_household,
    get_market_model,
    initialize_session_state,
)

st.set_page_config(page_title="Sensitivity Analysis", page_icon="🎯", layout="wide")

initialize_session_state()

st.title("🎯 Sensitivity Analysis")

st.markdown("""
Understand which factors have the biggest impact on your CEFR and retirement outcomes.
""")

# Get data
household = get_household()
market_model = get_market_model()
tax_model = st.session_state.tax_model

# Calculate base CEFR
base_result = compute_cefr(
    household=household,
    tax_model=tax_model,
    real_discount_rate=market_model.real_discount_rate,
    base_inflation=market_model.inflation_mean,
)
base_cefr = base_result.cefr

st.metric("Base CEFR", f"{base_cefr:.2f}")

st.divider()

# Tornado Chart Analysis
st.subheader("Tornado Chart - Factor Sensitivity")

st.markdown("""
This chart shows how much each factor affects your CEFR when varied by ±20% from base assumptions.
""")

# Calculate sensitivities
parameters = []
low_values = []
high_values = []
parameter_labels = []

# 1. Total Assets
param = "Total Assets"
parameters.append(param)
parameter_labels.append(param)

# Low scenario (80% of assets)
low_household = household.model_copy(deep=True)
for asset in low_household.balance_sheet.assets:
    asset.value *= 0.8
low_result = compute_cefr(household=low_household, tax_model=tax_model)
low_values.append(low_result.cefr)

# High scenario (120% of assets)
high_household = household.model_copy(deep=True)
for asset in high_household.balance_sheet.assets:
    asset.value *= 1.2
high_result = compute_cefr(household=high_household, tax_model=tax_model)
high_values.append(high_result.cefr)

# 2. Annual Spending
param = "Annual Spending"
parameters.append(param)
parameter_labels.append(param)

# Low spending (80%)
low_household = household.model_copy(deep=True)
for liability in low_household.liabilities:
    liability.annual_amount *= 0.8
low_result = compute_cefr(household=low_household, tax_model=tax_model)
low_values.append(low_result.cefr)

# High spending (120%)
high_household = household.model_copy(deep=True)
for liability in high_household.liabilities:
    liability.annual_amount *= 1.2
high_result = compute_cefr(household=high_household, tax_model=tax_model)
high_values.append(high_result.cefr)

# 3. Discount Rate
param = "Discount Rate"
parameters.append(param)
parameter_labels.append(param)

low_result = compute_cefr(
    household=household,
    tax_model=tax_model,
    real_discount_rate=market_model.real_discount_rate * 0.5,
)
low_values.append(low_result.cefr)

high_result = compute_cefr(
    household=household,
    tax_model=tax_model,
    real_discount_rate=market_model.real_discount_rate * 1.5,
)
high_values.append(high_result.cefr)

# 4. Inflation
param = "Inflation"
parameters.append(param)
parameter_labels.append(param)

low_result = compute_cefr(
    household=household,
    tax_model=tax_model,
    base_inflation=market_model.inflation_mean * 0.6,
)
low_values.append(low_result.cefr)

high_result = compute_cefr(
    household=household,
    tax_model=tax_model,
    base_inflation=market_model.inflation_mean * 1.4,
)
high_values.append(high_result.cefr)

# 5. Tax Rate
param = "Tax Rate"
parameters.append(param)
parameter_labels.append(param)

from fundedness.models.tax import TaxModel

low_tax = TaxModel(
    federal_ordinary_rate=tax_model.federal_ordinary_rate * 0.8,
    federal_ltcg_rate=tax_model.federal_ltcg_rate * 0.8,
    state_ordinary_rate=tax_model.state_ordinary_rate * 0.8,
)
low_result = compute_cefr(household=household, tax_model=low_tax)
low_values.append(low_result.cefr)

high_tax = TaxModel(
    federal_ordinary_rate=min(tax_model.federal_ordinary_rate * 1.2, 0.5),
    federal_ltcg_rate=min(tax_model.federal_ltcg_rate * 1.2, 0.3),
    state_ordinary_rate=min(tax_model.state_ordinary_rate * 1.2, 0.15),
)
high_result = compute_cefr(household=household, tax_model=high_tax)
high_values.append(high_result.cefr)

# Create tornado chart
tornado_fig = create_tornado_chart(
    parameters=parameters,
    low_values=low_values,
    high_values=high_values,
    base_value=base_cefr,
    parameter_labels=parameter_labels,
    title="CEFR Sensitivity to Key Factors",
    value_label="CEFR",
)
st.plotly_chart(tornado_fig, use_container_width=True)

st.divider()

# Scenario Analysis
st.subheader("Scenario Comparison")

st.markdown("""
Compare your CEFR under different pre-defined scenarios.
""")

scenarios = {
    "Base Case": base_cefr,
}

# Best Case: Higher assets, lower spending, lower taxes
best_household = household.model_copy(deep=True)
for asset in best_household.balance_sheet.assets:
    asset.value *= 1.15
for liability in best_household.liabilities:
    liability.annual_amount *= 0.9
best_result = compute_cefr(household=best_household, tax_model=tax_model)
scenarios["Best Case"] = best_result.cefr

# Worst Case: Lower assets, higher spending
worst_household = household.model_copy(deep=True)
for asset in worst_household.balance_sheet.assets:
    asset.value *= 0.85
for liability in worst_household.liabilities:
    liability.annual_amount *= 1.1
worst_result = compute_cefr(household=worst_household, tax_model=tax_model)
scenarios["Worst Case"] = worst_result.cefr

# Market Crash: 40% drop in assets
crash_household = household.model_copy(deep=True)
for asset in crash_household.balance_sheet.assets:
    asset.value *= 0.6
crash_result = compute_cefr(household=crash_household, tax_model=tax_model)
scenarios["Market Crash (-40%)"] = crash_result.cefr

# High Inflation: Higher spending needs
inflation_household = household.model_copy(deep=True)
for liability in inflation_household.liabilities:
    liability.annual_amount *= 1.2
inflation_result = compute_cefr(
    household=inflation_household,
    tax_model=tax_model,
    base_inflation=0.04,
)
scenarios["High Inflation"] = inflation_result.cefr

# Longer Life: Extended planning horizon
if household.primary_member:
    long_household = household.model_copy(deep=True)
    long_household.members[0].life_expectancy = 100
    long_result = compute_cefr(household=long_household, tax_model=tax_model)
    scenarios["Live to 100"] = long_result.cefr

scenario_fig = create_scenario_comparison_chart(
    scenarios=list(scenarios.keys()),
    values=list(scenarios.values()),
    base_scenario="Base Case",
    title="CEFR Under Different Scenarios",
    value_label="CEFR",
)
st.plotly_chart(scenario_fig, use_container_width=True)

# Insights
st.divider()
st.subheader("Key Insights")

# Find most impactful factor
max_impact_idx = 0
max_impact = 0
for i, (low, high) in enumerate(zip(low_values, high_values)):
    impact = abs(high - low)
    if impact > max_impact:
        max_impact = impact
        max_impact_idx = i

st.markdown(f"""
Based on this analysis:

1. **Most Impactful Factor**: {parameter_labels[max_impact_idx]}
   - This factor has the largest effect on your CEFR when varied by ±20%

2. **Scenario Resilience**:
   - {"Your CEFR stays above 1.0 even in worst-case scenarios" if min(scenarios.values()) >= 1.0 else "Your CEFR falls below 1.0 in some scenarios - consider building more buffer"}

3. **Market Crash Impact**:
   - A 40% market decline would reduce your CEFR to {scenarios.get('Market Crash (-40%)', 0):.2f}

4. **Longevity Risk**:
   - {"Living to 100 would not significantly impact your funding" if scenarios.get('Live to 100', 0) >= 0.9 else "Living longer than expected could strain your resources"}
""")

# Interactive what-if
st.divider()
st.subheader("What-If Calculator")

col1, col2 = st.columns(2)

with col1:
    asset_change = st.slider(
        "Asset Value Change",
        min_value=-50,
        max_value=50,
        value=0,
        step=5,
        format="%d%%",
    )

    spending_change = st.slider(
        "Spending Change",
        min_value=-50,
        max_value=50,
        value=0,
        step=5,
        format="%d%%",
    )

with col2:
    whatif_household = household.model_copy(deep=True)

    for asset in whatif_household.balance_sheet.assets:
        asset.value *= (1 + asset_change / 100)

    for liability in whatif_household.liabilities:
        liability.annual_amount *= (1 + spending_change / 100)

    whatif_result = compute_cefr(household=whatif_household, tax_model=tax_model)

    st.metric(
        "What-If CEFR",
        f"{whatif_result.cefr:.2f}",
        delta=f"{whatif_result.cefr - base_cefr:+.2f}",
    )

    st.metric(
        "What-If Status",
        "Funded" if whatif_result.is_funded else "Underfunded",
    )
