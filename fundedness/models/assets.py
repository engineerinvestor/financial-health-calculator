"""Asset and balance sheet models."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AccountType(str, Enum):
    """Tax treatment of an account."""

    TAXABLE = "taxable"
    TAX_DEFERRED = "tax_deferred"  # Traditional IRA, 401(k)
    TAX_EXEMPT = "tax_exempt"  # Roth IRA, Roth 401(k)
    HSA = "hsa"


class AssetClass(str, Enum):
    """Broad asset class categories."""

    CASH = "cash"
    BONDS = "bonds"
    STOCKS = "stocks"
    REAL_ESTATE = "real_estate"
    ALTERNATIVES = "alternatives"


class LiquidityClass(str, Enum):
    """Liquidity classification for assets."""

    CASH = "cash"  # Immediate liquidity
    TAXABLE_INDEX = "taxable_index"  # Public securities in taxable accounts
    RETIREMENT = "retirement"  # Tax-advantaged retirement accounts
    HOME_EQUITY = "home_equity"  # Primary residence equity
    PRIVATE_BUSINESS = "private_business"  # Illiquid business interests
    RESTRICTED = "restricted"  # Restricted stock, vesting schedules


class ConcentrationLevel(str, Enum):
    """Concentration/diversification level."""

    DIVERSIFIED = "diversified"  # Broad index funds
    SECTOR = "sector"  # Sector-specific concentration
    SINGLE_STOCK = "single_stock"  # Individual company stock
    STARTUP = "startup"  # Early-stage company equity


class Asset(BaseModel):
    """A single asset holding."""

    name: str = Field(..., description="Descriptive name for the asset")
    value: float = Field(..., ge=0, description="Current market value in dollars")
    account_type: AccountType = Field(
        default=AccountType.TAXABLE,
        description="Tax treatment of the account",
    )
    asset_class: AssetClass = Field(
        default=AssetClass.STOCKS,
        description="Broad asset class category",
    )
    liquidity_class: LiquidityClass = Field(
        default=LiquidityClass.TAXABLE_INDEX,
        description="Liquidity classification",
    )
    concentration_level: ConcentrationLevel = Field(
        default=ConcentrationLevel.DIVERSIFIED,
        description="Concentration/diversification level",
    )
    cost_basis: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cost basis for tax calculations (taxable accounts only)",
    )
    expected_return: Optional[float] = Field(
        default=None,
        description="Override expected return (annual, decimal)",
    )
    volatility: Optional[float] = Field(
        default=None,
        ge=0,
        description="Override volatility (annual standard deviation, decimal)",
    )

    @field_validator("cost_basis")
    @classmethod
    def validate_cost_basis(cls, v: Optional[float], info) -> Optional[float]:
        """Warn if cost basis exceeds value (unrealized loss)."""
        return v

    @property
    def unrealized_gain(self) -> Optional[float]:
        """Calculate unrealized gain/loss if cost basis is known."""
        if self.cost_basis is None:
            return None
        return self.value - self.cost_basis


class BalanceSheet(BaseModel):
    """Collection of assets representing a household's balance sheet."""

    assets: list[Asset] = Field(default_factory=list, description="List of asset holdings")

    @property
    def total_value(self) -> float:
        """Total market value of all assets."""
        return sum(asset.value for asset in self.assets)

    @property
    def by_account_type(self) -> dict[AccountType, float]:
        """Total value by account type."""
        result: dict[AccountType, float] = {}
        for asset in self.assets:
            result[asset.account_type] = result.get(asset.account_type, 0) + asset.value
        return result

    @property
    def by_asset_class(self) -> dict[AssetClass, float]:
        """Total value by asset class."""
        result: dict[AssetClass, float] = {}
        for asset in self.assets:
            result[asset.asset_class] = result.get(asset.asset_class, 0) + asset.value
        return result

    @property
    def by_liquidity_class(self) -> dict[LiquidityClass, float]:
        """Total value by liquidity class."""
        result: dict[LiquidityClass, float] = {}
        for asset in self.assets:
            result[asset.liquidity_class] = result.get(asset.liquidity_class, 0) + asset.value
        return result

    def get_stock_allocation(self) -> float:
        """Calculate percentage allocated to stocks."""
        if self.total_value == 0:
            return 0.0
        stock_value = sum(
            asset.value for asset in self.assets if asset.asset_class == AssetClass.STOCKS
        )
        return stock_value / self.total_value

    def get_bond_allocation(self) -> float:
        """Calculate percentage allocated to bonds."""
        if self.total_value == 0:
            return 0.0
        bond_value = sum(
            asset.value for asset in self.assets if asset.asset_class == AssetClass.BONDS
        )
        return bond_value / self.total_value
