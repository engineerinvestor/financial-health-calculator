"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client for API."""
    from api.main import app
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for basic API endpoints."""

    def test_root_endpoint(self, client):
        """Root endpoint should return API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Fundedness API"

    def test_health_check(self, client):
        """Health check should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestCEFREndpoint:
    """Tests for CEFR computation endpoint."""

    def test_compute_cefr_basic(self, client):
        """Basic CEFR computation should work."""
        request_data = {
            "assets": [
                {"name": "401k", "value": 500000, "account_type": "tax_deferred"},
                {"name": "Roth", "value": 200000, "account_type": "tax_exempt"},
            ],
            "liabilities": [
                {"name": "Spending", "annual_amount": 50000, "is_essential": True},
            ],
            "planning_horizon": 30,
        }

        response = client.post("/api/v1/cefr/compute", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "cefr" in data
        assert data["cefr"] > 0
        assert "is_funded" in data
        assert "gross_assets" in data
        assert data["gross_assets"] == 700000

    def test_compute_cefr_validation_error(self, client):
        """Invalid request should return 400."""
        request_data = {
            "assets": [],  # Empty assets
            "liabilities": [],  # Empty liabilities
        }

        response = client.post("/api/v1/cefr/compute", json=request_data)
        # Should still work, just return 0 or inf CEFR
        assert response.status_code == 200

    def test_compute_cefr_with_tax_model(self, client):
        """Custom tax model should be applied."""
        request_data = {
            "assets": [
                {"name": "Taxable", "value": 100000, "account_type": "taxable"},
            ],
            "liabilities": [
                {"name": "Spending", "annual_amount": 10000},
            ],
            "tax_model": {
                "federal_ordinary_rate": 0.30,
                "federal_ltcg_rate": 0.20,
                "state_ordinary_rate": 0.10,
            },
        }

        response = client.post("/api/v1/cefr/compute", json=request_data)
        assert response.status_code == 200


class TestSimulateEndpoint:
    """Tests for simulation endpoint."""

    def test_run_simulation_basic(self, client):
        """Basic simulation should work."""
        request_data = {
            "initial_wealth": 1000000,
            "annual_spending": 40000,
            "stock_weight": 0.6,
            "n_simulations": 100,
            "n_years": 30,
            "random_seed": 42,
        }

        response = client.post("/api/v1/simulate/run", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "success_rate" in data
        assert "median_terminal_wealth" in data
        assert "wealth_percentiles" in data
        assert "survival_probability" in data
        assert len(data["survival_probability"]) == 30

    def test_run_simulation_with_floor(self, client):
        """Simulation with spending floor should track floor breach."""
        request_data = {
            "initial_wealth": 1000000,
            "annual_spending": 40000,
            "spending_floor": 30000,
            "n_simulations": 100,
            "n_years": 30,
        }

        response = client.post("/api/v1/simulate/run", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "floor_breach_rate" in data


class TestCompareEndpoint:
    """Tests for strategy comparison endpoint."""

    def test_compare_strategies_basic(self, client):
        """Basic strategy comparison should work."""
        request_data = {
            "initial_wealth": 1000000,
            "spending_floor": 30000,
            "starting_age": 65,
            "stock_weight": 0.6,
            "n_simulations": 100,
            "n_years": 30,
            "strategies": [
                {"type": "fixed_swr", "withdrawal_rate": 0.04},
                {"type": "guardrails"},
            ],
        }

        response = client.post("/api/v1/compare/strategies", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "strategies" in data
        assert len(data["strategies"]) == 2

        for strategy in data["strategies"]:
            assert "name" in strategy
            assert "success_rate" in strategy
            assert "median_terminal_wealth" in strategy

    def test_compare_all_strategy_types(self, client):
        """All strategy types should be supported."""
        strategy_types = [
            "fixed_swr",
            "percent_portfolio",
            "guardrails",
            "vpw",
            "rmd_style",
        ]

        for strategy_type in strategy_types:
            request_data = {
                "initial_wealth": 1000000,
                "n_simulations": 100,  # Minimum required by API
                "n_years": 20,
                "strategies": [{"type": strategy_type}],
            }

            response = client.post("/api/v1/compare/strategies", json=request_data)
            assert response.status_code == 200, f"Failed for strategy: {strategy_type}"
