
"""
Core financial calculation engine for WEAVE.

This module provides reusable mathematical functions for analyzing
historical stock prices and calculating fundamental financial metrics.

The engine is independent of stock-data APIs and databases.
Other backend services should supply validated, chronological prices.

Conventions:
    - Prices must be positive and finite.
    - Returns are decimals unless explicitly stated otherwise.
    - 0.10 represents a 10% return.
    - Trading year = 252 trading days.
    - Six months = approximately 126 trading days.
    - Annualization assumes daily trading observations.
"""

import math
from collections.abc import Sequence


# Standard number of trading days in a financial year.
# Used to annualize daily volatility and other risk statistics.
TRADING_DAYS_PER_YEAR = 252

# Approximate number of trading days in six months.
# Used as the default lookback for momentum calculations.
SIX_MONTH_TRADING_DAYS = 126


def validate_prices(
    prices: Sequence[float],
    minimum: int = 1
) -> list[float]:
    """
    Validate a historical price series.

    Checks:
        1. The series contains enough observations.
        2. Every observation is numeric.
        3. Every price is positive.
        4. No price is NaN or infinite.

    Returns:
        A new list containing the validated prices.

    REVIEW:
        The returned list is a mutable copy, not an immutable one.
        A tuple would be immutable if that behavior were required.
    """

    # Ensure enough observations exist for the requested calculation.
    if len(prices) < minimum:
        raise ValueError(
            f"Need at least {minimum} prices, got {len(prices)}"
        )

    # Check each price before allowing mathematical operations.
    for price in prices:

        # Reject values that are not integers or floating-point numbers.
        #
        # REVIEW:
        # Python considers bool a subclass of int.
        # This currently means True may be accepted as price 1.
        # Explicitly reject bool if strict numeric validation is desired.
        if not isinstance(price, (int, float)):
            raise TypeError(
                f"All prices must be numeric, got {type(price)}"
            )

        # NaN and infinity can corrupt mathematical results.
        # Zero and negative prices are invalid for this engine.
        if math.isnan(price) or math.isinf(price) or price <= 0:
            raise ValueError(
                f"All prices must be positive and finite, got {price}"
            )

    # Return a separate list so the original input is not modified.
    #
    # Note: The caller can still modify this returned list.
    return list(prices)


def simple_returns(
    prices: Sequence[float]
) -> list[float]:
    """
    Calculate arithmetic returns between consecutive prices.

    Formula:
        r(t) = P(t) / P(t-1) - 1

    Example:
        Prices = [100, 110, 121]
        Returns = [0.10, 0.10]

    Returns:
        List of daily returns expressed as decimals.
    """

    # At least two prices are required to calculate one return.
    prices = validate_prices(prices, minimum=2)

    returns = []

    # Start at index 1 because each return requires a previous price.
    for i in range(1, len(prices)):

        # Compare the current price to the previous observation.
        daily_return = prices[i] / prices[i - 1] - 1

        # Store the calculated return without modifying prices.
        returns.append(daily_return)

    # The resulting list contains one fewer observation than prices.
    return returns


def log_returns(
    prices: Sequence[float]
) -> list[float]:
    """
    Calculate continuously compounded logarithmic returns.

    Formula:
        g(t) = ln(P(t) / P(t-1))

    Log returns are additive across consecutive time periods
    and are useful for certain financial models and simulations.

    Returns:
        List of logarithmic returns expressed as decimals.
    """

    prices = validate_prices(prices, minimum=2)

    returns = []

    for i in range(1, len(prices)):

        # Calculate the ratio between consecutive prices.
        # Apply the natural logarithm to obtain log return.
        returns.append(
            math.log(prices[i] / prices[i - 1])
        )

    # REVIEW:
    # For extreme floating-point price ratios, division could
    # underflow to zero or overflow. Using the difference of
    # logarithms can improve numerical robustness:
    #
    # math.log(prices[i]) - math.log(prices[i - 1])

    return returns


