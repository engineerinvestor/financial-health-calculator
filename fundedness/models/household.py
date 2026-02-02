"""Household and person models."""

from typing import Optional

from pydantic import BaseModel, Field, model_validator

from fundedness.models.assets import BalanceSheet
from fundedness.models.liabilities import Liability


class Person(BaseModel):
    """An individual person in the household."""

    name: str = Field(..., description="Person's name")
    age: int = Field(..., ge=0, le=120, description="Current age")
    retirement_age: Optional[int] = Field(
        default=None,
        ge=0,
        le=120,
        description="Expected retirement age (None if already retired)",
    )
    life_expectancy: int = Field(
        default=95,
        ge=0,
        le=120,
        description="Planning life expectancy",
    )
    social_security_age: int = Field(
        default=67,
        ge=62,
        le=70,
        description="Age to claim Social Security",
    )
    social_security_annual: float = Field(
        default=0,
        ge=0,
        description="Expected annual Social Security benefit at claiming age (today's dollars)",
    )
    pension_annual: float = Field(
        default=0,
        ge=0,
        description="Expected annual pension benefit (today's dollars)",
    )
    pension_start_age: Optional[int] = Field(
        default=None,
        ge=0,
        le=120,
        description="Age when pension payments begin",
    )
    is_primary: bool = Field(
        default=True,
        description="Whether this is the primary earner/planner",
    )

    @model_validator(mode="after")
    def validate_ages(self) -> "Person":
        """Validate age relationships."""
        if self.retirement_age is not None and self.retirement_age < self.age:
            # Already past retirement age, treat as retired
            self.retirement_age = None
        if self.life_expectancy < self.age:
            raise ValueError("Life expectancy must be greater than current age")
        return self

    @property
    def years_to_retirement(self) -> int:
        """Years until retirement (0 if already retired)."""
        if self.retirement_age is None:
            return 0
        return max(0, self.retirement_age - self.age)

    @property
    def years_in_retirement(self) -> int:
        """Expected years in retirement."""
        retirement_age = self.retirement_age or self.age
        return max(0, self.life_expectancy - retirement_age)

    @property
    def planning_horizon(self) -> int:
        """Total years in planning horizon."""
        return max(0, self.life_expectancy - self.age)


class Household(BaseModel):
    """A household unit for financial planning."""

    name: str = Field(
        default="My Household",
        description="Household name",
    )
    members: list[Person] = Field(
        default_factory=list,
        description="Household members",
    )
    balance_sheet: BalanceSheet = Field(
        default_factory=BalanceSheet,
        description="Household balance sheet",
    )
    liabilities: list[Liability] = Field(
        default_factory=list,
        description="Future spending obligations",
    )
    state: str = Field(
        default="CA",
        description="State of residence (for tax calculations)",
    )
    filing_status: str = Field(
        default="married_filing_jointly",
        description="Tax filing status",
    )

    @property
    def primary_member(self) -> Optional[Person]:
        """Get the primary household member."""
        for member in self.members:
            if member.is_primary:
                return member
        return self.members[0] if self.members else None

    @property
    def planning_horizon(self) -> int:
        """Planning horizon based on longest-lived member."""
        if not self.members:
            return 30  # Default
        return max(member.planning_horizon for member in self.members)

    @property
    def total_assets(self) -> float:
        """Total asset value."""
        return self.balance_sheet.total_value

    @property
    def essential_spending(self) -> float:
        """Total annual essential spending."""
        return sum(
            liability.annual_amount
            for liability in self.liabilities
            if liability.is_essential
        )

    @property
    def discretionary_spending(self) -> float:
        """Total annual discretionary spending."""
        return sum(
            liability.annual_amount
            for liability in self.liabilities
            if not liability.is_essential
        )

    @property
    def total_spending(self) -> float:
        """Total annual spending target."""
        return self.essential_spending + self.discretionary_spending
