# Task A — WEAVE Project Foundation and Architecture

## Overview

Task A establishes the foundational architecture for WEAVE, an educational investment research and portfolio analysis application.

The purpose of this phase is to create a maintainable project structure that allows frontend and backend components to be developed independently while sharing clearly defined interfaces.

This document describes the initial project setup and should be updated to match the official Task A requirements if they differ.




### Frontend

The frontend provides the user-facing application structure, including pages for:

- Learning
- Practice exercises
- Stock research
- Portfolio management
- Historical backtesting

Shared components and TypeScript interfaces support consistent navigation, API communication, and data handling.

### Backend

The backend is organized into separate layers:

**API:** Defines HTTP endpoints and request handling.

**Services:** Coordinates application operations.

**Data:** Handles historical and external market data.

**Engines:** Performs financial calculations and investment analysis.

**Schemas:** Defines request, response, and data validation contracts.

This structure is intended to keep calculation logic independent from data retrieval and frontend rendering.

## Development Setup

### Backend

From the project root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The health endpoint is available at `/health`.

### Frontend

From the project root:

```bash
cd frontend
npm install
npm run dev
```

To verify the frontend:

```bash
npx tsc --noEmit
npm run build
```

## Development Conventions

- Develop changes on feature branches rather than directly on `main`.
- Use descriptive commit messages.
- Keep separate project responsibilities in separate modules.
- Document mathematical assumptions and important interfaces.
- Add tests alongside implemented functionality.
- Do not commit API keys, credentials, virtual environments, or generated dependency folders.

## Implementation Status

The initial application skeleton, dependencies, interfaces, placeholder pages, and backend routing structure have been established.

The initial setup does not imply that every API endpoint or application feature has been fully implemented.

Future development will connect these components to real market data, financial calculations, portfolio simulations, and user-facing functionality.

## Integration Requirements

All backend engines should expose clearly defined inputs and outputs.

Frontend components should communicate through API interfaces rather than directly accessing backend implementation details.

Historical market data must be cleaned and aligned before financial calculations.

## Remaining Verification

Before treating this phase as complete, confirm that:

- The frontend builds successfully.
- The backend starts successfully.
- Required dependencies are declared.
- Imports resolve correctly.
- Environment variables are documented.
- Project directories match the team's agreed architecture.
- Existing tests and startup checks pass.

## Summary

Task A provides the structural foundation for WEAVE. Its primary goal is to make subsequent implementation work modular, testable, and easier to coordinate across the development team.

# TASK B



# Task C — Financial Calculation and Risk Analysis Engine

## Overview

Task C implements the foundational financial calculations required by WEAVE.

The engine processes historical asset prices to calculate returns, momentum, volatility, and downside risk. Additional modules extend these calculations to risk-adjusted performance, portfolio mathematics, and strategy simulation.

The primary design objective is to separate mathematical analysis from market data retrieval and application presentation.

## Architecture

```text
backend/
└── app/
    └── engines/
        ├── calculations.py
        ├── risk_metrics.py
        ├── portfolio_math.py
        ├── backtesting.py
        └── simulations.py
```

The last module, `simulations.py`, is part of the planned advanced architecture and is not required for the five core Task C metrics.

## Financial Conventions

All calculations follow these conventions unless otherwise specified:

| Convention | Value |
|---|---|
| Trading days per year | 252 |
| Six-month lookback | 126 trading intervals |
| Returns | Decimal fractions |
| Percentage price change | Percentage units |
| Volatility | Annualized standard deviation |
| Maximum drawdown | Nonnegative decimal loss |
| Price ordering | Chronological |
| Price inputs | Positive, finite numbers |
| Historical prices | Adjusted closing prices preferred |

Example: a cumulative return of `0.15` represents a 15% gain. A percentage price change of `15.0` represents the same percentage movement.

Financial metrics are historical estimates and do not guarantee future investment performance.

---

## 1. Core Financial Calculations

**Implementation:** `calculations.py`

### 1.1 Simple Returns

Simple returns measure price changes between consecutive observations.

\[
r_t=\frac{P_t}{P_{t-1}}-1
\]

These values are reused throughout the risk and portfolio analysis modules.

### 1.2 Logarithmic Returns

Log returns measure continuously compounded price changes.

\[
g_t=\ln\left(\frac{P_t}{P_{t-1}}\right)
\]

Log returns can be added across consecutive periods and are useful for certain simulation models.

### 1.3 Cumulative Return

Cumulative return measures total price appreciation or depreciation.

\[
R_{\text{cum}}=\frac{P_{\text{end}}}{P_{\text{start}}}-1
\]

Example:

```python
prices = [100, 110, 121]
result = engine.cumulative_return(prices)
# Expected: 0.21
```

