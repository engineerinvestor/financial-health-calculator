# Installation

## Quick Install

Install the package from PyPI:

```bash
pip install fundedness
```

## Optional Dependencies

The package has several optional dependency groups:

### Streamlit App

For the interactive web interface:

```bash
pip install fundedness[streamlit]
```

### FastAPI Backend

For the REST API:

```bash
pip install fundedness[api]
```

### Documentation

For building documentation locally:

```bash
pip install fundedness[docs]
```

### Development

For development and testing:

```bash
pip install fundedness[dev]
```

### All Dependencies

Install everything:

```bash
pip install fundedness[all]
```

## Development Setup

Clone the repository and install in editable mode:

```bash
git clone https://github.com/engineerinvestor/financial-health-calculator.git
cd financial-health-calculator
pip install -e ".[dev]"
```

## Requirements

- Python 3.10 or higher
- NumPy >= 1.24.0
- Pandas >= 2.0.0
- Pydantic >= 2.0.0
- Plotly >= 5.18.0
- SciPy >= 1.11.0

## Verifying Installation

After installation, verify it works:

```python
from fundedness import compute_cefr
print("Installation successful!")
```
