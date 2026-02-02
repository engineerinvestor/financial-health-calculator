"""CEFR (Certainty-Equivalent Funded Ratio) calculation engine."""

from dataclasses import dataclass, field

from fundedness.liabilities import calculate_total_liability_pv
from fundedness.liquidity import get_liquidity_factor
from fundedness.models.assets import Asset, BalanceSheet
from fundedness.models.household import Household
from fundedness.models.liabilities import Liability
from fundedness.models.tax import TaxModel
from fundedness.risk import get_reliability_factor


@dataclass
class AssetHaircutDetail:
    """Detailed haircut breakdown for a single asset."""

    asset: Asset
    gross_value: float
    tax_rate: float
    after_tax_value: float
    liquidity_factor: float
    after_liquidity_value: float
    reliability_factor: float
    net_value: float

    @property
    def total_haircut(self) -> float:
        """Total haircut as decimal (1 - net/gross)."""
        if self.gross_value == 0:
            return 0.0
        return 1 - (self.net_value / self.gross_value)

    @property
    def tax_haircut(self) -> float:
        """Tax haircut amount in dollars."""
        return self.gross_value - self.after_tax_value

    @property
    def liquidity_haircut(self) -> float:
        """Liquidity haircut amount in dollars."""
        return self.after_tax_value - self.after_liquidity_value

    @property
    def reliability_haircut(self) -> float:
        """Reliability haircut amount in dollars."""
        return self.after_liquidity_value - self.net_value


@dataclass
class CEFRResult:
    """Complete CEFR calculation result with breakdown."""

    # Main ratio
    cefr: float

    # Numerator components
    gross_assets: float
    total_tax_haircut: float
    total_liquidity_haircut: float
    total_reliability_haircut: float
    net_assets: float

    # Denominator
    liability_pv: float

    # Detailed breakdowns
    asset_details: list[AssetHaircutDetail] = field(default_factory=list)

    @property
    def total_haircut(self) -> float:
        """Total haircut amount."""
        return self.total_tax_haircut + self.total_liquidity_haircut + self.total_reliability_haircut

    @property
    def haircut_percentage(self) -> float:
        """Total haircut as percentage of gross assets."""
        if self.gross_assets == 0:
            return 0.0
        return self.total_haircut / self.gross_assets

    @property
    def is_funded(self) -> bool:
        """Whether CEFR >= 1.0 (fully funded)."""
        return self.cefr >= 1.0

    @property
    def funding_gap(self) -> float:
        """Dollar gap if underfunded (positive = gap, negative = surplus)."""
        return self.liability_pv - self.net_assets

    def get_interpretation(self) -> str:
        """Get a human-readable interpretation of the CEFR."""
        if self.cefr >= 2.0:
            return "Excellent: Very well-funded with significant buffer"
        elif self.cefr >= 1.5:
            return "Strong: Well-funded with comfortable margin"
        elif self.cefr >= 1.0:
            return "Adequate: Fully funded but limited cushion"
        elif self.cefr >= 0.8:
            return "Marginal: Slightly underfunded, minor adjustments needed"
        elif self.cefr >= 0.5:
            return "Concerning: Significantly underfunded, action required"
        else:
            return "Critical: Severely underfunded, major changes needed"


def compute_asset_haircuts(
    asset: Asset,
    tax_model: TaxModel,
) -> AssetHaircutDetail:
    """Compute all haircuts for a single asset.

    Args:
        asset: The asset to analyze
        tax_model: Tax rate assumptions

    Returns:
        Detailed haircut breakdown
    """
    gross_value = asset.value

    # Step 1: Tax haircut
    cost_basis_ratio = None
    if asset.cost_basis is not None and asset.value > 0:
        cost_basis_ratio = asset.cost_basis / asset.value

    tax_rate = tax_model.get_effective_tax_rate(
        account_type=asset.account_type,
        cost_basis_ratio=cost_basis_ratio,
    )
    after_tax_value = gross_value * (1 - tax_rate)

    # Step 2: Liquidity haircut
    liquidity_factor = get_liquidity_factor(asset.liquidity_class)
    after_liquidity_value = after_tax_value * liquidity_factor

    # Step 3: Reliability haircut
    reliability_factor = get_reliability_factor(
        concentration_level=asset.concentration_level,
        asset_class=asset.asset_class,
    )
    net_value = after_liquidity_value * reliability_factor

    return AssetHaircutDetail(
        asset=asset,
        gross_value=gross_value,
        tax_rate=tax_rate,
        after_tax_value=after_tax_value,
        liquidity_factor=liquidity_factor,
        after_liquidity_value=after_liquidity_value,
        reliability_factor=reliability_factor,
        net_value=net_value,
    )


def compute_cefr(
    household: Household | None = None,
    balance_sheet: BalanceSheet | None = None,
    liabilities: list[Liability] | None = None,
    tax_model: TaxModel | None = None,
    planning_horizon: int | None = None,
    real_discount_rate: float = 0.02,
    base_inflation: float = 0.025,
) -> CEFRResult:
    """Compute the Certainty-Equivalent Funded Ratio (CEFR).

    CEFR = Σ(Asset × (1-τ) × λ × ρ) / PV(Liabilities)

    Where:
        τ = tax rate
        λ = liquidity factor
        ρ = reliability factor

    Args:
        household: Complete household model (alternative to separate components)
        balance_sheet: Asset holdings (if household not provided)
        liabilities: Future spending obligations (if household not provided)
        tax_model: Tax rate assumptions (defaults to TaxModel())
        planning_horizon: Years to plan for (defaults to household horizon or 30)
        real_discount_rate: Real discount rate for liability PV
        base_inflation: Base inflation assumption

    Returns:
        CEFRResult with complete breakdown
    """
    # Extract components from household or use provided values
    if household is not None:
        balance_sheet = household.balance_sheet
        liabilities = household.liabilities
        if planning_horizon is None:
            planning_horizon = household.planning_horizon
    else:
        if balance_sheet is None:
            balance_sheet = BalanceSheet()
        if liabilities is None:
            liabilities = []

    if planning_horizon is None:
        planning_horizon = 30

    if tax_model is None:
        tax_model = TaxModel()

    # Compute asset haircuts
    asset_details = [
        compute_asset_haircuts(asset, tax_model)
        for asset in balance_sheet.assets
    ]

    # Aggregate numerator
    gross_assets = sum(d.gross_value for d in asset_details)
    total_tax_haircut = sum(d.tax_haircut for d in asset_details)
    total_liquidity_haircut = sum(d.liquidity_haircut for d in asset_details)
    total_reliability_haircut = sum(d.reliability_haircut for d in asset_details)
    net_assets = sum(d.net_value for d in asset_details)

    # Compute liability PV (denominator)
    liability_pv, _ = calculate_total_liability_pv(
        liabilities=liabilities,
        planning_horizon=planning_horizon,
        real_discount_rate=real_discount_rate,
        base_inflation=base_inflation,
    )

    # Calculate CEFR
    if liability_pv == 0:
        cefr = float("inf") if net_assets > 0 else 0.0
    else:
        cefr = net_assets / liability_pv

    return CEFRResult(
        cefr=cefr,
        gross_assets=gross_assets,
        total_tax_haircut=total_tax_haircut,
        total_liquidity_haircut=total_liquidity_haircut,
        total_reliability_haircut=total_reliability_haircut,
        net_assets=net_assets,
        liability_pv=liability_pv,
        asset_details=asset_details,
    )