A minimum of two prices is required.

### 1.4 Percentage Price Change

\[
\Delta P_{\%}=
\frac{P_{\text{new}}-P_{\text{old}}}
{P_{\text{old}}}\times100
\]

Unlike cumulative return, this method returns percentage units.

Example:

```python
engine.percentage_price_change(100, 110)
# Expected: 10.0
```

### 1.5 Six-Month Momentum

Momentum evaluates historical price performance over a specified lookback.

\[
M_{6m,t}=\frac{P_t}{P_{t-126}}-1
\]

The default requires 127 price observations to calculate 126 trading intervals of performance.

The six-month period is an approximation based on trading sessions, not exact calendar months.

### 1.6 Annualized Volatility

Volatility measures dispersion in daily returns.

Sample standard deviation:

\[
s_r=
\sqrt{\frac{\sum_{t=1}^{n}(r_t-\bar r)^2}{n-1}}
\]

Annualized volatility:

\[
\sigma_{\text{annual}}=s_r\sqrt{252}
\]

This annualization assumes daily return variability can be scaled using the square-root-of-time approximation.

At least three prices are required to calculate two daily returns and their sample standard deviation.

### 1.7 Maximum Drawdown

Maximum drawdown measures the largest observed decline from a historical peak.

Running peak:

\[
H_t=\max_{s\leq t}P_s
\]

Drawdown:

\[
D_t=1-\frac{P_t}{H_t}
\]

Maximum drawdown:

\[
MDD=\max_tD_t
\]

Example:

```python
prices = [100, 120, 90, 110]
result = engine.maximum_drawdown(prices)
# Expected: 0.25
```

The result represents a 25% historical peak-to-trough decline.

---

## 2. Advanced Risk Metrics

**Implementation:** `risk_metrics.py`

These calculations extend the required core engine.

### 2.1 Sharpe Ratio

Measures excess return relative to total volatility.

\[
S=
\frac{\bar r-r_{f,d}}{s_r}\sqrt{252}
\]

Where \(r_{f,d}\) is the effective daily risk-free rate.

The annual rate is converted using:

\[
r_{f,d}=(1+r_{f,a})^{1/252}-1
\]

The method returns `None` when volatility is zero or insufficient observations are available.

### 2.2 Sortino Ratio

Measures excess return relative to downside deviation.

\[
So=
\frac{\bar r-\tau_d}{\sigma_d^-}\sqrt{252}
\]

Where:

\[
\sigma_d^-=
\sqrt{\frac{1}{n}\sum_{t=1}^{n}
\min(0,r_t-\tau_d)^2}
\]

The downside-deviation convention includes all return observations in the denominator.

### 2.3 Historical Value at Risk

Historical VaR estimates a loss threshold at a selected confidence level.

Define historical losses:

\[
L_t=-r_t
\]

Then:

\[
VaR_\alpha=\max(0,Q_\alpha(L))
\]

The implementation uses ascending loss ordering with linear quantile interpolation.

Default confidence level: 95%.

VaR is not a maximum possible loss and does not measure the severity of losses beyond the threshold.

### 2.4 Expected Shortfall

Expected Shortfall estimates the average loss in the worst portion of historical observations.

For confidence level \(\alpha\), the tail proportion is:

\[
1-\alpha
\]

The implemented empirical estimator sorts losses from largest to smallest and includes fractional weighting at the tail boundary.

The result is reported as a nonnegative decimal.

### 2.5 CAPM Beta

Beta estimates an asset's historical sensitivity to a market benchmark.

\[
\beta_i=
\frac{\operatorname{Cov}(r_i,r_m)}
{\operatorname{Var}(r_m)}
\]

The asset and market returns must represent matching dates.

The method returns `None` when the benchmark variance is zero or insufficient paired observations exist.

### 2.6 Rolling Volatility

Calculates annualized sample standard deviation using moving windows.

\[
\sigma_{t,w}=
s(r_{t-w+1},\ldots,r_t)\sqrt{252}
\]

Default window: 21 daily returns.

A 21-return window requires 22 historical prices.

---

## 3. Portfolio Mathematics

**Implementation:** `portfolio_math.py`

### Expected Portfolio Return

\[
E[R_p]=\mathbf w^T\boldsymbol\mu
\]

### Portfolio Variance

\[
\sigma_p^2=\mathbf w^T\Sigma\mathbf w
\]

### Portfolio Volatility

\[
\sigma_p=\sqrt{\mathbf w^T\Sigma\mathbf w}
\]

The covariance matrix and expected returns must use consistent annual or daily time conventions.

### Sharpe-Ratio Optimization

The portfolio optimizer attempts to maximize:

