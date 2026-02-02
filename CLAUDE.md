# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python financial planning toolkit that implements:
- **CEFR (Certainty-Equivalent Funded Ratio)**: A fundedness metric that applies after-tax, liquidity, and risk haircuts to assets
- **Victor-style lifetime utility optimization**: Spending and asset allocation policies that maximize expected lifetime utility
- **Withdrawal Strategy Lab**: Comparison framework for withdrawal strategies (fixed SWR, guardrails, VPW, RMD-style)

The project includes both a Python package (`fundedness/`) and a Streamlit web application (`streamlit_app/`).

## Development Status

This project is in the **specification/planning phase**. The `background_information.md` file contains the complete design spec. No implementation code exists yet.

## Planned Commands

Once implemented, the project will use:
- **Package manager**: pip
- **Testing**: pytest (with property tests for monotonicity)
- **Docs**: MkDocs
- **CLI**: `fundedness cefr config.yaml`, `fundedness simulate config.yaml`, `fundedness policy-search config.yaml`
- **Streamlit**: `streamlit run streamlit_app/app.py`

## Architecture

### Core Package Structure (`fundedness/`)

```
fundedness/
├── cefr.py              # CEFR ratio calculation with haircut breakdowns
├── liabilities.py       # Liability PV calculations with schedules
├── taxes.py             # Tax modeling by account type
├── liquidity.py         # Liquidity factor adjustments
├── risk.py              # Reliability/concentration haircuts
├── markets.py           # Return/covariance/inflation assumptions
├── simulate.py          # Monte Carlo engine (time-to-floor, time-to-ruin)
├── utility.py           # CRRA utility with subsistence floor
├── policies.py          # Spending/allocation policy interface
├── optimize.py          # Parametric policy search (v0.4+)
├── withdrawals/         # Withdrawal strategy implementations
├── allocation/          # Glidepath strategies (constant, rising equity, bucket)
└── tax/strategy.py      # Tax-aware withdrawal sequencing
```

### Data Models (Pydantic)

Key models: `Household`, `BalanceSheet`, `Asset`, `Liability`, `MarketModel`, `TaxModel`, `UtilityModel`, `SimulationConfig`

### Core Formulas

**CEFR Calculation:**
```
CEFR = Σ(Asset × (1-tax_rate) × liquidity_factor × reliability_factor) / PV(Liabilities)
```

**CRRA Utility with Floor:**
```
u(C) = (C - F)^(1-γ) / (1-γ)  where C > F (subsistence floor)
```

## Development Tiers

1. **MVP (v0.1-0.3)**: CEFR + Monte Carlo runway with P10/P50/P90 bands
2. **v0.4-0.7**: Victor-style parametric policy search
3. **v1.0+**: Tax-aware account flows, Roth conversions

## Key Concepts

- **Haircuts**: Three adjustments to assets—after-tax (τ), liquidity (λ), reliability (ρ)
- **Floor/Flex spending**: Essential spending floor vs adjustable discretionary
- **Time metrics**: Time-to-floor-breach, time-to-ruin, max spending drawdown
- **Confidence intervals**: Scenario percentiles (P10/P50/P90), not statistical CIs

## Default Haircut Assumptions

Liquidity: cash=1.0, taxable_index=0.95, retirement=0.85, home_equity=0.5, private_business=0.3
Reliability: diversified_bonds=0.95, diversified_equity=0.85, single_stock=0.60, startup=0.30

## Deployment Preferences

- **Web App**: Deploy on Streamlit Cloud (free tier)
- **API**: Expose core functionality via a REST API (FastAPI recommended) for programmatic access
- **Tutorials**: Create Jupyter notebooks in `examples/` that run in Google Colab. Include working "Open in Colab" badge links in the README using the format:
  ```
  [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/engineerinvestor/financial-health-calculator/blob/main/examples/NOTEBOOK.ipynb)
  ```

## Visualization Standards

Use **Plotly** as the primary visualization library for beautiful, interactive charts:
- Clean, professional appearance with `template="plotly_white"`
- Interactive features: hover tooltips, zoom, pan
- Consistent color palette: blues (#3498db, #2980b9) for wealth, greens (#27ae60, #2ecc71) for spending/survival
- Fan charts with gradient opacity for percentile bands (P10-P90)
- Export capability to HTML/PNG for reports