def sample_variance(
    values: Sequence[float]
) -> float:
    """
    Calculate sample variance for a numerical dataset.

    Formula:
        s^2 = SUM((x - mean)^2) / (n - 1)

    Sample variance measures how widely observations
    are distributed around their arithmetic mean.

    Returns:
        Variance expressed in squared units.
    """

    # Sample variance requires at least two observations.
    if len(values) < 2:
        raise ValueError(
            "Need at least 2 observations for sample variance"
        )

    # Calculate the arithmetic mean.
    mean = sum(values) / len(values)

    # Measure the squared distance of each value from the mean.
    squared_deviations = sum(
        (x - mean) ** 2 for x in values
    )

    # Divide by n - 1 using the sample variance convention.
    #
    # REVIEW:
    # This function does not currently validate NaN, infinity,
    # or nonnumeric inputs in the supplied values.
    return squared_deviations / (len(values) - 1)


def sample_std(
    values: Sequence[float]
) -> float:
    """
    Calculate sample standard deviation.

    Formula:
        s = sqrt(SUM((x - mean)^2) / (n - 1))

    Standard deviation measures variability in the same
    units as the original observations.

    Returns:
        Sample standard deviation.
    """

    if len(values) < 2:
        raise ValueError(
            "Need at least 2 observations for sample std"
        )

    mean = sum(values) / len(values)

    squared_deviations = sum(
        (x - mean) ** 2 for x in values
    )

    # Standard deviation is the square root of variance.
    #
    # REVIEW:
    # This duplicates the calculation in sample_variance().
    # Consider reusing that function to avoid maintaining
    # the same formula in two different locations.
    return math.sqrt(
        squared_deviations / (len(values) - 1)
    )


def sample_covariance(
    x_values: Sequence[float],
    y_values: Sequence[float]
) -> float:
    """
    Calculate sample covariance between two datasets.

    Formula:
        Cov(X,Y) =
            SUM((X - mean_X)(Y - mean_Y)) / (n - 1)

    Interpretation:
        Positive covariance:
            The series generally move together.

        Negative covariance:
            The series generally move in opposite directions.

        Zero covariance:
            No linear comovement is detected.

    This function will be useful for:
        - CAPM beta
        - Portfolio covariance matrices
        - Portfolio risk calculations

    Returns:
        Sample covariance.
    """

    # Both datasets must contain the same number of observations.
    if len(x_values) != len(y_values):
        raise ValueError(
            "X and Y must have the same length"
        )

    if len(x_values) < 2:
        raise ValueError(
            "Need at least 2 observations for sample covariance"
        )

    n = len(x_values)

    # Calculate the average of each dataset independently.
    mean_x = sum(x_values) / n
    mean_y = sum(y_values) / n

    # Multiply paired deviations from their respective means.
    cov = sum(
        (x_values[i] - mean_x)
        * (y_values[i] - mean_y)
        for i in range(n)
    )

    # REVIEW:
    # Matching lengths do not guarantee matching dates.
    # Task B must align asset and benchmark observations
    # before calculating their covariance.
    #
    # Nonfinite input values should also be rejected.
    return cov / (n - 1)


