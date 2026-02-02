"""Withdrawal strategy comparison API endpoints."""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from fundedness.models.market import MarketModel
from fundedness.models.simulation import SimulationConfig
from fundedness.withdrawals.comparison import compare_strategies
from fundedness.withdrawals.fixed_swr import FixedRealSWRPolicy, PercentOfPortfolioPolicy
from fundedness.withdrawals.guardrails import GuardrailsPolicy
from fundedness.withdrawals.rmd_style import RMDStylePolicy
from fundedness.withdrawals.vpw import VPWPolicy

router = APIRouter()


class StrategyConfig(BaseModel):
    """Configuration for a withdrawal strategy."""

    type: Literal["fixed_swr", "percent_portfolio", "guardrails", "vpw", "rmd_style"]
    withdrawal_rate: float | None = Field(default=None, ge=0.01, le=0.15)


class CompareRequest(BaseModel):
    """Request schema for strategy comparison."""

    initial_wealth: float = Field(..., gt=0)
    spending_floor: float | None = Field(default=None, ge=0)
    starting_age: int = Field(default=65, ge=50, le=90)
    stock_weight: float = Field(default=0.6, ge=0, le=1)
    n_simulations: int = Field(default=2500, ge=100, le=25000)
    n_years: int = Field(default=30, ge=1, le=50)
    strategies: list[StrategyConfig] = Field(
        default_factory=lambda: [
            StrategyConfig(type="fixed_swr"),
            StrategyConfig(type="guardrails"),
            StrategyConfig(type="vpw"),
        ]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "initial_wealth": 1000000,
                    "spending_floor": 30000,
                    "starting_age": 65,
                    "stock_weight": 0.6,
                    "strategies": [
                        {"type": "fixed_swr", "withdrawal_rate": 0.04},
                        {"type": "guardrails"},
                        {"type": "vpw"},
                    ],
                }
            ]
        }
    }


class StrategyMetrics(BaseModel):
    """Metrics for a single strategy."""

    name: str
    success_rate: float
    floor_breach_rate: float
    median_terminal_wealth: float
    median_initial_spending: float
    average_spending: float
    spending_volatility: float


class CompareResponse(BaseModel):
    """Response schema for strategy comparison."""

    strategies: list[StrategyMetrics]
    n_simulations: int
    n_years: int


def build_policy(config: StrategyConfig, spending_floor: float | None, starting_age: int):
    """Build a withdrawal policy from configuration."""
    rate = config.withdrawal_rate or 0.04

    match config.type:
        case "fixed_swr":
            return FixedRealSWRPolicy(withdrawal_rate=rate, floor_spending=spending_floor)
        case "percent_portfolio":
            return PercentOfPortfolioPolicy(withdrawal_rate=rate, floor_spending=spending_floor)
        case "guardrails":
            return GuardrailsPolicy(initial_rate=rate + 0.01, floor_spending=spending_floor)
        case "vpw":
            return VPWPolicy(starting_age=starting_age, floor_spending=spending_floor)
        case "rmd_style":
            return RMDStylePolicy(starting_age=starting_age, floor_spending=spending_floor)
        case _:
            raise ValueError(f"Unknown strategy type: {config.type}")


@router.post("/strategies", response_model=CompareResponse)
async def compare_strategies_endpoint(request: CompareRequest) -> CompareResponse:
    """Compare multiple withdrawal strategies.

    Runs the same market scenarios through different withdrawal strategies
    to show how each performs under identical conditions.
    """
    try:
        # Build policies
        policies = [
            build_policy(config, request.spending_floor, request.starting_age)
            for config in request.strategies
        ]

        # Build config
        config = SimulationConfig(
            n_simulations=request.n_simulations,
            n_years=request.n_years,
            random_seed=42,
            market_model=MarketModel(),
        )

        # Run comparison
        result = compare_strategies(
            policies=policies,
            initial_wealth=request.initial_wealth,
            config=config,
            stock_weight=request.stock_weight,
            starting_age=request.starting_age,
            spending_floor=request.spending_floor,
        )

        # Convert to response
        strategies = [
            StrategyMetrics(
                name=name,
                success_rate=metrics["success_rate"],
                floor_breach_rate=metrics["floor_breach_rate"],
                median_terminal_wealth=metrics["median_terminal_wealth"],
                median_initial_spending=metrics["median_initial_spending"],
                average_spending=metrics["average_spending"],
                spending_volatility=metrics["spending_volatility"],
            )
            for name, metrics in result.metrics.items()
        ]

        return CompareResponse(
            strategies=strategies,
            n_simulations=request.n_simulations,
            n_years=request.n_years,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
