"""FastAPI REST API for the fundedness package."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import cefr, compare, simulate

app = FastAPI(
    title="Fundedness API",
    description="""
    A REST API for financial planning calculations including:
    - CEFR (Certainty-Equivalent Funded Ratio) calculations
    - Monte Carlo retirement simulations
    - Withdrawal strategy comparisons
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cefr.router, prefix="/api/v1/cefr", tags=["CEFR"])
app.include_router(simulate.router, prefix="/api/v1/simulate", tags=["Simulation"])
app.include_router(compare.router, prefix="/api/v1/compare", tags=["Comparison"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Fundedness API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "cefr": "/api/v1/cefr/compute",
            "simulate": "/api/v1/simulate/run",
            "compare": "/api/v1/compare/strategies",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
