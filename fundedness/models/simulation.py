"""Simulation configuration model."""

from typing import Literal

from pydantic import BaseModel, Field

from fundedness.models.market import MarketModel
from fundedness.models.tax import TaxModel
from fundedness.models.utility import UtilityModel


class SimulationConfig(BaseModel):
    """Configuration for Monte Carlo simulations."""

    # Simulation parameters
    n_simulations: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Number of Monte Carlo paths",
    )
    n_years: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Simulation horizon in years",
    )
    random_seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility (None = random)",
    )

    # Model components
    market_model: MarketModel = Field(
        default_factory=MarketModel,
        description="Market return and risk assumptions",
    )
    tax_model: TaxModel = Field(
        default_factory=TaxModel,
        description="Tax rate assumptions",
    )
    utility_model: UtilityModel = Field(
        default_factory=UtilityModel,
        description="Utility function parameters",
    )

    # Return generation
    return_model: Literal["lognormal", "t_distribution", "bootstrap"] = Field(
        default="lognormal",
        description="Model for generating returns",
    )

    # Output options
    percentiles: list[int] = Field(
        default=[10, 25, 50, 75, 90],
        description="Percentiles to report (0-100)",
    )
    track_spending: bool = Field(
        default=True,
        description="Track spending paths in simulation",
    )
    track_allocation: bool = Field(
        default=False,
        description="Track allocation changes over time",
    )

    # Performance
    use_vectorized: bool = Field(
        default=True,
        description="Use vectorized numpy operations for speed",
    )
    chunk_size: int = Field(
        default=1000,
        ge=100,
        description="Chunk size for memory-efficient simulation",
    )

    def get_percentile_labels(self) -> list[str]:
        """Get formatted percentile labels."""
        return [f"P{p}" for p in self.percentiles]
