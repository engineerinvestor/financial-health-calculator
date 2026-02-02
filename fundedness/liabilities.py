"""Liability present value calculations."""

from dataclasses import dataclass

import numpy as np

from fundedness.models.liabilities import Liability


@dataclass
class LiabilityPV:
    """Present value calculation result for a liability."""

    liability: Liability
    present_value: float
    nominal_total: float
    inflation_adjustment: float
    discount_factor: float


def calculate_annuity_pv(
    annual_payment: float,
    n_years: int,
    discount_rate: float,
    growth_rate: float = 0.0,
    start_year: int = 0,
) -> float:
    """Calculate present value of a growing annuity.

    Args:
        annual_payment: Annual payment amount (in today's dollars)
        n_years: Number of payment years
        discount_rate: Annual real discount rate (decimal)
        growth_rate: Annual growth rate of payments (decimal, e.g., for inflation)
        start_year: Years until first payment (0 = immediate)

    Returns:
        Present value of the annuity
    """
    if n_years <= 0:
        return 0.0

    if discount_rate == growth_rate:
        # Special case: growing perpetuity formula doesn't apply
        # Use simple sum
        pv = annual_payment * n_years / ((1 + discount_rate) ** start_year)
        return pv

    # Present value of growing annuity formula
    # PV = P * [1 - ((1+g)/(1+r))^n] / (r - g)
    # where P = first payment, g = growth rate, r = discount rate, n = years

    factor = ((1 + growth_rate) / (1 + discount_rate)) ** n_years
    if abs(discount_rate - growth_rate) < 1e-10:
        # Avoid division by near-zero
        pv_factor = n_years / (1 + discount_rate)
    else:
        pv_factor = (1 - factor) / (discount_rate - growth_rate)

    pv = annual_payment * pv_factor

    # Discount back to today if payments start in the future
    if start_year > 0:
        pv = pv / ((1 + discount_rate) ** start_year)

    return pv


def calculate_liability_pv(
    liability: Liability,
    planning_horizon: int,
    real_discount_rate: float = 0.02,
    base_inflation: float = 0.025,
) -> LiabilityPV:
    """Calculate present value of a single liability.

    Args:
        liability: The liability to value
        planning_horizon: Total planning horizon in years
        real_discount_rate: Real discount rate (decimal)
        base_inflation: Base CPI inflation assumption (decimal)

    Returns:
        LiabilityPV with calculation details
    """
    # Determine duration
    end_year = liability.end_year if liability.end_year is not None else planning_horizon
    n_years = max(0, end_year - liability.start_year)

    if n_years <= 0:
        return LiabilityPV(
            liability=liability,
            present_value=0.0,
            nominal_total=0.0,
            inflation_adjustment=1.0,
            discount_factor=1.0,
        )

    # Get inflation rate for this liability
    inflation_rate = liability.get_inflation_rate(base_inflation)

    # Calculate PV
    pv = calculate_annuity_pv(
        annual_payment=liability.annual_amount,
        n_years=n_years,
        discount_rate=real_discount_rate,
        growth_rate=inflation_rate - base_inflation,  # Real growth above CPI
        start_year=liability.start_year,
    )

    # Apply probability adjustment
    pv *= liability.probability

    # Calculate nominal total for reference
    nominal_total = liability.annual_amount * n_years

    # Calculate inflation adjustment factor
    avg_inflation_factor = (1 + inflation_rate) ** (n_years / 2)

    # Calculate average discount factor
    avg_discount_factor = 1 / ((1 + real_discount_rate) ** (liability.start_year + n_years / 2))

    return LiabilityPV(
        liability=liability,
        present_value=pv,
        nominal_total=nominal_total,
        inflation_adjustment=avg_inflation_factor,
        discount_factor=avg_discount_factor,
    )


def calculate_total_liability_pv(
    liabilities: list[Liability],
    planning_horizon: int,
    real_discount_rate: float = 0.02,
    base_inflation: float = 0.025,
) -> tuple[float, list[LiabilityPV]]:
    """Calculate total present value of all liabilities.

    Args:
        liabilities: List of liabilities to value
        planning_horizon: Total planning horizon in years
        real_discount_rate: Real discount rate (decimal)
        base_inflation: Base CPI inflation assumption (decimal)

    Returns:
        Tuple of (total_pv, list of LiabilityPV details)
    """
    details = [
        calculate_liability_pv(
            liability=liability,
            planning_horizon=planning_horizon,
            real_discount_rate=real_discount_rate,
            base_inflation=base_inflation,
        )
        for liability in liabilities
    ]

    total_pv = sum(d.present_value for d in details)

    return total_pv, details


def calculate_essential_liability_pv(
    liabilities: list[Liability],
    planning_horizon: int,
    real_discount_rate: float = 0.02,
    base_inflation: float = 0.025,
) -> float:
    """Calculate present value of essential (floor) liabilities only.

    Args:
        liabilities: List of all liabilities
        planning_horizon: Total planning horizon in years
        real_discount_rate: Real discount rate (decimal)
        base_inflation: Base CPI inflation assumption (decimal)

    Returns:
        Present value of essential liabilities
    """
    essential = [l for l in liabilities if l.is_essential]
    total_pv, _ = calculate_total_liability_pv(
        liabilities=essential,
        planning_horizon=planning_horizon,
        real_discount_rate=real_discount_rate,
        base_inflation=base_inflation,
    )
    return total_pv


def generate_liability_schedule(
    liabilities: list[Liability],
    n_years: int,
    base_inflation: float = 0.025,
) -> np.ndarray:
    """Generate year-by-year liability schedule.

    Args:
        liabilities: List of liabilities
        n_years: Number of years to project
        base_inflation: Base CPI inflation assumption

    Returns:
        Array of shape (n_years,) with total liability per year
    """
    schedule = np.zeros(n_years)

    for liability in liabilities:
        inflation_rate = liability.get_inflation_rate(base_inflation)
        end_year = min(
            liability.end_year if liability.end_year is not None else n_years,
            n_years,
        )

        for year in range(liability.start_year, end_year):
            if year < n_years:
                # Adjust for inflation from year 0
                inflation_factor = (1 + inflation_rate) ** year
                schedule[year] += liability.annual_amount * inflation_factor * liability.probability

    return schedule
