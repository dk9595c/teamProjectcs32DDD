
"""
WEAVE stock screening and ranking utilities.

This module filters stocks using financial metrics calculated
by the shared calculation and risk engines.

Conventions:
    - Historical prices are chronological and date-aligned.
    - Returns, volatility and drawdown use decimal fractions.
    - Missing historical metrics are represented by None.
    - The composite score is an experimental heuristic, not
      a validated investment rating or prediction.
"""

import math
from collections.abc import Sequence

from app.engines.calculations import (
    SIX_MONTH_TRADING_DAYS,
    FinancialCalculationEngine,
    validate_prices,
)
from app.engines.risk_metrics import RiskMetricsEngine


def _finite_number(value: float, name: str) -> float:
    """Validate a finite number, rejecting booleans."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
    ):
        raise TypeError(f"{name} must be numeric")

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")

    return float(value)


class StockScreen:
    """Filter and score equities using shared financial metrics."""

    def __init__(self):
        # Reuse the mathematical implementations from Task C.
        self.calculations = FinancialCalculationEngine()
        self.risk = RiskMetricsEngine()

    def filter_by_price(
        self,
        prices: Sequence[float],
        min_price: float = 1.0,
        max_price: float = float("inf")
    ) -> bool:
        """
        Check whether the latest price is inside a price range.

        The lower and upper limits are inclusive.
        An empty series returns False.
        """

        min_price = _finite_number(min_price, "min_price")

        # Permit positive infinity as an unlimited upper bound.
        if max_price == float("inf"):
            max_price = float("inf")
        else:
            max_price = _finite_number(max_price, "max_price")

        if min_price <= 0 or max_price < min_price:
            raise ValueError("Invalid price range")

        if len(prices) == 0:
            return False

        # Validate the whole input rather than trusting only
        # the last observation.
        valid_prices = validate_prices(prices)

        return min_price <= valid_prices[-1] <= max_price

    def filter_by_volatility(
        self,
        prices: Sequence[float],
        max_volatility: float = 1.0
    ) -> bool:
        """
        Filter by annualized historical volatility.

        Example:
            max_volatility=0.30 allows volatility up to 30%.

        At least three prices are required to calculate
        sample volatility from two daily returns.
        """

        limit = _finite_number(
            max_volatility, "max_volatility"
        )

        if limit < 0:
            raise ValueError(
                "max_volatility must be nonnegative"
            )

        if len(prices) < 3:
            return False

        # Reuse Task C instead of duplicating the formula.
        volatility = self.calculations.annualized_volatility(
            prices
        )

        if not math.isfinite(volatility):
            raise ValueError("Calculated volatility is not finite")

        return volatility <= limit

    def filter_by_momentum(
        self,
        prices: Sequence[float],
        min_momentum: float = 0.0,
        lookback: int = SIX_MONTH_TRADING_DAYS
    ) -> bool:
        """
        Filter stocks by trailing momentum.

        Formula:
            Momentum = Latest Price / Lookback Price - 1

        The default lookback is 126 trading intervals.
        """

        threshold = _finite_number(
            min_momentum, "min_momentum"
        )

        if (
            isinstance(lookback, bool)
            or not isinstance(lookback, int)
            or lookback < 1
        ):
            raise ValueError(
                "lookback must be a positive integer"
            )

        if len(prices) < lookback + 1:
            return False

        momentum = self.calculations.six_month_momentum(
            prices, lookback
        )

        return momentum >= threshold

    def score_stock(
        self,
        prices: Sequence[float],
        benchmark_prices: Sequence[float] | None = None
    ) -> dict:
        """
        Calculate a stock's metrics and experimental score.

        The score combines:
            + 30% cumulative return contribution
            + 15% six-month momentum contribution
            - 25% annualized volatility contribution
            - 20% maximum drawdown contribution
            + Optional beta-based adjustment

        IMPORTANT:
            These coefficients are heuristic design choices.
            They are NOT empirically calibrated.

            The score is not a probability, percentile, or
            standardized 0-100 investment rating.

        Returns:
            Dictionary containing calculated metrics and score.

            Insufficient history produces None for metrics
            requiring more observations.

            Invalid supplied prices raise an error.
        """

        # Require at least one valid price, then compute only
        # metrics supported by the available history.
        valid_prices = validate_prices(prices, minimum=1)

        metrics = {
            "cumulative_return": None,
            "annualized_volatility": None,
            "momentum_6m": None,
            "max_drawdown": None,
            "beta": None,
            "score": None,
        }

        # Cumulative return requires at least two prices.
        if len(valid_prices) >= 2:
            metrics["cumulative_return"] = (
                self.calculations.cumulative_return(
                    valid_prices
                )
            )

        # Annualized sample volatility requires three prices.
        if len(valid_prices) >= 3:
            metrics["annualized_volatility"] = (
                self.calculations.annualized_volatility(
                    valid_prices
                )
            )

        # Six-month momentum requires 127 price observations.
        if len(valid_prices) >= SIX_MONTH_TRADING_DAYS + 1:
            metrics["momentum_6m"] = (
                self.calculations.six_month_momentum(
                    valid_prices,
                    lookback=SIX_MONTH_TRADING_DAYS
                )
            )

        # One price is sufficient to define zero drawdown.
        metrics["max_drawdown"] = (
            self.calculations.maximum_drawdown(
                valid_prices
            )
        )

        # Calculate beta only when benchmark data is provided.
        #
        # Equal-length arrays must ALSO represent identical
        # trading dates. Task B must ensure this alignment.
        if benchmark_prices is not None:
            valid_benchmark = validate_prices(
                benchmark_prices, minimum=1
            )

            if len(valid_benchmark) != len(valid_prices):
                raise ValueError(
                    "Asset and benchmark histories must align"
                )

            if len(valid_prices) >= 3:
                metrics["beta"] = self.risk.capm_beta(
                    valid_prices, valid_benchmark
                )

        # Do not manufacture a zero momentum or zero
        # volatility value when the history is insufficient.
        required = (
            "cumulative_return",
            "annualized_volatility",
            "momentum_6m",
            "max_drawdown",
        )

        # A full composite score requires all core metrics.
        if any(metrics[key] is None for key in required):
            return metrics

        # Apply the existing heuristic coefficients.
        score = (
            0.30 * metrics["cumulative_return"]
            + 0.15 * metrics["momentum_6m"]
            - 0.25 * metrics["annualized_volatility"]
            - 0.20 * metrics["max_drawdown"]
        )

        # Beta is optional. If unavailable, no adjustment
        # is applied rather than assuming beta equals 1.
        if metrics["beta"] is not None:
            beta_adjustment = (
                1.0 if metrics["beta"] <= 1.2 else -0.5
            )
            score += 0.10 * beta_adjustment

        if not math.isfinite(score):
            raise ValueError("Composite score is not finite")

        metrics["score"] = score

        return metrics
