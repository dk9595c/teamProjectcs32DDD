
"""
WEAVE historical simulation engine.

Supported models:
    1. Lognormal Monte Carlo price simulation.
    2. Historical return bootstrapping.
    3. Simulation distribution summaries.

Important:
    Simulated outcomes depend on the historical sample and
    the assumptions of the selected model.

    These models do not predict future prices with certainty.
"""

import math
import random
from collections.abc import Sequence

from app.engines.calculations import (
    log_returns,
    sample_std,
)


def _finite(value: float, name: str) -> float:
    """Validate a finite numeric value."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
    ):
        raise TypeError(f"{name} must be numeric")

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")

    return float(value)


def _positive_int(value: int, name: str) -> None:
    """Require an integer greater than zero."""
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value <= 0
    ):
        raise ValueError(
            f"{name} must be a positive integer"
        )


def _mean(values: Sequence[float]) -> float:
    """Calculate the arithmetic mean of a nonempty series."""
    if len(values) == 0:
        raise ValueError("Cannot calculate mean of empty data")

    return math.fsum(values) / len(values)


def _quantile(
    sorted_values: Sequence[float],
    probability: float
) -> float:
    """
    Calculate an interpolated quantile.

    Input must be sorted in ascending order.

    Convention:
        position = p * (n - 1)

    Linear interpolation handles fractional positions
    instead of always selecting a lower array index.
    """
    if len(sorted_values) == 0:
        raise ValueError("Cannot calculate an empty quantile")

    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1")

    position = probability * (len(sorted_values) - 1)

    lower = math.floor(position)
    upper = math.ceil(position)
    fraction = position - lower

    return (
        sorted_values[lower] * (1 - fraction)
        + sorted_values[upper] * fraction
    )


class SimulationEngine:
    """Generate and summarize model-based future scenarios."""

    def monte_carlo(
        self,
        historical_prices: Sequence[float],
        starting_price: float = 100.0,
        simulation_days: int = 252,
        number_of_paths: int = 10000,
        random_seed: int = 42
    ) -> list[list[float]]:
        """
        Generate Monte Carlo paths using historical log returns.

        Model:
            log_return(t) = mu + sigma * Z(t)

            P(t+1) = P(t) * exp(log_return(t))

        Where:
            mu = Historical mean daily log return.
            sigma = Historical sample daily log-return std.
            Z = Independent standard normal random variable.

        This is a discrete lognormal model closely related
        to geometric Brownian motion.

        Each path contains:
            simulation_days + 1 values.

        The initial price is stored at index zero.
        """

        # Require sufficient data to estimate both a mean
        # and a sample standard deviation.
        if len(historical_prices) < 3:
            raise ValueError(
                "At least 3 historical prices are required"
            )

        starting_price = _finite(
            starting_price, "starting_price"
        )

        if starting_price <= 0:
            raise ValueError(
                "starting_price must be positive"
            )

        _positive_int(simulation_days, "simulation_days")
        _positive_int(number_of_paths, "number_of_paths")

        # Historical prices are validated by the shared helper.
        #
        # A log-return model is chosen because exponentiating
        # simulated returns gives positive prices.
        historical_log_returns = log_returns(
            historical_prices
        )

        # Guard against extreme numerical input behavior.
        if not all(
            math.isfinite(r)
            for r in historical_log_returns
        ):
            raise ValueError(
                "Historical log returns must be finite"
            )

        # Estimate the daily log-return distribution.
        mu = _mean(historical_log_returns)
        sigma = sample_std(historical_log_returns)

        if not all(
            math.isfinite(x) for x in (mu, sigma)
        ):
            raise ValueError(
                "Estimated simulation parameters are invalid"
            )

        # Use a local random generator, not global random state.
        #
        # The same seed and inputs produce identical paths.
        rng = random.Random(random_seed)

        paths = []

        for _ in range(number_of_paths):
            price = starting_price
            path = [price]

            for _ in range(simulation_days):
                z = rng.gauss(0.0, 1.0)

                # Generate one normally distributed log return.
                simulated_log_return = mu + sigma * z

                # Convert log return to a price multiplier.
                try:
                    price *= math.exp(simulated_log_return)
                except OverflowError as exc:
                    raise ValueError(
                        "Simulation overflowed; review the model "
                        "parameters or historical data"
                    ) from exc

                # Extreme underflow can produce zero even with
                # a theoretically positive lognormal model.
                if not math.isfinite(price) or price <= 0:
                    raise ValueError(
                        "Simulation produced an invalid price"
                    )

                path.append(price)

            paths.append(path)

        return paths

    def bootstrap(
        self,
        historical_returns: Sequence[float],
        initial_value: float = 100.0,
        horizon: int = 252,
        simulations: int = 10000,
        random_seed: int = 42
    ) -> list[list[float]]:
        """
        Generate bootstrap paths by resampling returns.

        Formula:
            V(t+1) = V(t) * (1 + sampled_return)

        Each return is sampled independently with replacement
        from the supplied historical return series.

        Unlike Monte Carlo, this method does not assume
        returns follow a normal distribution.

        Limitation:
            Independent resampling does not preserve
            serial correlations between trading days.
        """

        initial_value = _finite(
            initial_value, "initial_value"
        )

        if initial_value <= 0:
            raise ValueError(
                "initial_value must be positive"
            )

        _positive_int(horizon, "horizon")
        _positive_int(simulations, "simulations")

        # An empty return history cannot support sampling.
        if len(historical_returns) == 0:
            raise ValueError(
                "Historical returns cannot be empty"
            )

        valid_returns = []

        for r in historical_returns:
            r = _finite(r, "historical return")

            # A return below -100% is invalid for the
            # long-only price/value model used here.
            #
            # Exclude exactly -100% as well because the
            # simulated positive value would become zero.
            if r <= -1:
                raise ValueError(
                    "Historical returns must exceed -100%"
                )

            valid_returns.append(r)

        rng = random.Random(random_seed)
        paths = []

        for _ in range(simulations):
            value = initial_value
            path = [value]

            for _ in range(horizon):

                # Resample an observed return with replacement.
                sampled_return = rng.choice(valid_returns)

                # Compound the simulated value.
                value *= 1 + sampled_return

                if not math.isfinite(value) or value <= 0:
                    raise ValueError(
                        "Bootstrap produced an invalid value"
                    )

                path.append(value)

            paths.append(path)

        return paths

    def monte_carlo_summary(
        self,
        paths: list[list[float]],
        confidence_levels: list[float] | None = None
    ) -> dict:
        """
        Summarize simulated price or portfolio-value paths.

        For each simulated day, calculate:
            - Mean
            - Median
            - Requested quantiles

        Also calculate final-day:
            - Mean
            - Median
            - Minimum
            - Maximum
            - Sample standard deviation

        Quantile convention:
            Ascending sort with linear interpolation.

        This method summarizes either Monte Carlo
        or bootstrap output.
        """

        if confidence_levels is None:
            confidence_levels = [
                0.05, 0.25, 0.50, 0.75, 0.95
            ]

        # Preserve the original empty-input convention.
        if not paths:
            return {}

        # Validate the requested percentile levels.
        for level in confidence_levels:
            level = _finite(level, "confidence level")

            if not 0 <= level <= 1:
                raise ValueError(
                    "Confidence levels must be between 0 and 1"
                )

        # Require rectangular paths to avoid indexing errors.
        num_days = len(paths[0])

        if num_days == 0:
            raise ValueError("Simulation paths cannot be empty")

        for path in paths:
            if len(path) != num_days:
                raise ValueError(
                    "All simulation paths must have equal length"
                )

            # Reject invalid outcomes before calculating statistics.
            for value in path:
                value = _finite(value, "simulated value")

                if value <= 0:
                    raise ValueError(
                        "Simulated values must be positive"
                    )

        summary = {}

        for day_idx in range(num_days):

            # Gather this day's value from every path.
            day_values = [
                path[day_idx] for path in paths
            ]

            sorted_values = sorted(day_values)

            # Use an interpolated median, including when
            # the number of paths is even.
            day_summary = {
                "mean": _mean(day_values),
                "median": _quantile(sorted_values, 0.50),
            }

            # Calculate the requested percentile values.
            for level in confidence_levels:
                key = f"p{int(round(level * 100))}"

                day_summary[key] = _quantile(
                    sorted_values, level
                )

            summary[f"day_{day_idx}"] = day_summary

        # Final-value statistics describe the distribution
        # at the end of the simulated horizon.
        final_values = [
            path[-1] for path in paths
        ]

        sorted_final = sorted(final_values)

        summary["final"] = {
            "mean": _mean(final_values),
            "median": _quantile(sorted_final, 0.50),
            "min": sorted_final[0],
            "max": sorted_final[-1],
            "std": (
                sample_std(final_values)
                if len(final_values) >= 2
                else 0.0
            ),
        }

        return summary