class FinancialCalculationEngine:
    """
    Calculate foundational financial metrics from historical prices.

    This class performs mathematical analysis only.

    It does not:
        - Download market data.
        - Connect to external APIs.
        - Execute trades.
        - Predict future stock prices.

    Its methods can be reused by WEAVE's screening,
    portfolio, backtesting, and risk analysis components.
    """

    def cumulative_return(
        self,
        prices: Sequence[float]
    ) -> float:
        """
        Calculate cumulative return from first to last price.

        Formula:
            R = (P_end / P_start) - 1

        Example:
            Prices = [100, 110, 121]
            Return = 0.21, or 21%

        Returns:
            Cumulative return as a decimal.
        """

        prices = validate_prices(prices, minimum=2)

        # Record the beginning and ending prices.
        start_price = prices[0]
        end_price = prices[-1]

        # Compare ending wealth to starting wealth.
        # Subtract 1 to isolate the investment return.
        return end_price / start_price - 1

    def percentage_price_change(
        self,
        old_price: float,
        new_price: float
    ) -> float:
        """
        Calculate percentage price change between two observations.

        Formula:
            Percentage Change =
                ((New Price - Old Price) / Old Price) * 100

        Example:
            Old Price = 100
            New Price = 110
            Result = 10.0

        Returns:
            Percentage change in percentage units,
            unlike other metrics that return decimals.
        """

        # Both inputs must be numeric.
        if (
            not isinstance(old_price, (int, float))
            or not isinstance(new_price, (int, float))
        ):
            raise TypeError(
                "Both prices must be numeric"
            )

        # Zero prices would cause invalid divisions.
        # Negative prices are also disallowed.
        if old_price <= 0 or new_price <= 0:
            raise ValueError(
                "Both prices must be positive"
            )

        # Prevent undefined or infinite financial results.
        if (
            math.isnan(old_price)
            or math.isnan(new_price)
            or math.isinf(old_price)
            or math.isinf(new_price)
        ):
            raise ValueError(
                "Both prices must be finite"
            )

        # Calculate the absolute price movement.
        difference = new_price - old_price

        # Divide by the original price, then convert to percent.
        #
        # REVIEW:
        # This method duplicates parts of validate_prices().
        # A shared validation helper could improve consistency.
        return (difference / old_price) * 100

    def six_month_momentum(
        self,
        prices: Sequence[float],
        lookback: int = 126
    ) -> float:
        """
        Calculate historical momentum over a lookback period.

        Formula:
            Momentum = (P_today / P_past) - 1

        Default:
            126 trading intervals, approximately six months.

        Interpretation:
            Positive value = price increased.
            Negative value = price decreased.

        Returns:
            Momentum as a decimal.
        """

        # A lookback of 126 requires at least 127 prices.
        # This includes both the historical and latest prices.
        #
        # REVIEW:
        # Explicitly require lookback to be an integer >= 1.
        # Zero and negative lookbacks currently are not rejected.
        prices = validate_prices(
            prices,
            minimum=lookback + 1
        )

        # Most recent available price.
        latest_price = prices[-1]

        # Price exactly 'lookback' trading intervals earlier.
        historical_price = prices[-(lookback + 1)]

        # Calculate historical percentage appreciation.
        #
        # NOTE:
        # Momentum measures past price behavior.
        # It does not guarantee future price appreciation.
        return latest_price / historical_price - 1

    def annualized_volatility(
        self,
        prices: Sequence[float]
    ) -> float:
        """
        Calculate annualized historical return volatility.

        Daily Return:
            r(t) = P(t) / P(t-1) - 1

        Annualized Volatility:
            sigma_annual = sigma_daily * sqrt(252)

        The calculation uses the sample standard deviation
        of daily arithmetic returns.

        Returns:
            Annualized volatility as a decimal.
        """

        # Need at least three prices to obtain two daily returns.
        # Two returns are the minimum for sample standard deviation.
        prices = validate_prices(prices, minimum=3)

        # Convert historical price observations into daily returns.
        returns = simple_returns(prices)

        # Calculate variability in daily returns.
        daily_volatility = sample_std(returns)

        # Annualize daily volatility using square-root-of-time scaling.
        #
        # ASSUMPTION:
        # This scaling is approximate when returns exhibit serial
        # correlation or changing volatility.
        #
        # REVIEW:
        # simple_returns() validates the prices again.
        # The duplicate validation could be avoided later.
        return (
            daily_volatility
            * math.sqrt(TRADING_DAYS_PER_YEAR)
        )

    def maximum_drawdown(
        self,
        prices: Sequence[float]
    ) -> float:
        """
        Calculate the largest historical peak-to-trough decline.

        Running Peak:
            H(t) = max(P(0), ..., P(t))

        Drawdown:
            D(t) = 1 - P(t) / H(t)

        Maximum Drawdown:
            MDD = max(D(t))

        Example:
            Prices = [100, 120, 90, 110]
            MDD = 0.25, or 25%

        Returns:
            Maximum drawdown as a nonnegative decimal.
        """

        # A single valid price has zero drawdown.
        prices = validate_prices(prices, minimum=1)

        # Start with the first observation as the running peak.
        running_peak = prices[0]

        # Initially, no decline from a peak has occurred.
        worst_drawdown = 0.0

        # Traverse the price history in chronological order.
        for price in prices:

            # Update the historical peak when the price rises.
            running_peak = max(running_peak, price)

            # Calculate the current decline from that peak.
            current_drawdown = (
                1 - price / running_peak
            )

            # Keep track of the largest observed decline.
            worst_drawdown = max(
                worst_drawdown,
                current_drawdown
            )

        # NOTE:
        # This method analyzes a price series.
        # For portfolio drawdown, pass the portfolio equity curve.
        return worst_drawdown
