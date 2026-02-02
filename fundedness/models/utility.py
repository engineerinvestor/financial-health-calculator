"""Utility model for lifetime utility optimization."""

import numpy as np
from pydantic import BaseModel, Field


class UtilityModel(BaseModel):
    """CRRA utility model with subsistence floor."""

    gamma: float = Field(
        default=3.0,
        gt=0,
        description="Coefficient of relative risk aversion (CRRA parameter)",
    )
    subsistence_floor: float = Field(
        default=30000,
        ge=0,
        description="Minimum annual spending floor in dollars",
    )
    bequest_weight: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Weight on bequest utility (0 = no bequest motive)",
    )
    time_preference: float = Field(
        default=0.02,
        ge=0,
        description="Pure rate of time preference (discount rate for utility)",
    )

    def utility(self, consumption: float) -> float:
        """Calculate CRRA utility of consumption.

        Args:
            consumption: Annual consumption in dollars

        Returns:
            Utility value (can be negative)

        Raises:
            ValueError: If consumption is below subsistence floor
        """
        excess = consumption - self.subsistence_floor

        if excess <= 0:
            # Below floor: large negative utility
            return -1e10

        if self.gamma == 1.0:
            # Log utility special case
            return np.log(excess)

        return (excess ** (1 - self.gamma)) / (1 - self.gamma)

    def marginal_utility(self, consumption: float) -> float:
        """Calculate marginal utility of consumption.

        Args:
            consumption: Annual consumption in dollars

        Returns:
            Marginal utility value
        """
        excess = consumption - self.subsistence_floor

        if excess <= 0:
            return 1e10  # Very high marginal utility when below floor

        return excess ** (-self.gamma)

    def inverse_marginal_utility(self, mu: float) -> float:
        """Calculate consumption from marginal utility (for optimization).

        Args:
            mu: Marginal utility value

        Returns:
            Consumption that produces this marginal utility
        """
        excess = mu ** (-1 / self.gamma)
        return excess + self.subsistence_floor

    def certainty_equivalent(
        self,
        consumption_samples: np.ndarray,
    ) -> float:
        """Calculate certainty equivalent consumption.

        The certainty equivalent is the guaranteed consumption that
        provides the same expected utility as the risky consumption stream.

        Args:
            consumption_samples: Array of consumption outcomes

        Returns:
            Certainty equivalent consumption value
        """
        # Calculate expected utility
        utilities = np.array([self.utility(c) for c in consumption_samples])
        expected_utility = np.mean(utilities)

        # Invert to find certainty equivalent
        if self.gamma == 1.0:
            return np.exp(expected_utility) + self.subsistence_floor

        # For CRRA: CE = (EU * (1-gamma))^(1/(1-gamma)) + floor
        ce_excess = (expected_utility * (1 - self.gamma)) ** (1 / (1 - self.gamma))
        return ce_excess + self.subsistence_floor

    def lifetime_utility(
        self,
        consumption_path: np.ndarray,
        survival_probabilities: np.ndarray | None = None,
    ) -> float:
        """Calculate discounted lifetime utility.

        Args:
            consumption_path: Array of annual consumption values
            survival_probabilities: Probability of being alive at each year (optional)

        Returns:
            Discounted expected lifetime utility
        """
        n_years = len(consumption_path)

        if survival_probabilities is None:
            survival_probabilities = np.ones(n_years)

        total_utility = 0.0
        for t, (consumption, survival_prob) in enumerate(
            zip(consumption_path, survival_probabilities)
        ):
            discount = (1 + self.time_preference) ** (-t)
            total_utility += discount * survival_prob * self.utility(consumption)

        return total_utility

    def risk_tolerance(self, wealth: float) -> float:
        """Calculate risk tolerance at a given wealth level.

        Risk tolerance = 1 / (gamma * wealth) for CRRA utility.

        Args:
            wealth: Current wealth level

        Returns:
            Risk tolerance as decimal
        """
        if wealth <= self.subsistence_floor:
            return 0.0  # No risk tolerance below floor

        excess_wealth = wealth - self.subsistence_floor
        return 1 / (self.gamma * excess_wealth) * excess_wealth
