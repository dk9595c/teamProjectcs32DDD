"""Tests for backtesting engine."""

import pytest
import math
import random
from app.engines.backtesting import BacktestEngine


class TestBacktestEngine:

    @pytest.fixture
    def engine(self):
        return BacktestEngine()

    @pytest.fixture
    def multi_asset_prices(self):
        """Create simple multi-asset price data."""
        random.seed(42)
        assets = {}
        for name in ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']:
            prices = [100.0]
            for _ in range(251):
                prices.append(prices[-1] * (1 + random.gauss(0.0005, 0.01)))
            assets[name] = prices
        return assets

    # --- buy_and_hold ---

    def test_buy_and_hold_single_asset(self, engine):
        prices = {'AAPL': [100, 105, 110, 115, 120]}
        weights = {'AAPL': 1.0}
        result = engine.buy_and_hold(prices, weights, capital=10000)
        assert len(result) == 5
        assert result[0] == pytest.approx(10000)
        assert result[-1] == pytest.approx(12000)

    def test_buy_and_hold_multi_asset(self, engine, multi_asset_prices):
        weights = {a: 0.2 for a in multi_asset_prices}
        result = engine.buy_and_hold(multi_asset_prices, weights, capital=100000)
        assert len(result) == 252
        assert result[0] == pytest.approx(100000)

    def test_buy_and_hold_invalid_weights(self, engine):
        prices = {'AAPL': [100, 105, 110]}
        weights = {'AAPL': 0.5}  # Doesn't sum to 1
        with pytest.raises(ValueError):
            engine.buy_and_hold(prices, weights)

    def test_buy_and_hold_mismatched_lengths(self, engine):
        prices = {
            'AAPL': [100, 105, 110],
            'GOOGL': [100, 105]
        }
        weights = {'AAPL': 0.5, 'GOOGL': 0.5}
        with pytest.raises(ValueError):
            engine.buy_and_hold(prices, weights)

    # --- periodic_rebalancing ---

    def test_periodic_rebalancing_returns_structure(self, engine, multi_asset_prices):
        weights = {a: 0.2 for a in multi_asset_prices}
        schedule = [21, 42, 63, 84]
        result = engine.periodic_rebalancing(multi_asset_prices, weights, schedule)
        assert 'equity_curve' in result
        assert 'trade_log' in result
        assert 'final_value' in result
        assert len(result['equity_curve']) == 252

    # --- momentum_backtest ---

    def test_momentum_backtest_returns_structure(self, engine, multi_asset_prices):
        result = engine.momentum_backtest(multi_asset_prices, lookback=21, top_k=3)
        assert 'equity_curve' in result
        assert 'trade_log' in result
        assert 'final_value' in result
        assert result['final_value'] > 0

    def test_momentum_backtest_single_asset(self, engine):
        prices = {'AAPL': [100 + i for i in range(50)]}
        result = engine.momentum_backtest(prices, lookback=5, top_k=1)
        assert result['final_value'] > 0

    # --- walk_forward_test ---

    def test_walk_forward_test_returns_structure(self, engine, multi_asset_prices):
        result = engine.walk_forward_test(multi_asset_prices, train_window=100, test_window=21)
        assert 'equity_curve' in result
        assert 'final_value' in result
        assert 'total_return' in result

    def test_walk_forward_test_empty(self, engine):
        result = engine.walk_forward_test({}, train_window=252, test_window=63)
        assert result['equity_curve'] == []

    # --- stress_test ---

    def test_stress_test_crash(self, engine, multi_asset_prices):
        weights = {a: 0.2 for a in multi_asset_prices}
        scenarios = {
            'crash': {a: -0.30 for a in multi_asset_prices},
            'mild_downturn': {a: -0.05 for a in multi_asset_prices}
        }
        result = engine.stress_test(multi_asset_prices, weights, scenarios)
        assert 'crash' in result
        assert 'mild_downturn' in result
        assert result['crash']['portfolio_return'] == pytest.approx(-0.30)
        assert result['mild_downturn']['portfolio_return'] == pytest.approx(-0.05)
        # Crash should be worse than mild downturn
        assert result['crash']['portfolio_return'] < result['mild_downturn']['portfolio_return']

    def test_stress_test_partial_shocks(self, engine, multi_asset_prices):
        weights = {'AAPL': 0.6, 'GOOGL': 0.4}
        scenarios = {
            'aapl_crash': {'AAPL': -0.40, 'GOOGL': -0.10},
        }
        result = engine.stress_test(multi_asset_prices, weights, scenarios)
        # 0.6 * (-0.40) + 0.4 * (-0.10) = -0.28
        assert result['aapl_crash']['portfolio_return'] == pytest.approx(-0.28)
