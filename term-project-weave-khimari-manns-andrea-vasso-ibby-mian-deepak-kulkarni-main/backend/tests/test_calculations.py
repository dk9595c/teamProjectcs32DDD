"""Tests for core financial calculations."""

import pytest
import math
from app.engines.calculations import (
    FinancialCalculationEngine,
    simple_returns,
    log_returns,
    sample_std,
    sample_variance,
    sample_covariance,
    validate_prices,
)


class TestFinancialCalculationEngine:

    @pytest.fixture
    def engine(self):
        return FinancialCalculationEngine()

    # --- cumulative_return ---

    def test_cumulative_return_basic(self, engine):
        prices = [100, 110, 121]
        result = engine.cumulative_return(prices)
        assert result == pytest.approx(0.21)

    def test_cumulative_return_negative(self, engine):
        prices = [100, 90, 80]
        result = engine.cumulative_return(prices)
        assert result == pytest.approx(-0.20)

    def test_cumulative_return_two_prices(self, engine):
        prices = [50, 75]
        result = engine.cumulative_return(prices)
        assert result == pytest.approx(0.50)

    def test_cumulative_return_too_few_prices(self, engine):
        with pytest.raises(ValueError):
            engine.cumulative_return([100])

    # --- percentage_price_change ---

    def test_percentage_price_change_positive(self, engine):
        result = engine.percentage_price_change(100, 110)
        assert result == pytest.approx(10.0)

    def test_percentage_price_change_negative(self, engine):
        result = engine.percentage_price_change(100, 90)
        assert result == pytest.approx(-10.0)

    def test_percentage_price_change_no_change(self, engine):
        result = engine.percentage_price_change(100, 100)
        assert result == pytest.approx(0.0)

    def test_percentage_price_change_zero_price(self, engine):
        with pytest.raises(ValueError):
            engine.percentage_price_change(0, 100)

    def test_percentage_price_change_negative_price(self, engine):
        with pytest.raises(ValueError):
            engine.percentage_price_change(-10, 100)

    # --- six_month_momentum ---

    def test_six_month_momentum_positive(self, engine):
        prices = [100] * 125 + [110, 115]
        result = engine.six_month_momentum(prices)
        assert result == pytest.approx(115 / 100 - 1)

    def test_six_month_momentum_custom_lookback(self, engine):
        prices = [100, 110, 120, 130]
        result = engine.six_month_momentum(prices, lookback=2)
        assert result == pytest.approx(130 / 110 - 1)

    def test_six_month_momentum_insufficient_data(self, engine):
        prices = [100, 110]
        with pytest.raises(ValueError):
            engine.six_month_momentum(prices, lookback=126)

    # --- annualized_volatility ---

    def test_annualized_volatility_known(self, engine):
        # Simple case: two-price series
        prices = [100, 102, 100, 98, 100]
        result = engine.annualized_volatility(prices)
        # Should be a positive number
        assert result > 0
        assert isinstance(result, float)

    def test_annualized_volatility_constant_prices(self, engine):
        prices = [100] * 10
        result = engine.annualized_volatility(prices)
        assert result == pytest.approx(0.0)

    def test_annualized_volatility_too_few_prices(self, engine):
        with pytest.raises(ValueError):
            engine.annualized_volatility([100, 102])

    # --- maximum_drawdown ---

    def test_maximum_drawdown_basic(self, engine):
        # Peak at 105, then drop to 70 => 33.3% drawdown from peak
        prices = [100, 105, 102, 90, 80, 70, 75, 80]
        result = engine.maximum_drawdown(prices)
        assert result == pytest.approx(1 - 70 / 105)  # 105 -> 70 = 33.3% drawdown from peak

    def test_maximum_drawdown_ascending(self, engine):
        prices = [100, 110, 120, 130]
        result = engine.maximum_drawdown(prices)
        assert result == pytest.approx(0.0)

    def test_maximum_drawdown_immediate_drop(self, engine):
        prices = [100, 80, 70, 90]
        result = engine.maximum_drawdown(prices)
        assert result == pytest.approx(0.30)  # 100 -> 70

    def test_maximum_drawdown_single_price(self, engine):
        prices = [100]
        result = engine.maximum_drawdown(prices)
        assert result == pytest.approx(0.0)

    # --- Helpers ---

    def test_simple_returns_basic(self):
        prices = [100, 102, 98]
        returns = simple_returns(prices)
        assert len(returns) == 2
        assert returns[0] == pytest.approx(0.02)
        assert returns[1] == pytest.approx(98 / 102 - 1)

    def test_log_returns_basic(self):
        prices = [100, 102]
        returns = log_returns(prices)
        assert len(returns) == 1
        assert returns[0] == pytest.approx(math.log(1.02))

    def test_sample_std_basic(self):
        values = [2, 4, 4, 4, 5, 5, 7, 9]
        # Population std would be 2, sample std is slightly higher
        result = sample_std(values)
        assert result == pytest.approx(2.138, abs=0.01)

    def test_sample_variance_basic(self):
        values = [2, 4, 4, 4, 5, 5, 7, 9]
        result = sample_variance(values)
        assert result == pytest.approx(4.571, abs=0.01)

    def test_sample_covariance_basic(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 5, 4, 8]
        result = sample_covariance(x, y)
        assert result > 0

    def test_validate_prices_invalid(self):
        with pytest.raises(ValueError):
            validate_prices([100, -1, 100], minimum=2)

    def test_validate_prices_nan(self):
        with pytest.raises(ValueError):
            validate_prices([100, float('nan'), 100], minimum=2)

    def test_validate_prices_too_short(self):
        with pytest.raises(ValueError):
            validate_prices([100], minimum=3)