\[
\frac{\mathbf w^T\boldsymbol\mu-r_f}
{\sqrt{\mathbf w^T\Sigma\mathbf w}}
\]

Subject to allocation constraints.

The current implementation uses numerical gradient ascent and should be treated as preliminary.

**Known limitation:** Clamping portfolio weights followed by normalization does not guarantee that individual minimum and maximum allocation constraints remain satisfied.

Additional numerical validation and constrained optimization are required.

### Kelly Criterion

Binary Kelly:

\[
f^*=\frac{bp-(1-p)}{b}
\]

Approximate continuous-return Kelly:

\[
f^*\approx\frac{\mu_e}{\sigma^2}
\]

These estimates rely on strong assumptions about probabilities, payoffs, and expected returns. They are educational allocation models, not guaranteed position-sizing recommendations.

---

## 4. Backtesting Integration

**Implementation:** `backtesting.py`

The backtesting engine includes methods for:

- Buy-and-hold simulation
- Periodic portfolio rebalancing
- Historical momentum strategies
- Walk-forward analysis
- Scenario stress testing

Portfolio equity must satisfy:

\[
V_t=C_t+\sum_iq_{i,t}P_{i,t}
\]

Where \(C_t\) is available cash and \(q_{i,t}\) is the number of shares held.

Transaction costs must be included in cash accounting.

The current backtesting implementation requires further verification of cash accounting, execution timing, and daily portfolio valuation.

Backtesting results should not be considered validated until these issues are resolved.

---

## 5. Input Validation

The calculation engine must account for:

- Empty historical datasets
- Insufficient observations
- Zero or negative prices
- NaN and infinite values
- Invalid lookback lengths
- Inconsistent historical date alignment
- Invalid allocation weights
- Invalid confidence levels
- Zero variance or undefined ratios

Calculation functions should not mutate source datasets.

The backend data layer is responsible for aligning historical prices by actual dates before passing them to the calculation engine.

## 6. Unit Testing

**Test location:** `backend/tests/`

Run the financial calculation tests from the backend directory:

```bash
python -m pytest -q tests/test_calculations.py
```

Run all available backend tests:

```bash
python -m pytest -q
```

### Required Test Cases

| Calculation | Input | Expected Result |
|---|---|---|
| Cumulative return | `[100,110,121]` | `0.21` |
| Negative return | `[100,80]` | `-0.20` |
| Percentage change | `100 → 90` | `-10.0` |
| Maximum drawdown | `[100,120,90,110]` | `0.25` |
| Constant-price volatility | `[100,100,100]` | `0.0` |
| Sharpe with zero volatility | Constant prices | `None` |
| Beta against identical benchmark | Nonconstant identical return series | `1.0` |

Additional tests should verify incorrect inputs, numerical edge cases, and whether original datasets remain unchanged.

The complete integrated test suite has not yet been verified.

---

## 7. Dependencies

The core financial and risk calculations use Python's standard mathematical libraries and existing local modules.

Key imports include:

```python
import math
from collections.abc import Sequence

from app.engines.calculations import (
    TRADING_DAYS_PER_YEAR,
    FinancialCalculationEngine,
    simple_returns,
    sample_std,
    sample_variance,
    sample_covariance,
)
```

The current portfolio optimizer implements matrix operations directly. NumPy and SciPy may be introduced for more robust matrix computation and constrained optimization, but they are not required by the basic formulas documented here.

---

## 8. Implementation Status and Known Limitations

### Implemented

- Core returns and price changes
- Six-month momentum
- Annualized volatility
- Maximum drawdown
- Sample variance, standard deviation, and covariance helpers
- Sharpe and Sortino ratios
- Historical VaR and Expected Shortfall
- CAPM beta
- Rolling volatility
- Initial portfolio mathematics and Kelly sizing
- Initial backtesting methods

### Requires Further Work

- Full integration testing
- Financial boundary-case verification
- Robust portfolio optimization constraints
- Reliable handling of extremely large or small numeric inputs
- Backtesting cash-accounting corrections
- Date-aware financial data alignment
- API service integration
- Performance benchmarking
- Validation against manually calculated fixtures

### Modeling Limitations

Financial calculations are based on historical observations and selected mathematical conventions.

They do not account automatically for all market conditions, liquidity constraints, slippage, taxes, dividends, or changing statistical relationships.

Simulation outputs and optimized portfolios must be presented as model-based estimates rather than guaranteed investment outcomes.

## Summary

Task C establishes WEAVE's reusable financial calculation foundation.

The five required metrics provide essential investment analysis capabilities. Additional risk, portfolio, and backtesting methods extend the architecture toward more advanced research and portfolio evaluation.

The initial implementation is in place, but full correctness and integration must be established through unit tests, financial verification, and further development before production use.

### Task D
### Task E