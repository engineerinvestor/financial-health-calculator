"""Tax model for after-tax calculations."""

from pydantic import BaseModel, Field

from fundedness.models.assets import AccountType


class TaxModel(BaseModel):
    """Tax rates and assumptions."""

    # Federal marginal rates
    federal_ordinary_rate: float = Field(
        default=0.24,
        ge=0,
        le=1,
        description="Federal marginal tax rate on ordinary income",
    )
    federal_ltcg_rate: float = Field(
        default=0.15,
        ge=0,
        le=1,
        description="Federal long-term capital gains rate",
    )
    federal_stcg_rate: float = Field(
        default=0.24,
        ge=0,
        le=1,
        description="Federal short-term capital gains rate (usually = ordinary)",
    )

    # State rates
    state_ordinary_rate: float = Field(
        default=0.093,
        ge=0,
        le=1,
        description="State marginal tax rate on ordinary income",
    )
    state_ltcg_rate: float = Field(
        default=0.093,
        ge=0,
        le=1,
        description="State long-term capital gains rate",
    )

    # Other
    niit_rate: float = Field(
        default=0.038,
        ge=0,
        le=1,
        description="Net Investment Income Tax rate (3.8%)",
    )
    niit_applies: bool = Field(
        default=True,
        description="Whether NIIT applies to this household",
    )

    # Cost basis assumptions
    default_cost_basis_ratio: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Default cost basis as fraction of value (for unrealized gains)",
    )

    @property
    def total_ordinary_rate(self) -> float:
        """Combined federal + state ordinary income tax rate."""
        return self.federal_ordinary_rate + self.state_ordinary_rate

    @property
    def total_ltcg_rate(self) -> float:
        """Combined federal + state + NIIT long-term capital gains rate."""
        base = self.federal_ltcg_rate + self.state_ltcg_rate
        if self.niit_applies:
            base += self.niit_rate
        return base

    def get_effective_tax_rate(
        self,
        account_type: AccountType,
        cost_basis_ratio: float | None = None,
    ) -> float:
        """Get the effective tax rate for withdrawals from an account type.

        Args:
            account_type: Type of account
            cost_basis_ratio: Cost basis as fraction of value (for taxable accounts)

        Returns:
            Effective tax rate as decimal (0-1)
        """
        match account_type:
            case AccountType.TAX_EXEMPT:
                # Roth: no tax on withdrawals
                return 0.0

            case AccountType.TAX_DEFERRED:
                # Traditional IRA/401k: taxed as ordinary income
                return self.total_ordinary_rate

            case AccountType.HSA:
                # HSA: no tax if used for medical expenses
                return 0.0

            case AccountType.TAXABLE:
                # Taxable: only gains are taxed
                if cost_basis_ratio is None:
                    cost_basis_ratio = self.default_cost_basis_ratio

                # Gains portion = (1 - cost_basis_ratio)
                gains_portion = 1 - cost_basis_ratio
                return gains_portion * self.total_ltcg_rate

    def get_haircut_by_account_type(self) -> dict[AccountType, float]:
        """Get tax haircut factors by account type.

        Returns:
            Dictionary mapping account type to (1 - tax_rate)
        """
        return {
            AccountType.TAXABLE: 1 - self.get_effective_tax_rate(AccountType.TAXABLE),
            AccountType.TAX_DEFERRED: 1 - self.get_effective_tax_rate(AccountType.TAX_DEFERRED),
            AccountType.TAX_EXEMPT: 1 - self.get_effective_tax_rate(AccountType.TAX_EXEMPT),
            AccountType.HSA: 1 - self.get_effective_tax_rate(AccountType.HSA),
        }
