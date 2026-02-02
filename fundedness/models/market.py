"""Market assumptions model."""

from typing import Optional

import numpy as np
from pydantic import BaseModel, Field, field_validator


class MarketModel(BaseModel):
    """Market return and risk assumptions."""

    # Expected returns (annual, real)
    stock_return: float = Field(
        default=0.05,
        description="Expected real return for stocks (decimal)",
    )
    bond_return: float = Field(
        default=0.015,
        description="Expected real return for bonds (decimal)",
    )
    cash_return: float = Field(
        default=0.0,
        description="Expected real return for cash (decimal)",
    )
    real_estate_return: float = Field(
        default=0.03,
        description="Expected real return for real estate (decimal)",
    )

    # Volatility (annual standard deviation)
    stock_volatility: float = Field(
        default=0.16,
        ge=0,
        description="Annual volatility for stocks (decimal)",
    )
    bond_volatility: float = Field(
        default=0.06,
        ge=0,
        description="Annual volatility for bonds (decimal)",
    )
    cash_volatility: float = Field(
        default=0.01,
        ge=0,
        description="Annual volatility for cash (decimal)",
    )
    real_estate_volatility: float = Field(
        default=0.12,
        ge=0,
        description="Annual volatility for real estate (decimal)",
    )

    # Correlations
    stock_bond_correlation: float = Field(
        default=0.0,
        ge=-1,
        le=1,
        description="Correlation between stocks and bonds",
    )
    stock_real_estate_correlation: float = Field(
        default=0.5,
        ge=-1,
        le=1,
        description="Correlation between stocks and real estate",
    )

    # Inflation
    inflation_mean: float = Field(
        default=0.025,
        description="Expected long-term inflation rate (decimal)",
    )
    inflation_volatility: float = Field(
        default=0.015,
        ge=0,
        description="Volatility of inflation (decimal)",
    )

    # Discount rate
    real_discount_rate: float = Field(
        default=0.02,
        description="Real discount rate for liability PV calculations (decimal)",
    )

    # Fat tails
    use_fat_tails: bool = Field(
        default=False,
        description="Use t-distribution for fatter tails",
    )
    degrees_of_freedom: int = Field(
        default=5,
        ge=3,
        description="Degrees of freedom for t-distribution (lower = fatter tails)",
    )

    @field_validator("degrees_of_freedom")
    @classmethod
    def validate_dof(cls, v: int) -> int:
        """Ensure degrees of freedom is reasonable."""
        if v < 3:
            raise ValueError("Degrees of freedom must be at least 3")
        return v

    def get_correlation_matrix(self) -> np.ndarray:
        """Get the correlation matrix for asset classes.

        Returns:
            4x4 correlation matrix for [stocks, bonds, cash, real_estate]
        """
        return np.array([
            [1.0, self.stock_bond_correlation, 0.0, self.stock_real_estate_correlation],
            [self.stock_bond_correlation, 1.0, 0.1, 0.2],
            [0.0, 0.1, 1.0, 0.0],
            [self.stock_real_estate_correlation, 0.2, 0.0, 1.0],
        ])

    def get_covariance_matrix(self) -> np.ndarray:
        """Get the covariance matrix for asset classes.

        Returns:
            4x4 covariance matrix for [stocks, bonds, cash, real_estate]
        """
        volatilities = np.array([
            self.stock_volatility,
            self.bond_volatility,
            self.cash_volatility,
            self.real_estate_volatility,
        ])
        corr = self.get_correlation_matrix()
        # Covariance = outer product of volatilities * correlation
        return np.outer(volatilities, volatilities) * corr

    def get_cholesky_decomposition(self) -> np.ndarray:
        """Get Cholesky decomposition for correlated returns generation.

        Returns:
            Lower triangular Cholesky matrix
        """
        cov = self.get_covariance_matrix()
        return np.linalg.cholesky(cov)

    def expected_portfolio_return(
        self,
        stock_weight: float,
        bond_weight: Optional[float] = None,
    ) -> float:
        """Calculate expected return for a portfolio.

        Args:
            stock_weight: Weight in stocks (0-1)
            bond_weight: Weight in bonds (remainder is cash if not specified)

        Returns:
            Expected annual real return
        """
        if bond_weight is None:
            bond_weight = 1 - stock_weight

        cash_weight = max(0, 1 - stock_weight - bond_weight)

        return (
            stock_weight * self.stock_return
            + bond_weight * self.bond_return
            + cash_weight * self.cash_return
        )

    def portfolio_volatility(
        self,
        stock_weight: float,
        bond_weight: Optional[float] = None,
    ) -> float:
        """Calculate portfolio volatility.

        Args:
            stock_weight: Weight in stocks (0-1)
            bond_weight: Weight in bonds (remainder is cash if not specified)

        Returns:
            Annual portfolio volatility
        """
        if bond_weight is None:
            bond_weight = 1 - stock_weight

        cash_weight = max(0, 1 - stock_weight - bond_weight)
        weights = np.array([stock_weight, bond_weight, cash_weight, 0])

        cov = self.get_covariance_matrix()
        portfolio_variance = weights @ cov @ weights

        return np.sqrt(portfolio_variance)
