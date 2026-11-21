
"""
Portfolio mathematics engine for WEAVE.

This module handles:
    1. Expected portfolio returns.
    2. Portfolio volatility using covariance matrices.
    3. Portfolio optimization using the Sharpe ratio.
    4. Binary Kelly position sizing.
    5. Approximate continuous-return Kelly sizing.

The engine operates on numerical inputs only.
It does not retrieve historical stock prices or execute trades.

Financial conventions:
    - Portfolio weights are represented as decimal fractions.
    - 0.25 represents a 25% allocation.
    - Returns and risk-free rates use decimal notation.
    - Historical returns are assumed to be daily observations.
    - Annualization uses 252 trading days.
"""

import math
from collections.abc import Sequence


def _dot(
    a: Sequence[float],
    b: Sequence[float]
) -> float:
    """
    Calculate the dot product of two vectors.

    Formula:
        a · b = SUM(a[i] * b[i])

    Used for:
        - Expected portfolio returns.
        - Portfolio variance.
        - Sharpe-ratio calculations.
    """

    # A dot product requires vectors of equal dimension.
    if len(a) != len(b):
        raise ValueError(
            "Sequences must have the same length"
        )

    # Multiply corresponding elements and sum their products.
    return sum(x * y for x, y in zip(a, b))


def _transpose_mul_matrix_vector(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float]
) -> list[float]:
    """
    Multiply a matrix by a column vector.

    Mathematical operation:
        result = Matrix @ Vector

    Despite the function's name, this does not transpose
    the matrix.

    Each output element is the dot product of one
    matrix row and the supplied vector.

    REVIEW:
        Consider renaming this helper to _matrix_vector_mul().
        Its current name could cause confusion.
    """

    # REVIEW:
    # Validate that the matrix is rectangular and that
    # each row contains exactly len(vector) elements.
    return [
        _dot(row, vector)
        for row in matrix
    ]


def _matrix_mul(
    matrix_a: Sequence[Sequence[float]],
    matrix_b: Sequence[Sequence[float]]
) -> list[list[float]]:
    """
    Multiply two matrices.

    Matrix multiplication:
        C[i][j] = SUM(A[i][k] * B[k][j])

    Dimension requirement:
        A has dimensions (n x p).
        B has dimensions (p x m).
        Result has dimensions (n x m).

    REVIEW:
        This helper currently assumes both matrices are
        nonempty, rectangular, and dimensionally compatible.
    """

    # Number of rows in the first matrix.
    n = len(matrix_a)

    # Number of columns in the second matrix.
    # REVIEW: Empty matrix_b raises IndexError here.
    m = len(matrix_b[0])

    # Initialize the result with zero values.
    result = [
        [0.0] * m
        for _ in range(n)
    ]

    # Visit every result-matrix position.
    for i in range(n):
        for j in range(m):

            # Multiply a row of A by a column of B.
            result[i][j] = sum(
                matrix_a[i][k] * matrix_b[k][j]
                for k in range(len(matrix_b))
            )

    # REVIEW:
    # Verify len(matrix_a[0]) == len(matrix_b)
    # before performing matrix multiplication.
    return result


def _matrix_transpose(
    matrix: Sequence[Sequence[float]]
) -> list[list[float]]:
    """
    Transpose a matrix.

    A transpose exchanges rows and columns.

    Formula:
        Transpose(A)[j][i] = A[i][j]

    Useful for matrix-based portfolio calculations.
    """

    # Determine the original matrix dimensions.
    n = len(matrix)

    # REVIEW: An empty matrix raises IndexError.
    m = len(matrix[0])

    # Exchange the row and column indices.
    return [
        [matrix[i][j] for i in range(n)]
        for j in range(m)
    ]


def _clamp(
    value: float,
    min_val: float,
    max_val: float
) -> float:
    """
    Restrict a value to an allowed interval.

    Formula:
        clamp(x, a, b) = max(a, min(b, x))

    Examples:
        clamp(1.2, 0, 1) -> 1.0
        clamp(-0.2, 0, 1) -> 0.0

    Used to enforce investment allocation limits.
    """

    # REVIEW:
    # Validate min_val <= max_val.
    # Reject nonfinite inputs.
    return max(
        min_val,
        min(max_val, value)
    )


