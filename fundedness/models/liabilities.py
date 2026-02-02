"""Liability models for future spending obligations."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LiabilityType(str, Enum):
    """Type of liability/spending obligation."""

    ESSENTIAL_SPENDING = "essential_spending"  # Non-negotiable living expenses
    DISCRETIONARY_SPENDING = "discretionary_spending"  # Flexible lifestyle spending
    LEGACY_GOAL = "legacy_goal"  # Bequest target
    MORTGAGE = "mortgage"  # Home loan payments
    DEBT = "debt"  # Other debt obligations
    HEALTHCARE = "healthcare"  # Healthcare/long-term care costs
    TAXES = "taxes"  # Future tax obligations


class InflationLinkage(str, Enum):
    """How the liability is linked to inflation."""

    NONE = "none"  # Fixed nominal amount
    CPI = "cpi"  # Linked to Consumer Price Index
    WAGE = "wage"  # Linked to wage growth
    HEALTHCARE = "healthcare"  # Linked to healthcare inflation (typically higher)
    CUSTOM = "custom"  # Custom inflation rate


class Liability(BaseModel):
    """A future spending obligation or liability."""

    name: str = Field(..., description="Descriptive name for the liability")
    liability_type: LiabilityType = Field(
        default=LiabilityType.ESSENTIAL_SPENDING,
        description="Category of liability",
    )
    annual_amount: float = Field(
        ...,
        ge=0,
        description="Annual spending amount in today's dollars",
    )
    start_year: int = Field(
        default=0,
        ge=0,
        description="Years from now when liability begins (0 = now)",
    )
    end_year: Optional[int] = Field(
        default=None,
        ge=0,
        description="Years from now when liability ends (None = until death)",
    )
    inflation_linkage: InflationLinkage = Field(
        default=InflationLinkage.CPI,
        description="How the liability adjusts for inflation",
    )
    custom_inflation_rate: Optional[float] = Field(
        default=None,
        description="Custom inflation rate if inflation_linkage is CUSTOM (decimal)",
    )
    probability: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Probability this liability occurs (1.0 = certain)",
    )
    is_essential: bool = Field(
        default=True,
        description="Whether this is essential (floor) vs discretionary (flex) spending",
    )

    @property
    def duration_years(self) -> Optional[int]:
        """Duration of the liability in years, if end_year is specified."""
        if self.end_year is None:
            return None
        return self.end_year - self.start_year

    def get_inflation_rate(self, base_cpi: float = 0.025) -> float:
        """Get the effective inflation rate for this liability.

        Args:
            base_cpi: Base CPI inflation rate assumption

        Returns:
            Effective annual inflation rate as decimal
        """
        match self.inflation_linkage:
            case InflationLinkage.NONE:
                return 0.0
            case InflationLinkage.CPI:
                return base_cpi
            case InflationLinkage.WAGE:
                return base_cpi + 0.01  # Assume 1% real wage growth
            case InflationLinkage.HEALTHCARE:
                return base_cpi + 0.02  # Assume 2% excess healthcare inflation
            case InflationLinkage.CUSTOM:
                return self.custom_inflation_rate or base_cpi
