"""Monte Carlo simulation API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from fundedness.models.market import MarketModel
from fundedness.models.simulation import SimulationConfig
from fundedness.simulate import run_simulation

router = APIRouter()


class MarketModelInput(BaseModel):
    """Input schema for market assumptions."""

    stock_return: float = Field(default=0.05, description="Expected real stock return")
    bond_return: float = Field(default=0.015, description="Expected real bond return")
    stock_volatility: float = Field(default=0.16, ge=0)
    bond_volatility: float = Field(default=0.06, ge=0)
    inflation_mean: float = Field(default=0.025, ge=0)
    use_fat_tails: bool = Field(default=False)


class SimulationRequest(BaseModel):
    """Request schema for Monte Carlo simulation."""

    initial_wealth: float = Field(..., gt=0, description="Starting portfolio value")
    annual_spending: float = Field(..., ge=0, description="Annual spending amount")
    stock_weight: float = Field(default=0.6, ge=0, le=1, description="Stock allocation")
    spending_floor: float | None = Field(default=None, ge=0, description="Minimum spending")
    n_simulations: int = Field(default=5000, ge=100, le=50000)
    n_years: int = Field(default=30, ge=1, le=60)
    random_seed: int | None = Field(default=None)
    market_model: MarketModelInput | None = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "initial_wealth": 1000000,
                    "annual_spending": 40000,
                    "stock_weight": 0.6,
                    "spending_floor": 30000,
                    "n_simulations": 5000,
                    "n_years": 30,
                }
            ]
        }
    }


class PercentileData(BaseModel):
    """Percentile time series data."""

    P10: list[float]
    P25: list[float]
    P50: list[float]
    P75: list[float]
    P90: list[float]


class SimulationResponse(BaseModel):
    """Response schema for simulation results."""

    success_rate: float
    floor_breach_rate: float
    median_terminal_wealth: float
    mean_terminal_wealth: float
    n_simulations: int
    n_years: int
    wealth_percentiles: PercentileData
    spending_percentiles: PercentileData | None = None
    survival_probability: list[float]


@router.post("/run", response_model=SimulationResponse)
async def run_simulation_endpoint(request: SimulationRequest) -> SimulationResponse:
    """Run a Monte Carlo retirement simulation.

    Simulates thousands of possible market scenarios to show the range
    of potential outcomes for your retirement portfolio.
    """
    try:
        # Build market model
        market_model = MarketModel()
        if request.market_model:
            market_model = MarketModel(
                stock_return=request.market_model.stock_return,
                bond_return=request.market_model.bond_return,
                stock_volatility=request.market_model.stock_volatility,
                bond_volatility=request.market_model.bond_volatility,
                inflation_mean=request.market_model.inflation_mean,
                use_fat_tails=request.market_model.use_fat_tails,
            )

        # Build config
        config = SimulationConfig(
            n_simulations=request.n_simulations,
            n_years=request.n_years,
            random_seed=request.random_seed,
            market_model=market_model,
        )

        # Run simulation
        result = run_simulation(
            initial_wealth=request.initial_wealth,
            annual_spending=request.annual_spending,
            config=config,
            stock_weight=request.stock_weight,
            spending_floor=request.spending_floor,
        )

        # Convert percentiles to response format
        wealth_percentiles = PercentileData(
            P10=result.wealth_percentiles.get("P10", []).tolist(),
            P25=result.wealth_percentiles.get("P25", []).tolist(),
            P50=result.wealth_percentiles.get("P50", []).tolist(),
            P75=result.wealth_percentiles.get("P75", []).tolist(),
            P90=result.wealth_percentiles.get("P90", []).tolist(),
        )

        spending_percentiles = None
        if result.spending_percentiles:
            spending_percentiles = PercentileData(
                P10=result.spending_percentiles.get("P10", []).tolist(),
                P25=result.spending_percentiles.get("P25", []).tolist(),
                P50=result.spending_percentiles.get("P50", []).tolist(),
                P75=result.spending_percentiles.get("P75", []).tolist(),
                P90=result.spending_percentiles.get("P90", []).tolist(),
            )

        return SimulationResponse(
            success_rate=result.success_rate,
            floor_breach_rate=result.floor_breach_rate,
            median_terminal_wealth=result.median_terminal_wealth,
            mean_terminal_wealth=result.mean_terminal_wealth,
            n_simulations=result.n_simulations,
            n_years=result.n_years,
            wealth_percentiles=wealth_percentiles,
            spending_percentiles=spending_percentiles,
            survival_probability=result.get_survival_probability().tolist(),
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
