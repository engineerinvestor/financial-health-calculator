"""CEFR calculation API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from fundedness.cefr import CEFRResult, compute_cefr
from fundedness.models.assets import (
    AccountType,
    Asset,
    AssetClass,
    BalanceSheet,
    ConcentrationLevel,
    LiquidityClass,
)
from fundedness.models.liabilities import InflationLinkage, Liability, LiabilityType
from fundedness.models.tax import TaxModel

router = APIRouter()


class AssetInput(BaseModel):
    """Input schema for an asset."""

    name: str = Field(..., description="Asset name")
    value: float = Field(..., ge=0, description="Current market value")
    account_type: AccountType = Field(default=AccountType.TAXABLE)
    asset_class: AssetClass = Field(default=AssetClass.STOCKS)
    liquidity_class: LiquidityClass = Field(default=LiquidityClass.TAXABLE_INDEX)
    concentration_level: ConcentrationLevel = Field(default=ConcentrationLevel.DIVERSIFIED)
    cost_basis: float | None = Field(default=None, ge=0)


class LiabilityInput(BaseModel):
    """Input schema for a liability."""

    name: str = Field(..., description="Liability name")
    annual_amount: float = Field(..., ge=0, description="Annual spending amount")
    liability_type: LiabilityType = Field(default=LiabilityType.ESSENTIAL_SPENDING)
    start_year: int = Field(default=0, ge=0)
    end_year: int | None = Field(default=None, ge=0)
    inflation_linkage: InflationLinkage = Field(default=InflationLinkage.CPI)
    is_essential: bool = Field(default=True)


class TaxModelInput(BaseModel):
    """Input schema for tax assumptions."""

    federal_ordinary_rate: float = Field(default=0.24, ge=0, le=1)
    federal_ltcg_rate: float = Field(default=0.15, ge=0, le=1)
    state_ordinary_rate: float = Field(default=0.093, ge=0, le=1)


class CEFRRequest(BaseModel):
    """Request schema for CEFR calculation."""

    assets: list[AssetInput] = Field(..., description="List of assets")
    liabilities: list[LiabilityInput] = Field(..., description="List of liabilities/spending")
    planning_horizon: int = Field(default=30, ge=1, le=100)
    real_discount_rate: float = Field(default=0.02, ge=-0.05, le=0.15)
    base_inflation: float = Field(default=0.025, ge=0, le=0.15)
    tax_model: TaxModelInput | None = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "assets": [
                        {"name": "401k", "value": 500000, "account_type": "tax_deferred"},
                        {"name": "Roth IRA", "value": 200000, "account_type": "tax_exempt"},
                        {"name": "Taxable", "value": 300000, "account_type": "taxable"},
                    ],
                    "liabilities": [
                        {"name": "Living Expenses", "annual_amount": 60000, "is_essential": True},
                        {"name": "Travel", "annual_amount": 15000, "is_essential": False},
                    ],
                    "planning_horizon": 30,
                }
            ]
        }
    }


class AssetHaircutResponse(BaseModel):
    """Response schema for asset haircut details."""

    name: str
    gross_value: float
    tax_rate: float
    after_tax_value: float
    liquidity_factor: float
    after_liquidity_value: float
    reliability_factor: float
    net_value: float
    total_haircut: float


class CEFRResponse(BaseModel):
    """Response schema for CEFR calculation."""

    cefr: float
    is_funded: bool
    interpretation: str
    gross_assets: float
    net_assets: float
    liability_pv: float
    funding_gap: float
    total_tax_haircut: float
    total_liquidity_haircut: float
    total_reliability_haircut: float
    haircut_percentage: float
    asset_details: list[AssetHaircutResponse]


@router.post("/compute", response_model=CEFRResponse)
async def compute_cefr_endpoint(request: CEFRRequest) -> CEFRResponse:
    """Compute the CEFR (Certainty-Equivalent Funded Ratio).

    The CEFR measures how well your assets can cover planned spending after
    accounting for taxes, liquidity constraints, and concentration risk.
    """
    try:
        # Convert input to domain models
        assets = [
            Asset(
                name=a.name,
                value=a.value,
                account_type=a.account_type,
                asset_class=a.asset_class,
                liquidity_class=a.liquidity_class,
                concentration_level=a.concentration_level,
                cost_basis=a.cost_basis,
            )
            for a in request.assets
        ]

        liabilities = [
            Liability(
                name=l.name,
                annual_amount=l.annual_amount,
                liability_type=l.liability_type,
                start_year=l.start_year,
                end_year=l.end_year,
                inflation_linkage=l.inflation_linkage,
                is_essential=l.is_essential,
            )
            for l in request.liabilities
        ]

        balance_sheet = BalanceSheet(assets=assets)

        tax_model = TaxModel()
        if request.tax_model:
            tax_model = TaxModel(
                federal_ordinary_rate=request.tax_model.federal_ordinary_rate,
                federal_ltcg_rate=request.tax_model.federal_ltcg_rate,
                state_ordinary_rate=request.tax_model.state_ordinary_rate,
            )

        # Compute CEFR
        result = compute_cefr(
            balance_sheet=balance_sheet,
            liabilities=liabilities,
            tax_model=tax_model,
            planning_horizon=request.planning_horizon,
            real_discount_rate=request.real_discount_rate,
            base_inflation=request.base_inflation,
        )

        # Convert to response
        asset_details = [
            AssetHaircutResponse(
                name=d.asset.name,
                gross_value=d.gross_value,
                tax_rate=d.tax_rate,
                after_tax_value=d.after_tax_value,
                liquidity_factor=d.liquidity_factor,
                after_liquidity_value=d.after_liquidity_value,
                reliability_factor=d.reliability_factor,
                net_value=d.net_value,
                total_haircut=d.total_haircut,
            )
            for d in result.asset_details
        ]

        return CEFRResponse(
            cefr=result.cefr,
            is_funded=result.is_funded,
            interpretation=result.get_interpretation(),
            gross_assets=result.gross_assets,
            net_assets=result.net_assets,
            liability_pv=result.liability_pv,
            funding_gap=result.funding_gap,
            total_tax_haircut=result.total_tax_haircut,
            total_liquidity_haircut=result.total_liquidity_haircut,
            total_reliability_haircut=result.total_reliability_haircut,
            haircut_percentage=result.haircut_percentage,
            asset_details=asset_details,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
