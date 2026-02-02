"""Liquidity factor mappings for CEFR calculations."""

from fundedness.models.assets import LiquidityClass

# Default liquidity factors by class
# These represent the fraction of asset value that can be readily accessed
DEFAULT_LIQUIDITY_FACTORS: dict[LiquidityClass, float] = {
    LiquidityClass.CASH: 1.0,  # Immediately liquid
    LiquidityClass.TAXABLE_INDEX: 0.95,  # Small trading costs
    LiquidityClass.RETIREMENT: 0.85,  # Early withdrawal penalties, RMD constraints
    LiquidityClass.HOME_EQUITY: 0.50,  # HELOC access, selling costs
    LiquidityClass.PRIVATE_BUSINESS: 0.30,  # Very illiquid, long sale process
    LiquidityClass.RESTRICTED: 0.20,  # Vesting constraints, lockups
}


def get_liquidity_factor(
    liquidity_class: LiquidityClass,
    custom_factors: dict[LiquidityClass, float] | None = None,
) -> float:
    """Get the liquidity factor for an asset class.

    Args:
        liquidity_class: The liquidity classification of the asset
        custom_factors: Optional custom factor overrides

    Returns:
        Liquidity factor between 0 and 1
    """
    if custom_factors and liquidity_class in custom_factors:
        return custom_factors[liquidity_class]
    return DEFAULT_LIQUIDITY_FACTORS.get(liquidity_class, 1.0)


def get_all_liquidity_factors(
    custom_factors: dict[LiquidityClass, float] | None = None,
) -> dict[LiquidityClass, float]:
    """Get all liquidity factors with optional overrides.

    Args:
        custom_factors: Optional custom factor overrides

    Returns:
        Dictionary of liquidity class to factor
    """
    factors = DEFAULT_LIQUIDITY_FACTORS.copy()
    if custom_factors:
        factors.update(custom_factors)
    return factors
