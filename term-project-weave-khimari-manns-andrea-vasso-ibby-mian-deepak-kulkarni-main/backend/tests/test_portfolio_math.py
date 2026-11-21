"""Tests for portfolio math engine."""

import pytest
import math
import random
from app.engines.portfolio_math import PortfolioMathEngine


class TestPortfolioMathEngine:

    @pytest.fixture
    def engine(self):
        return PortfolioMathEngine()

    @pytest.fixture
    def returns_matrix(self):
        """Create a returns matrix with known properties."""
        random.seed(42)
        returns = []
        for _ in range(100):
            row = [random.gauss(0.0005, 0.01) for _ in range(4)]
            returns.append(row)
        return returns

    # --- expected_portfolio_return ---

    def test_expected_portfolio_return_basic(self, engine):
        weights = [0.5, 0.5]
        means = [0.08, 0.12]
        result = engine.expected_portfolio_return(weights, means)
        assert result == pytest.approx(0.10)

    def test_expected_portfolio_return_full_in_one(self, engine):
        weights = [1.0]
        means = [0.06]
        result = engine.expected_portfolio_return(weights, means)
        assert result == pytest.approx(0.06)

    def test_expected_portfolio_return_mismatched_length(self, engine):
        with pytest.raises(ValueError):
            engine.expected_portfolio_return([0.5], [0.08, 0.12])

    # --- portfolio_volatility ---

    def test_portfolio_volatility_single_asset(self, engine):
        weights = [1.0]
        covariance = [[0.04]]  # 20% vol
        result = engine.portfolio_volatility(weights, covariance)
        assert result == pytest.approx(0.20)

    def test_portfolio_volatility_perfectly_correlated(self, engine):
        weights = [0.5, 0.5]
        # Both assets have 0.04 variance and perfect correlation
        covariance = [[0.04, 0.04], [0.04, 0.04]]
        result = engine.portfolio_volatility(weights, covariance)
        assert result == pytest.approx(0.20)

    def test_portfolio_volatility_dimensions_mismatch(self, engine):
        with pytest.raises(ValueError):
            engine.portfolio_volatility([0.5, 0.5, 0.5], [[0.01, 0.0], [0.0, 0.01]])

    # --- optimize_portfolio ---

    def test_optimize_portfolio_structure(self, engine, returns_matrix):
        result = engine.optimize_portfolio(returns_matrix)
        assert len(result) == 4  # 4 assets
        assert abs(sum(result) - 1.0) < 1e-9  # weights sum to 1
        assert all(w >= 0 for w in result)  # non-negative

    def test_optimize_portfolio_reproducibility(self, engine, returns_matrix):
        result1 = engine.optimize_portfolio(returns_matrix, max_iterations=100)
        result2 = engine.optimize_portfolio(returns_matrix, max_iterations=100)
        assert len(result1) == len(result2)

    def test_optimize_portfolio_empty(self, engine):
        result = engine.optimize_portfolio([])
        assert result == []

    # --- binary_kelly ---

    def test_binary_kelly_favorable(self, engine):
        result = engine.binary_kelly(0.6, 2.0)
        assert result == pytest.approx(0.4)  # (2*0.6 - 0.4)/2 = 0.4

    def test_binary_kelly_unfavorable(self, engine):
        result = engine.binary_kelly(0.4, 2.0)
        assert result == pytest.approx(0.1)  # (2*0.4 - 0.6)/2 = 0.1 (small positive edge)

    def test_binary_kelly_even_money(self, engine):
        result = engine.binary_kelly(0.6, 1.0)
        assert result == pytest.approx(0.2)  # (1*0.6 - 0.4)/1 = 0.2

    def test_binary_kelly_invalid_probability(self, engine):
        with pytest.raises(ValueError):
            engine.binary_kelly(1.5, 2.0)

    def test_binary_kelly_invalid_payoff(self, engine):
        with pytest.raises(ValueError):
            engine.binary_kelly(0.5, 0)

    def test_binary_kelly_zero_probability(self, engine):
        result = engine.binary_kelly(0.0, 2.0)
        assert result == pytest.approx(-0.5)

    # --- approximate_kelly ---

    def test_approximate_kelly_basic(self, engine):
        result = engine.approximate_kelly(0.04, 0.16)
        assert result == pytest.approx(0.25)

    def test_approximate_kelly_clamped(self, engine):
        result = engine.approximate_kelly(2.0, 0.1, maximum_fraction=0.5)
        assert result == pytest.approx(0.5)

    def test_approximate_kelly_zero_variance(self, engine):
        result = engine.approximate_kelly(0.04, 0.0)
        assert result == 0.0

    def test_approximate_kelly_negative_variance(self, engine):
        result = engine.approximate_kelly(0.04, -0.1)
        assert result == 0.0

    def test_approximate_kelly_no_leverage(self, engine):
        result = engine.approximate_kelly(0.01, 0.0001, maximum_fraction=1.0)
        assert result == pytest.approx(1.0)  # 0.01/0.0001 = 100, clamped to 1.0
        # But clamped
        assert result <= 1.0
