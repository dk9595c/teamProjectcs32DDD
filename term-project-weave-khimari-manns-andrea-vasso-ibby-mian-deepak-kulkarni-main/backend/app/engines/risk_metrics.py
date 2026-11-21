
"""
Historical risk and risk-adjusted performance metrics for WEAVE.

This module calculates:
    1. Sharpe ratio
    2. Sortino ratio
    3. Historical Value at Risk (VaR)
    4. Expected Shortfall (CVaR)
    5. CAPM Beta
    6. Rolling volatility

Conventions:
    - Historical prices must be chronological.
    - Prices must be positive and finite.
    - Daily returns use adjusted closing prices when available.
    - One trading year contains approximately 252 sessions.
    - Returns and risk measures use decimal notation.
    - 0.05 represents 5%.
    - Risk ratios are annualized; VaR and ES are one-day measures.
    - Historical risk estimates do not guarantee future outcomes.
"""

import math
from collections.abc import Sequence

# Reuse the financial calculations implemented in Task C.
# This avoids duplicating foundational mathematical formulas.
from app.engines.calculations import (
    TRADING_DAYS_PER_YEAR,
    FinancialCalculationEngine,
    simple_returns,
    sample_std,
    sample_variance,
    sample_covariance,
)


def _validate_annual_rate(rate: float, name: str) -> None:
    """
    Validate an effective annual return or target rate.

    An annual rate must be:
        - Numeric, excluding booleans.
        - Finite (not NaN or infinity).
        - Greater than -100%.

    The -100% limit ensures that the conversion from annual
    to daily compounded rates remains mathematically valid.
    """

    if isinstance(rate, bool) or not isinstance(rate, (int, float)):
        raise TypeError(f"{name} must be numeric")

    if not math.isfinite(rate) or rate <= -1:
        raise ValueError(
            f"{name} must be finite and greater than -1"
        )


def _validate_confidence(confidence: float) -> None:
    """
    Validate the confidence level used in VaR and ES.

    Example:
        0.95 represents 95% confidence.

    The value must be strictly between 0 and 1.
    """

    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
    ):
        raise TypeError("confidence must be numeric")

    if not math.isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError(
            "confidence must be finite and between 0 and 1 (exclusive)"
        )


def _validated_returns(prices: Sequence[float]) -> list[float]:
    """
    Generate daily returns with additional safety checks.

    Reuses simple_returns() from the core calculation engine.

    Additional checks:
        - Reject boolean price values.
        - Reject nonfinite returns caused by numerical overflow.
    """

    # Python treats True and False as subclasses of int.
    # They should not be accepted as stock prices.
    if any(isinstance(price, bool) for price in prices):
        raise TypeError("boolean values are not valid prices")

    # The shared helper validates positive finite prices
    # and requires at least two price observations.
    returns = simple_returns(prices)

    # Extreme price ratios may overflow even when both
    # individual input prices are finite.
    if not all(math.isfinite(r) for r in returns):
        raise ValueError(
            "price ratios produced non-finite returns"
        )

    return returns


