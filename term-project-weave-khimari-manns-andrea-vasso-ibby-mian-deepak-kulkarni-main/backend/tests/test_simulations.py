"""Tests for simulation engine."""

import pytest
import math
import random
from app.engines.simulations import SimulationEngine


class TestSimulationEngine:

    @pytest.fixture
    def engine(self):
        return SimulationEngine()

    @pytest.fixture
    def historical_prices(self):
        """Create a realistic price series for simulation."""
        random.seed(42)
        prices = [100.0]
        for _ in range(251):
            prices.append(prices[-1] * (1 + random.gauss(0.0005, 0.01)))
        return prices

    # --- monte_carlo ---

    def test_monte_carlo_returns_paths(self, engine, historical_prices):
        paths = engine.monte_carlo(historical_prices, simulation_days=10, number_of_paths=100, random_seed=42)
        assert len(paths) == 100
        assert all(len(path) == 11 for path in paths)  # 10 days + initial

    def test_monte_carlo_starting_price(self, engine, historical_prices):
        paths = engine.monte_carlo(historical_prices, starting_price=50.0, number_of_paths=10, random_seed=42)
        assert all(path[0] == 50.0 for path in paths)

    def test_monte_carlo_reproducibility(self, engine, historical_prices):
        paths1 = engine.monte_carlo(historical_prices, number_of_paths=10, random_seed=42)
        paths2 = engine.monte_carlo(historical_prices, number_of_paths=10, random_seed=42)
        assert paths1 == paths2  # Same seed => identical paths

    def test_monte_carlo_different_seeds(self, engine, historical_prices):
        paths1 = engine.monte_carlo(historical_prices, number_of_paths=10, random_seed=42)
        paths2 = engine.monte_carlo(historical_prices, number_of_paths=10, random_seed=123)
        assert paths1 != paths2  # Different seeds => different paths

    def test_monte_carlo_prices_positive(self, engine, historical_prices):
        paths = engine.monte_carlo(historical_prices, number_of_paths=100, simulation_days=252, random_seed=42)
        for path in paths:
            for price in path:
                assert price > 0, "All simulated prices should be positive"

    # --- bootstrap ---

    def test_bootstrap_returns_paths(self, engine):
        returns = [0.01, -0.005, 0.008, -0.003, 0.002]
        paths = engine.bootstrap(returns, horizon=10, simulations=50, random_seed=42)
        assert len(paths) == 50
        assert all(len(path) == 11 for path in paths)

    def test_bootstrap_initial_value(self, engine):
        returns = [0.01, -0.005, 0.008]
        paths = engine.bootstrap(returns, initial_value=200.0, simulations=10, random_seed=42)
        assert all(path[0] == 200.0 for path in paths)

    def test_bootstrap_reproducibility(self, engine):
        returns = [0.01, -0.005, 0.008, -0.003]
        paths1 = engine.bootstrap(returns, simulations=10, random_seed=42)
        paths2 = engine.bootstrap(returns, simulations=10, random_seed=42)
        assert paths1 == paths2

    def test_bootstrap_ascending_returns(self, engine):
        returns = [0.02] * 10
        paths = engine.bootstrap(returns, initial_value=100.0, horizon=5, simulations=10, random_seed=42)
        for path in paths:
            for i in range(1, len(path)):
                assert path[i] >= path[i - 1], "With only positive returns, values should not decrease"

    def test_bootstrap_descending_returns(self, engine):
        returns = [-0.01] * 10
        paths = engine.bootstrap(returns, initial_value=100.0, horizon=5, simulations=10, random_seed=42)
        for path in paths:
            for i in range(1, len(path)):
                assert path[i] <= path[i - 1], "With only negative returns, values should not increase"

    # --- monte_carlo_summary ---

    def test_monte_carlo_summary_structure(self, engine, historical_prices):
        paths = engine.monte_carlo(historical_prices, simulation_days=5, number_of_paths=1000, random_seed=42)
        summary = engine.monte_carlo_summary(paths)
        assert 'day_0' in summary
        assert 'day_5' in summary
        assert 'final' in summary

    def test_monte_carlo_summary_final_stats(self, engine, historical_prices):
        paths = engine.monte_carlo(historical_prices, simulation_days=10, number_of_paths=1000, random_seed=42)
        summary = engine.monte_carlo_summary(paths)
        final = summary['final']
        assert 'mean' in final
        assert 'median' in final
        assert 'min' in final
        assert 'max' in final
        assert 'std' in final
        assert final['min'] > 0  # Prices should remain positive
        assert final['max'] > final['mean']

    def test_monte_carlo_summary_empty(self, engine):
        summary = engine.monte_carlo_summary([])
        assert summary == {}

    def test_monte_carlo_summary_percentiles(self, engine, historical_prices):
        paths = engine.monte_carlo(historical_prices, simulation_days=5, number_of_paths=1000, random_seed=42)
        summary = engine.monte_carlo_summary(paths, confidence_levels=[0.05, 0.95])
        day_0 = summary['day_0']
        assert 'p5' in day_0
        assert 'p95' in day_0
