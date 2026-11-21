"""Tests for risk metrics calculations."""

import pytest
import math
from app.engines.risk_metrics import RiskMetricsEngine


class TestRiskMetricsEngine:

    @pytest.fixture
    def engine(self):
        return RiskMetricsEngine()

    @pytest.fixture
    def price_series(self):
        """Create a realistic price series with known properties."""
        import random
        random.seed(42)
        prices = [100.0]
        for _ in range(251):
            # Simulate ~5% annual return with ~30% annual volatility (enough downside)
            daily_mean = 0.05 / 252
            daily_vol = 0.30 / math.sqrt(252)
            new_price = prices[-1] * math.exp(daily_mean + daily_vol * (random.gauss(0, 1)))
            prices.append(new_price)
        return prices

    @pytest.fixture
    def simple_price_series(self):
        """Create a simple predictable price series."""
        return [100, 101, 102, 101, 103, 104, 103, 105, 106, 107]

    # --- sharpe_ratio ---

    def test_sharpe_ratio_positive(self, engine, price_series):
        result = engine.sharpe_ratio(price_series, risk_free_rate=0.02)
        assert result is not None
        assert result > 0

    def test_sharpe_ratio_known_simple(self, engine, simple_price_series):
        result = engine.sharpe_ratio(simple_price_series, risk_free_rate=0.0)
        assert result is not None
        assert result > 0

    def test_sharpe_ratio_constant_prices(self, engine):
        constant_prices = [100.0] * 100
        result = engine.sharpe_ratio(constant_prices, risk_free_rate=0.02)
        assert result is None

    def test_sharpe_ratio_insufficient_data(self, engine):
        result = engine.sharpe_ratio([100, 101], risk_free_rate=0.02)
        assert result is None

    # --- sortino_ratio ---

    def test_sortino_ratio_positive(self, engine, price_series):
        result = engine.sortino_ratio(price_series, target_return=0.0)
        assert result is not None
        assert result > 0

    def test_sortino_ratio_known_simple(self, engine, simple_price_series):
        result = engine.sortino_ratio(simple_price_series, target_return=0.0)
        assert result is not None

    def test_sortino_ratio_constant_prices(self, engine):
        constant_prices = [100.0] * 100
        result = engine.sortino_ratio(constant_prices, target_return=0.0)
        assert result is None

    # --- historical_var ---

    def test_historical_var_positive(self, engine, price_series):
        result = engine.historical_var(price_series, confidence=0.95)
        assert result >= 0  # VaR is always non-negative (max of 0 and threshold)
        assert result <= 1.0

    def test_historical_var_99_percent(self, engine, price_series):
        var_99 = engine.historical_var(price_series, confidence=0.99)
        var_95 = engine.historical_var(price_series, confidence=0.95)
        assert var_99 >= var_95  # Higher confidence => higher VaR

    def test_historical_var_ascending_prices(self, engine):
        ascending = list(range(100, 200))
        result = engine.historical_var(ascending, confidence=0.95)
        assert result >= 0

    # --- expected_shortfall ---

    def test_expected_shortfall_positive(self, engine, price_series):
        result = engine.expected_shortfall(price_series, confidence=0.95)
        assert result > 0
        assert result <= 1.0

    def test_expected_shortfall_greather_than_var(self, engine, price_series):
        es = engine.expected_shortfall(price_series, confidence=0.95)
        var = engine.historical_var(price_series, confidence=0.95)
        assert es >= var

    # --- capm_beta ---

    def test_capm_beta_known(self, engine):
        # Perfectly correlated: beta should be ~1
        market = [100, 102, 104, 106, 108]
        asset = [100, 102, 104, 106, 108]
        result = engine.capm_beta(asset, market)
        assert result == pytest.approx(1.0, abs=0.01)

    def test_capm_beta_higher(self, engine):
        # Asset moves more than market
        market = [100, 102, 104, 106, 108]
        asset = [100, 104, 108, 106, 112]
        result = engine.capm_beta(asset, market)
        assert result > 1.0

    def test_capm_beta_constant_market(self, engine):
        market = [100.0] * 10
        asset = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]
        result = engine.capm_beta(asset, market)
        assert result is None  # Market variance is zero

    # --- rolling_volatility ---

    def test_rolling_volatility_length(self, engine, price_series):
        results = engine.rolling_volatility(price_series, window=21)
        returns = [price_series[i] / price_series[i - 1] - 1 for i in range(1, len(price_series))]
        assert len(results) == len(returns) - 20  # window size - 1 returns lost

    def test_rolling_volatility_positive(self, engine, price_series):
        results = engine.rolling_volatility(price_series, window=21)
        for r in results:
            assert r > 0

    def test_rolling_volatility_constant_prices(self, engine):
        constant = [100.0] * 100
        results = engine.rolling_volatility(constant, window=21)
        assert all(r == 0.0 for r in results)

    def test_rolling_volatility_invalid_window(self, engine):
        with pytest.raises(ValueError):
            engine.rolling_volatility([100, 101], window=1)