class PortfolioMathEngine:
    """
    Calculate portfolio returns, risk, and allocations.

    This engine implements mathematical models commonly
    used in portfolio analysis.

    Important distinction:
        Historical optimization does not guarantee
        superior future investment performance.
    """

    def expected_portfolio_return(
        self,
        weights: Sequence[float],
        means: Sequence[float]
    ) -> float:
        """
        Calculate a portfolio's expected return.

        Formula:
            E[R_p] = SUM(w[i] * E[R_i])

        Matrix notation:
            E[R_p] = w.T @ mu

        Args:
            weights:
                Allocation assigned to each asset.

            means:
                Expected return of each asset.

        Returns:
            Expected portfolio return as a decimal.

        Example:
            weights = [0.60, 0.40]
            means = [0.10, 0.05]

            E[R_p] = 0.60(0.10) + 0.40(0.05)
                   = 0.08

            Expected return = 8%.
        """

        # Every asset weight must correspond to a return estimate.
        if len(weights) != len(means):
            raise ValueError(
                "Weights and means must have the same length"
            )

        # REVIEW:
        # Define whether this method requires fully invested
        # weights or also permits cash and short positions.
        #
        # For long-only, fully invested portfolios:
        #     SUM(weights) = 1
        #     Each weight >= 0
        #
        # Validate finite weights and expected returns.

        # Multiply each asset's weight by its expected return.
        return _dot(weights, means)

    def portfolio_volatility(
        self,
        weights: Sequence[float],
        covariance: Sequence[Sequence[float]]
    ) -> float:
        """
        Calculate portfolio standard deviation.

        Portfolio variance:
            Variance = w.T @ Sigma @ w

        Portfolio volatility:
            Volatility = sqrt(Variance)

        Sigma represents the covariance matrix.

        A covariance matrix captures:
            - Individual asset return variances.
            - Relationships between asset returns.
            - Diversification effects.

        Args:
            weights:
                Portfolio allocation vector.

            covariance:
                Square covariance matrix.

        Returns:
            Portfolio volatility as a decimal.

        Important:
            The covariance matrix determines the time scale.

            Daily covariance produces daily volatility.
            Annual covariance produces annual volatility.
        """

        n = len(weights)

        # The covariance matrix must contain one row per asset.
        if n != len(covariance):
            raise ValueError(
                "Weights length must match covariance matrix dimensions"
            )

        # REVIEW:
        # Check each covariance row has exactly n columns.
        # Also check symmetry and finite values.
        #
        # A valid covariance matrix should be positive
        # semidefinite, meaning portfolio variance >= 0
        # for every possible weight vector.

        # Step 1:
        # Multiply covariance matrix by the weights vector.
        #
        # Result = Sigma @ w
        cov_w = _transpose_mul_matrix_vector(
            covariance,
            weights
        )

        # Step 2:
        # Multiply the weight vector by the previous result.
        #
        # Variance = w.T @ Sigma @ w
        variance = _dot(weights, cov_w)

        # REVIEW (CRITICAL):
        # Large negative variance indicates invalid covariance
        # input or a numerical problem.
        #
        # Silently changing every negative variance to zero
        # can conceal serious calculation errors.
        #
        # Only tiny negative floating-point errors should
        # potentially be treated as zero.
        if variance < 0:
            variance = 0.0

        # Step 3:
        # Convert portfolio variance into standard deviation.
        return math.sqrt(variance)

    def optimize_portfolio(
        self,
        returns_matrix: Sequence[Sequence[float]],
        risk_free_rate: float = 0.02,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
        max_iterations: int = 1000,
        step_size: float = 0.001
    ) -> list[float]:
        """
        Estimate portfolio weights that maximize Sharpe ratio.

        Objective:
            Maximize Sharpe Ratio

        Sharpe Ratio:
            S = (Expected Return - Risk-Free Rate) / Volatility

        Portfolio Expected Return:
            E[R_p] = w.T @ mu

        Portfolio Variance:
            Var(R_p) = w.T @ Sigma @ w

        Constraints:
            SUM(weights) = 1
            min_weight <= weight <= max_weight

        Optimization method:
            Numerical gradient ascent.

        Args:
            returns_matrix:
                Matrix of daily historical returns.

                Rows represent trading periods.
                Columns represent different assets.

            risk_free_rate:
                Annual risk-free rate.

            min_weight:
                Minimum allocation per asset.

            max_weight:
                Maximum allocation per asset.

            max_iterations:
                Maximum optimization steps.

            step_size:
                Learning rate for updating portfolio weights.

        Returns:
            Estimated portfolio allocation weights.

        REVIEW:
            This is a basic numerical optimizer.
            It does not guarantee convergence to the
            global optimum or even a feasible solution.
        """

        # No return observations means no portfolio to optimize.
        if not returns_matrix:
            return []

        # Number of assets is determined by the first row.
        n_assets = len(returns_matrix[0])

        # Number of historical trading observations.
        n_periods = len(returns_matrix)

        # REVIEW (CRITICAL):
        # Require:
        #     n_assets >= 1
        #     n_periods >= 2
        #
        # With only one observation, covariance calculation
        # divides by n_periods - 1 = 0.
        #
        # Also verify all rows have n_assets columns,
        # and every observation is finite.

        # --------------------------------------------------
        # Step 1: Calculate mean daily returns.
        # --------------------------------------------------

        mean_returns = []

        for j in range(n_assets):

            # Extract the return history for asset j.
            col_returns = [
                returns_matrix[i][j]
                for i in range(n_periods)
            ]

            # Arithmetic average of observed daily returns.
            mean_returns.append(
                sum(col_returns) / n_periods
            )

        # --------------------------------------------------
        # Step 2: Construct the covariance matrix.
        # --------------------------------------------------

        # Initialize an n_assets x n_assets matrix.
        covariance = [
            [0.0] * n_assets
            for _ in range(n_assets)
        ]

        for i in range(n_assets):
            for j in range(n_assets):

                # Select the historical returns of asset i.
                col_i = [
                    returns_matrix[k][i]
                    for k in range(n_periods)
                ]

                # Select the historical returns of asset j.
                col_j = [
                    returns_matrix[k][j]
                    for k in range(n_periods)
                ]

                # Calculate both asset return averages.
                mean_i = sum(col_i) / n_periods
                mean_j = sum(col_j) / n_periods

                # Sample covariance:
                #
                # Cov(i,j) =
                # SUM((r_i - mean_i)(r_j - mean_j)) / (n - 1)
                cov = sum(
                    (col_i[k] - mean_i)
                    * (col_j[k] - mean_j)
                    for k in range(n_periods)
                ) / (n_periods - 1)

                covariance[i][j] = cov

        # REVIEW:
        # Covariance calculations repeatedly extract columns
        # and calculate means inside nested loops.
        #
        # Compute column means once and reuse them to
        # reduce unnecessary repeated work.

        # --------------------------------------------------
        # Step 3: Annualize mean returns and covariance.
        # --------------------------------------------------

        # Approximate annual arithmetic return.
        annual_returns = [
            r * 252
            for r in mean_returns
        ]

        # Scale daily covariance to annual covariance.
        annual_cov = [
            [c * 252 for c in row]
            for row in covariance
        ]

        # REVIEW:
        # Replace hardcoded 252 with a shared constant.
        #
        # Annualization assumes the input contains daily
        # trading returns and applies conventional
        # square-root-of-time risk scaling.

        # --------------------------------------------------
        # Step 4: Initialize equal portfolio weights.
        # --------------------------------------------------

        # Each asset receives an equal starting allocation.
        weights = [
            1.0 / n_assets
        ] * n_assets

        # REVIEW (CRITICAL):
        # Check whether the requested constraints are feasible.
        #
        # For uniform bounds:
        #     n_assets * min_weight <= 1
        #     n_assets * max_weight >= 1
        #
        # Otherwise, no fully invested portfolio can satisfy
        # all allocation constraints.

        def portfolio_sharpe(
            w: list[float]
        ) -> float:
            """
            Calculate the annualized Sharpe ratio
            for a candidate weight vector.
            """

            # Calculate portfolio expected annual return.
            port_return = _dot(
                w,
                annual_returns
            )

            # Calculate portfolio annual variance.
            port_variance = _dot(
                w,
                _transpose_mul_matrix_vector(
                    annual_cov,
                    w
                )
            )

            # Standard deviation is the square root of variance.
            port_vol = math.sqrt(
                max(port_variance, 0.0)
            )

            # REVIEW (CRITICAL):
            # Returning zero when volatility is zero
            # incorrectly treats an undefined Sharpe ratio
            # as a valid numerical result.
            #
            # Handle this case explicitly.
            if port_vol == 0:
                return 0.0

            # Sharpe measures excess return per unit of risk.
            return (
                port_return - risk_free_rate
            ) / port_vol

        # --------------------------------------------------
        # Step 5: Improve weights using gradient ascent.
        # --------------------------------------------------

        for iteration in range(max_iterations):

            # Each entry approximates how changes in one
            # asset's allocation affect the Sharpe ratio.
            gradient = [
                0.0
            ] * n_assets

            # Small perturbation for finite differences.
            eps = 1e-6

            # Calculate the present portfolio's Sharpe ratio.
            #
            # REVIEW:
            # current_sharpe is not used later in this method.
            current_sharpe = portfolio_sharpe(
                weights
            )

            for j in range(n_assets):

                # Test a small increase in asset j's weight.
                w_up = list(weights)
                w_up[j] += eps

                # Renormalize to maintain total weight = 1.
                w_sum = sum(w_up)

                w_up = [
                    w / w_sum
                    for w in w_up
                ]

                # Test a small decrease in asset j's weight.
                w_down = list(weights)
                w_down[j] -= eps

                w_sum = sum(w_down)

                w_down = [
                    w / w_sum
                    for w in w_down
                ]

                # Estimate the derivative using central differences.
                #
                # dSharpe/dWeight[j] approximately equals:
                #
                # (Sharpe(w_up) - Sharpe(w_down)) / (2*eps)
                grad_j = (
                    portfolio_sharpe(w_up)
                    - portfolio_sharpe(w_down)
                ) / (2 * eps)

                gradient[j] = grad_j

                # REVIEW:
                # These perturbed weights may violate the
                # requested min/max constraints.
                #
                # The perturbation and renormalization also
                # change multiple weights at the same time.

            # Move in the direction of higher Sharpe ratio.
            new_weights = [
                weights[j] + step_size * gradient[j]
                for j in range(n_assets)
            ]

            # --------------------------------------------------
            # Step 6: Enforce allocation bounds.
            # --------------------------------------------------

            # Restrict individual weights to requested limits.
            new_weights = [
                _clamp(w, min_weight, max_weight)
                for w in new_weights
            ]

            # REVIEW (CRITICAL):
            # Clamping followed by normalization does not
            # guarantee that min_weight and max_weight
            # remain satisfied.
            #
            # Example:
            #     clamped weights = [0.6, 0.1]
            #     normalized = [0.857..., 0.143...]
            #
            # The first weight now exceeds a max_weight of 0.6.
            #
            # A bounded-simplex projection or constrained
            # optimization method is needed.

            # Renormalize weights so their sum equals 1.
            w_sum = sum(new_weights)

            if w_sum > 0:
                new_weights = [
                    w / w_sum
                    for w in new_weights
                ]
            else:
                # Return to equal weights when the sum is zero.
                #
                # REVIEW:
                # Equal weights may violate min/max constraints.
                new_weights = [
                    1.0 / n_assets
                ] * n_assets

            # --------------------------------------------------
            # Step 7: Evaluate convergence.
            # --------------------------------------------------

            # Measure total change in allocation weights.
            weight_change = sum(
                abs(new_weights[j] - weights[j])
                for j in range(n_assets)
            )

            # Stop if allocations have nearly stopped changing.
            #
            # REVIEW:
            # The condition measures weight changes, not
            # improvements in the optimization objective.
            #
            # REVIEW (BUG):
            # If convergence is detected here, the updated
            # new_weights are discarded because the loop
            # exits before weights = new_weights.
            if abs(weight_change) < 1e-8:
                break

            # Carry updated weights into the next iteration.
            weights = new_weights

        # REVIEW:
        # Before returning:
        # 1. Verify weights sum to 1.
        # 2. Verify every weight satisfies its bounds.
        # 3. Verify every weight is finite.
        # 4. Check whether optimization actually improved Sharpe.
        #
        # A small weight change alone does not prove that
        # a maximum-Sharpe allocation was found.

        return weights

    def binary_kelly(
        self,
        win_probability: float,
        payoff_ratio: float
    ) -> float:
        """
        Calculate the Kelly fraction for a binary outcome.

        Formula:
            f* = (b*p - q) / b

        Where:
            p = Probability of winning.
            q = Probability of losing = 1 - p.
            b = Net payoff per unit invested.

        Example:
            p = 0.60
            b = 1.0

            f* = (1.0*0.60 - 0.40) / 1.0
               = 0.20

            The theoretical Kelly fraction is 20%.

        Args:
            win_probability:
                Estimated probability of winning.

            payoff_ratio:
                Net payoff multiple for a successful outcome.

        Returns:
            Theoretical Kelly fraction.

        Important:
            The raw Kelly result may be negative.
            Negative values indicate a negative edge for
            the proposed binary bet.

            Kelly assumes the payoff structure and
            probabilities are known and reasonably accurate.
        """

        # A probability must be between zero and one.
        if not (0 <= win_probability <= 1):
            raise ValueError(
                "win_probability must be between 0 and 1"
            )

        # A valid winning payoff must be strictly positive.
        if payoff_ratio <= 0:
            raise ValueError(
                "payoff_ratio must be positive"
            )

        # REVIEW:
        # Explicitly reject NaN and infinity in both inputs.
        # NaN may bypass comparison-based validation.

        # Probability of success.
        p = win_probability

        # Probability of failure.
        q = 1 - p

        # Net amount won per unit wagered.
        b = payoff_ratio

        # Calculate the theoretical growth-optimal fraction.
        optimal_fraction = (
            b * p - q
        ) / b

        # REVIEW:
        # If this will be used for a long-only portfolio,
        # decide whether negative fractions should be
        # clamped to zero by a separate allocation policy.
        return optimal_fraction

    def approximate_kelly(
        self,
        expected_excess_return: float,
        return_variance: float,
        maximum_fraction: float = 1.0
    ) -> float:
        """
        Estimate a continuous-return Kelly allocation.

        Approximation:
            f* = Expected Excess Return / Return Variance

        The approximation assumes a simplified return model
        and should not be treated as a universal allocation rule.

        Args:
            expected_excess_return:
                Expected return above the risk-free rate.

            return_variance:
                Estimated variance of investment returns.

            maximum_fraction:
                Maximum allowed allocation.

                Example:
                    1.0 represents 100% of available capital.

        Returns:
            Kelly fraction restricted to:
                [0, maximum_fraction]

        Example:
            expected_excess_return = 0.04
            return_variance = 0.16

            f* = 0.04 / 0.16
               = 0.25

            Estimated allocation = 25%.

        IMPORTANT:
            Expected excess return and variance must use
            consistent time intervals.
        """

        # Variance must be positive to calculate the ratio.
        #
        # REVIEW:
        # Returning 0.0 hides invalid variance input.
        # Consider raising ValueError for negative variance
        # and defining an explicit policy for zero variance.
        if return_variance <= 0:
            return 0.0

        # Estimate growth-optimal allocation.
        fraction = (
            expected_excess_return
            / return_variance
        )

        # Restrict allocations to the allowed long-only range.
        #
        # Negative fractions become zero.
        # Fractions above maximum_fraction are capped.
        #
        # REVIEW:
        # Validate maximum_fraction is finite and nonnegative.
        # Also reject nonfinite returns and variance.
        return _clamp(
            fraction,
            0,
            maximum_fraction
        )
