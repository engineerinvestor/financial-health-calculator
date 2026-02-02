"""Reliability/risk factor mappings for CEFR calculations."""

from fundedness.models.assets import AssetClass, ConcentrationLevel

# Default reliability factors by concentration level
# These represent the certainty-equivalent haircut for concentration risk
DEFAULT_RELIABILITY_FACTORS: dict[ConcentrationLevel, float] = {
    ConcentrationLevel.DIVERSIFIED: 0.85,  # Broad market index
    ConcentrationLevel.SECTOR: 0.70,  # Sector concentration
    ConcentrationLevel.SINGLE_STOCK: 0.60,  # Individual company
    ConcentrationLevel.STARTUP: 0.30,  # Early-stage, high uncertainty
}

# Additional reliability adjustments by asset class
ASSET_CLASS_RELIABILITY: dict[AssetClass, float] = {
    AssetClass.CASH: 1.0,  # No reliability haircut for cash
    AssetClass.BONDS: 0.95,  # Slight credit/duration risk
    AssetClass.STOCKS: 1.0,  # Base reliability (modified by concentration)
    AssetClass.REAL_ESTATE: 0.90,  # Valuation uncertainty
    AssetClass.ALTERNATIVES: 0.80,  # Higher uncertainty
}


def get_reliability_factor(
    concentration_level: ConcentrationLevel,
    asset_class: AssetClass | None = None,
    custom_factors: dict[ConcentrationLevel, float] | None = None,
) -> float:
    """Get the reliability factor for an asset.

    The reliability factor combines concentration risk with asset class risk.

    Args:
        concentration_level: The concentration level of the asset
        asset_class: Optional asset class for additional adjustment
        custom_factors: Optional custom concentration factor overrides

    Returns:
        Reliability factor between 0 and 1
    """
    # Get concentration-based factor
    if custom_factors and concentration_level in custom_factors:
        concentration_factor = custom_factors[concentration_level]
    else:
        concentration_factor = DEFAULT_RELIABILITY_FACTORS.get(concentration_level, 1.0)

    # Apply asset class adjustment if provided
    if asset_class is not None:
        asset_adjustment = ASSET_CLASS_RELIABILITY.get(asset_class, 1.0)
        # Cash and bonds don't need concentration haircut
        if asset_class in (AssetClass.CASH, AssetClass.BONDS):
            return asset_adjustment
        return concentration_factor * asset_adjustment

    return concentration_factor


def get_all_reliability_factors(
    custom_factors: dict[ConcentrationLevel, float] | None = None,
) -> dict[ConcentrationLevel, float]:
    """Get all reliability factors with optional overrides.

    Args:
        custom_factors: Optional custom factor overrides

    Returns:
        Dictionary of concentration level to factor
    """
    factors = DEFAULT_RELIABILITY_FACTORS.copy()
    if custom_factors:
        factors.update(custom_factors)
    return factors
