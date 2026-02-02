# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python financial planning toolkit that implements:
- **CEFR (Certainty-Equivalent Funded Ratio)**: A fundedness metric that applies after-tax, liquidity, and risk haircuts to assets
- **Merton Optimal Policies**: Spending and asset allocation policies that maximize expected lifetime utility
- **Withdrawal Strategy Lab**: Comparison framework for withdrawal strategies (fixed SWR, guardrails, VPW, RMD-style, Merton optimal)

The project includes both a Python package (`fundedness/`) and a Streamlit web application (`streamlit_app/`).

## Development Status

This project is **actively developed** and published on PyPI as `fundedness`.

Current version: **0.2.x**

## Commands

- **Install**: `pip install fundedness` or `pip install "fundedness[all]"` for all extras
- **Testing**: `pytest` (runs 99+ tests)
- **Docs**: `mkdocs serve` (local) or auto-deployed to GitHub Pages
- **Streamlit**: `streamlit run streamlit_app/app.py`
- **API**: `uvicorn api.main:app --reload`

## Architecture

### Core Package Structure (`fundedness/`)

```
fundedness/
├── __init__.py          # Package exports
├── cefr.py              # CEFR ratio calculation with haircut breakdowns
├── liabilities.py       # Liability PV calculations with schedules
├── liquidity.py         # Liquidity factor adjustments
├── risk.py              # Reliability/concentration haircuts
├── simulate.py          # Monte Carlo engine with utility tracking
├── merton.py            # Merton optimal formulas (allocation, spending, CE return)
├── optimize.py          # Parametric policy optimization
├── policies.py          # Spending/allocation policy interface
├── models/              # Pydantic data models
│   ├── assets.py
│   ├── household.py
│   ├── liabilities.py
│   ├── market.py
│   ├── simulation.py
│   ├── tax.py
│   └── utility.py
├── withdrawals/         # Withdrawal strategy implementations
│   ├── base.py
│   ├── fixed_swr.py
│   ├── guardrails.py
│   ├── vpw.py
│   ├── rmd_style.py
│   ├── merton_optimal.py
│   └── comparison.py
├── allocation/          # Asset allocation strategies
│   ├── base.py
│   ├── constant.py
│   ├── glidepath.py
│   └── merton_optimal.py
└── viz/                 # Plotly visualizations
    ├── colors.py
    ├── fan_chart.py
    ├── waterfall.py
    ├── survival.py
    ├── comparison.py
    ├── optimal.py
    └── ...
```

### Data Models (Pydantic)

Key models: `Household`, `BalanceSheet`, `Asset`, `Liability`, `MarketModel`, `TaxModel`, `UtilityModel`, `SimulationConfig`

### Core Formulas

**CEFR Calculation:**
```
CEFR = Σ(Asset × (1-tax_rate) × liquidity_factor × reliability_factor) / PV(Liabilities)
```

**Merton Optimal Allocation:**
```
k* = (μ - r) / (γ × σ²)
```

**Merton Optimal Spending Rate:**
```
c* = rce - (rce - ρ) / γ
```

**CRRA Utility with Floor:**
```
u(C) = (C - F)^(1-γ) / (1-γ)  where C > F (subsistence floor)
```

## Key Concepts

- **Haircuts**: Three adjustments to assets—after-tax (τ), liquidity (λ), reliability (ρ)
- **Floor/Flex spending**: Essential spending floor vs adjustable discretionary
- **Time metrics**: Time-to-floor-breach, time-to-ruin, max spending drawdown
- **Confidence intervals**: Scenario percentiles (P10/P50/P90), not statistical CIs
- **Utility optimization**: Merton framework for optimal spending and allocation

## Default Haircut Assumptions

Liquidity: cash=1.0, taxable_index=0.95, retirement=0.85, home_equity=0.5, private_business=0.3
Reliability: diversified_bonds=0.95, diversified_equity=0.85, single_stock=0.60, startup=0.30

## Deployment

- **PyPI**: Published as `fundedness` - releases triggered by GitHub Release
- **Docs**: MkDocs Material deployed to GitHub Pages via `docs.yml` workflow
- **Web App**: Streamlit Cloud (free tier)
- **API**: FastAPI with endpoints in `api/`

## Visualization Standards

Use **Plotly** as the primary visualization library for beautiful, interactive charts:
- Clean, professional appearance with `template="plotly_white"`
- Interactive features: hover tooltips, zoom, pan
- Consistent color palette: blues (#3498db, #2980b9) for wealth, greens (#27ae60, #2ecc71) for spending/survival
- Fan charts with gradient opacity for percentile bands (P10-P90)
- Export capability to HTML/PNG for reports

## Documentation Notes

### LaTeX Equations in MkDocs

**Issue**: LaTeX equations using `$$...$$` syntax don't render in MkDocs Material.

**Solution**: Use `pymdownx.arithmatex` extension with MathJax:

1. In `mkdocs.yml`:
```yaml
markdown_extensions:
  - pymdownx.arithmatex:
      generic: true

extra_javascript:
  - javascripts/mathjax.js
  - https://unpkg.com/mathjax@3/es5/tex-mml-chtml.js
```

2. Create `docs/javascripts/mathjax.js`:
```javascript
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};
```

3. Use `\[...\]` for display math and `\(...\)` for inline math in markdown files.

## References

- Merton, R.C. (1969). Lifetime Portfolio Selection under Uncertainty. *The Review of Economics and Statistics*, 51(3), 247-257.
- Haghani, V. & White, J. (2023). *The Missing Billionaires: A Guide to Better Financial Decisions*. Wiley.