class RiskMetricsEngine:
    """
    Calculate historical investment risk and performance measures.

    Ratios such as Sharpe and Sortino compare returns
    against different definitions of risk.

    VaR and Expected Shortfall estimate historical losses.

    CAPM Beta measures sensitivity to market returns.

    Rolling volatility illustrates how risk changes over time.
    """

    def __init__(self):
        # Preserve access to the original calculation engine
        # for compatibility with other WEAVE components.
        self.calculations = FinancialCalculationEngine()

    def sharpe_ratio(
        self,
        prices: Sequence[float],
        risk_free_rate: float
    ) -> float | None:
        """
        Calculate the annualized Sharpe ratio.

        Formula:
            Sharpe = ((Mean Daily Return - Daily Risk-Free Rate)
                      / Daily Standard Deviation) * sqrt(252)

        The Sharpe ratio measures excess return per unit
        of total return volatility.

        Args:
            prices:
                Chronological historical prices.

            risk_free_rate:
                Effective annual risk-free rate.
                Example: 0.02 means 2%.

        Returns:
            Annualized Sharpe ratio.
            None if insufficient data or zero volatility.
        """

        # Ensure the risk-free rate can be converted
        # into an equivalent daily rate.
        _validate_annual_rate(risk_free_rate, "risk_free_rate")

        # Three prices produce two daily returns,
        # which is the minimum for sample standard deviation.
        if len(prices) < 3:
            return None

        returns = _validated_returns(prices)

        # Calculate daily sample volatility.
        daily_std = sample_std(returns)

        if not math.isfinite(daily_std):
            raise ValueError("volatility is not finite")

        # Zero volatility makes the Sharpe denominator zero.
        # Returning zero would incorrectly imply zero performance.
        if daily_std == 0:
            return None

        # Convert the annual effective risk-free rate
        # to an equivalent daily compounded rate.
        #
        # rf_daily = (1 + rf_annual)^(1/252) - 1
        daily_rf = (
            (1 + risk_free_rate) ** (1 / TRADING_DAYS_PER_YEAR)
            - 1
        )

        # Average historical daily return.
        mean_daily = sum(returns) / len(returns)

        # Calculate and annualize excess return per unit of risk.
        return (
            (mean_daily - daily_rf)
            / daily_std
            * math.sqrt(TRADING_DAYS_PER_YEAR)
        )

    def sortino_ratio(
        self,
        prices: Sequence[float],
        target_return: float
    ) -> float | None:
        """
        Calculate the annualized Sortino ratio.

        Formula:
            Sortino = ((Mean Daily Return - Daily Target Return)
                       / Downside Deviation) * sqrt(252)

        Unlike Sharpe, Sortino focuses on returns below
        a minimum acceptable target rather than total volatility.

        Downside deviation:
            sqrt(mean(min(0, return - target)^2))

        The mean includes ALL daily observations,
        including days with no downside deviation.

        Args:
            prices:
                Historical price observations.

            target_return:
                Effective annual minimum acceptable return.
                Example: 0.03 represents 3% annually.

        Returns:
            Annualized Sortino ratio.
            None if insufficient data or zero downside deviation.
        """

        # Validate the annual target before performing calculations.
        _validate_annual_rate(target_return, "target_return")

        if len(prices) < 3:
            return None

        returns = _validated_returns(prices)

        # Convert annual target return to daily compounded target.
        daily_target = (
            (1 + target_return) ** (1 / TRADING_DAYS_PER_YEAR)
            - 1
        )

        # Calculate squared shortfalls from the target.
        #
        # A return above target contributes zero downside risk.
        # A return below target contributes a squared shortfall.
        downside_mean_square = sum(
            min(0.0, r - daily_target) ** 2
            for r in returns
        ) / len(returns)

        # Convert mean squared shortfall to downside deviation.
        downside_dev = math.sqrt(downside_mean_square)

        if not math.isfinite(downside_dev):
            raise ValueError(
                "downside deviation is not finite"
            )

        # If no returns fall below target, downside deviation
        # is zero and the ratio cannot be calculated.
        if downside_dev == 0:
            return None

        mean_daily = sum(returns) / len(returns)

        # Annualize the daily Sortino ratio.
        return (
            (mean_daily - daily_target)
            / downside_dev
            * math.sqrt(TRADING_DAYS_PER_YEAR)
        )

    def historical_var(
        self,
        prices: Sequence[float],
        confidence: float = 0.95
    ) -> float:
        """
        Calculate one-day historical Value at Risk (VaR).

        Loss formula:
            Loss = -Daily Return

        At 95% confidence, VaR estimates the 95th
        percentile of the historical loss distribution.

        IMPORTANT:
            VaR is a loss threshold, not the maximum
            possible loss or a guarantee.

        Example:
            VaR = 0.04

            This represents an estimated 4% one-day
            loss threshold at the specified confidence.

        Returns:
            Nonnegative VaR as a decimal.

        Quantile convention:
            Linear interpolation between ascending
            ordered loss observations.
        """

        _validate_confidence(confidence)

        returns = _validated_returns(prices)

        # At least two returns are required by this implementation.
        if len(returns) < 2:
            raise ValueError(
                "VaR needs at least 2 daily returns"
            )

        # Convert returns to losses:
        # -10% return becomes +10% loss.
        losses = [-r for r in returns]

        # CORRECTION:
        # Sort losses in ASCENDING order.
        #
        # The original implementation sorted losses descending,
        # causing a 95th-percentile calculation to select
        # an observation near the smallest losses.
        losses.sort()

        # Calculate the fractional quantile position.
        position = confidence * (len(losses) - 1)

        # Identify neighboring observations.
        lower = math.floor(position)
        upper = math.ceil(position)

        # Calculate interpolation weight.
        fraction = position - lower

        # Interpolate the historical loss threshold.
        threshold = (
            losses[lower] * (1 - fraction)
            + losses[upper] * fraction
        )

        # Report loss magnitude, floored at zero.
        #
        # If all historical returns were positive,
        # the estimated positive-loss threshold is zero.
        return max(0.0, threshold)

    def expected_shortfall(
        self,
        prices: Sequence[float],
        confidence: float = 0.95
    ) -> float:
        """
        Calculate one-day historical Expected Shortfall (ES).

        Also called Conditional Value at Risk (CVaR).

        ES estimates the average loss in the worst
        (1 - confidence) fraction of observations.

        Example:
            confidence = 0.95

            Analyze the worst 5% of historical losses.

        Returns:
            Nonnegative Expected Shortfall as a decimal.

        Estimator:
            Empirical upper-tail average using fractional
            weighting at the tail boundary.

        NOTE:
            This estimator and the interpolated VaR quantile
            can differ slightly in small historical samples.
        """

        # CORRECTION:
        # Validate confidence, which the original implementation
        # did not do.
        _validate_confidence(confidence)

        returns = _validated_returns(prices)

        if len(returns) < 2:
            raise ValueError(
                "ES needs at least 2 daily returns"
            )

        # Convert daily returns to historical losses.
        #
        # Sort descending so the largest losses appear first.
        losses_desc = sorted(
            (-r for r in returns),
            reverse=True
        )

        # Calculate the number of observations represented
        # by the worst tail of the empirical distribution.
        #
        # Example:
        # 100 observations at 95% confidence -> 5 observations.
        #
        # 30 observations at 95% confidence -> 1.5 observations.
        tail_mass = (
            (1 - confidence)
            * len(losses_desc)
        )

        # Separate the tail into whole and fractional observations.
        whole_count = math.floor(tail_mass)
        fraction = tail_mass - whole_count

        # Include all observations completely inside the tail.
        total_tail_loss = sum(
            losses_desc[:whole_count]
        )

        # CORRECTION:
        # Instead of rounding upward and assigning full weight
        # to the next observation, include only the fraction
        # needed to complete the requested tail.
        if fraction > 0:
            total_tail_loss += (
                fraction * losses_desc[whole_count]
            )

        # Compute the weighted average of worst-tail losses.
        #
        # This is a historical estimate. With small datasets,
        # the result is highly sensitive to individual observations.
        return max(
            0.0,
            total_tail_loss / tail_mass
        )

    def capm_beta(
        self,
        asset_prices: Sequence[float],
        market_prices: Sequence[float]
    ) -> float | None:
        """
        Calculate CAPM beta relative to a market benchmark.

        Formula:
            Beta = Cov(Asset Returns, Market Returns)
                   / Var(Market Returns)

        Interpretation:
            Beta = 1:
                Similar directional sensitivity to the market.

            Beta > 1:
                Greater historical sensitivity to market movements.

            0 < Beta < 1:
                Lower historical sensitivity to market movements.

            Beta < 0:
                Historically negative market sensitivity.

        Args:
            asset_prices:
                Asset's chronological historical prices.

            market_prices:
                Benchmark's chronological historical prices.

        Returns:
            Beta coefficient.
            None if insufficient observations or zero
            benchmark variance.

        IMPORTANT:
            Both price series must already be aligned by date.
            Equal lengths alone do not establish date alignment.
        """

        # Both datasets must represent paired observations.
        if len(asset_prices) != len(market_prices):
            raise ValueError(
                "Asset and market prices must have matching lengths"
            )

        # Need at least two paired daily returns.
        if len(asset_prices) < 3:
            return None

        # Convert both price series into daily returns.
        asset_returns = _validated_returns(asset_prices)
        market_returns = _validated_returns(market_prices)

        # Calculate sample variance of benchmark returns.
        market_variance = sample_variance(market_returns)

        if not math.isfinite(market_variance):
            raise ValueError(
                "market variance is not finite"
            )

        # A market with zero return variance creates
        # an undefined beta denominator.
        if market_variance == 0:
            return None

        # Calculate sample covariance between the asset
        # and benchmark return series.
        covariance = sample_covariance(
            asset_returns,
            market_returns
        )

        if not math.isfinite(covariance):
            raise ValueError(
                "asset-market covariance is not finite"
            )

        # Beta measures the ratio of comovement
        # to the benchmark's own return variance.
        return covariance / market_variance

    def rolling_volatility(
        self,
        prices: Sequence[float],
        window: int = 21
    ) -> list[float]:
        """
        Calculate annualized volatility over rolling windows.

        Rolling formula:
            Rolling Volatility =
                SampleStd(Recent Daily Returns) * sqrt(252)

        Example:
            window = 21

            Calculate volatility over each trailing
            21-return window, approximately one month.

        Args:
            prices:
                Chronological historical prices.

            window:
                Number of DAILY RETURNS per window,
                rather than number of price observations.

        Returns:
            List of annualized rolling volatilities.

        Note:
            A window of 21 returns requires 22 prices.
            If insufficient data exists for a complete
            window, the result is an empty list.
        """

        # Reject invalid, noninteger, and boolean window sizes.
        if (
            isinstance(window, bool)
            or not isinstance(window, int)
            or window < 2
        ):
            raise ValueError(
                "window must be an integer of at least 2"
            )

        # Convert historical prices to daily returns.
        returns = _validated_returns(prices)

        results = []

        # Start after collecting the first complete window.
        #
        # Each subsequent iteration moves forward
        # by one daily return observation.
        for end in range(window, len(returns) + 1):

            # Select the trailing return window.
            trailing = returns[
                end - window:end
            ]

            # Calculate annualized volatility for this window.
            annual_std = (
                sample_std(trailing)
                * math.sqrt(TRADING_DAYS_PER_YEAR)
            )

            if not math.isfinite(annual_std):
                raise ValueError(
                    "rolling volatility is not finite"
                )

            # Record volatility for the completed window.
            results.append(annual_std)

        return results
