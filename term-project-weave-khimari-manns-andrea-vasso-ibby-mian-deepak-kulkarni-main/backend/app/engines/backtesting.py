
"""Backtesting engine for evaluating trading strategies on historical data."""

# REVIEW: These three imports are currently unused.
# Remove them if no future helper methods require them.
import math
import random
from collections.abc import Sequence


class BacktestEngine:
    """
    Engine for simulating investment strategies using historical prices.

    Financial convention:
        Portfolio Equity = Cash + Sum(Shares Held * Current Price)

    Assumptions:
        - Historical prices are ordered chronologically.
        - Each asset's price history represents the same trading dates.
        - Fractional shares are permitted.
        - Transaction costs are proportional to traded value.

    IMPORTANT:
        Existing implementation is preserved for review.
        Some methods still contain accounting and valuation bugs.
    """

    def buy_and_hold(
        self,
        prices_by_asset: dict[str, list[float]],
        weights: dict[str, float],
        capital: float = 10000.0
    ) -> list[float]:
        """
        Simulate a buy-and-hold investment strategy.

        A buy-and-hold strategy purchases assets at the beginning
        and maintains those holdings without rebalancing.

        Portfolio value:
            V(t) = SUM(shares[i] * price[i][t])

        Args:
            prices_by_asset: Asset names mapped to historical prices.
            weights: Initial allocation weights, summing to 1.
            capital: Starting portfolio value.

        Returns:
            Daily portfolio equity values.
        """

        # Identify the assets available for investment.
        asset_names = list(prices_by_asset.keys())

        # No assets means there is no strategy to simulate.
        if not asset_names:
            return []

        # Determine how many trading observations exist.
        date_count = len(prices_by_asset[asset_names[0]])

        # All arrays must contain the same number of observations.
        # REVIEW: Matching lengths do not guarantee matching dates.
        # Task B should align prices using their timestamps.
        for name in asset_names:
            if len(prices_by_asset[name]) != date_count:
                raise ValueError(
                    "All asset price series must have the same length"
                )

        # Verify that the portfolio is fully invested.
        weight_sum = sum(weights.values())

        if abs(weight_sum - 1.0) > 1e-9:
            raise ValueError(
                f"Weights must sum to 1.0, got {weight_sum}"
            )

        # REVIEW:
        # Validate capital > 0, nonempty price arrays,
        # positive finite prices, and nonnegative weights.
        # The weights dictionary should match the asset names.

        # Determine how many shares can initially be purchased.
        #
        # Formula:
        # Shares = (Initial Capital * Asset Weight) / Initial Price
        shares = {}

        for asset in asset_names:
            initial_price = prices_by_asset[asset][0]

            if initial_price > 0:
                shares[asset] = (
                    capital * weights[asset]
                ) / initial_price
            else:
                # REVIEW:
                # An invalid initial price should raise ValueError.
                # Silently assigning zero shares loses the allocation.
                shares[asset] = 0.0

        # Calculate the portfolio's value on each historical date.
        #
        # Share quantities remain unchanged throughout the strategy.
        portfolio_values = []

        for date_idx in range(date_count):
            total_value = 0.0

            for asset in asset_names:
                total_value += (
                    shares[asset]
                    * prices_by_asset[asset][date_idx]
                )

            portfolio_values.append(total_value)

        return portfolio_values

    def periodic_rebalancing(
        self,
        prices_by_asset: dict[str, list[float]],
        weights: dict[str, float],
        schedule: list[int],
        trading_cost_rate: float = 0.001,
        capital: float = 10000.0
    ) -> dict:
        """
        Simulate periodic portfolio rebalancing.

        Rebalancing restores asset allocations to target weights
        after market movements cause the allocations to drift.

        Target Asset Value:
            Target[i] = Portfolio Equity * Weight[i]

        Transaction Cost:
            Cost = abs(Shares Traded * Execution Price) * Cost Rate

        Args:
            prices_by_asset: Historical price observations.
            weights: Target portfolio allocation.
            schedule: Trading-day indices on which to rebalance.
            trading_cost_rate: Proportional transaction cost.
            capital: Initial capital.

        Returns:
            Dictionary containing:
                equity_curve
                trade_log
                final_value
        """

        asset_names = list(prices_by_asset.keys())

        if not asset_names:
            return {
                'equity_curve': [],
                'trade_log': [],
                'final_value': 0.0
            }

        # REVIEW:
        # Reuse input validation from buy_and_hold().
        # Check dates, prices, weights, and trading costs.
        date_count = len(prices_by_asset[asset_names[0]])

        # Establish initial positions using allocation weights.
        shares = {}

        for asset in asset_names:
            initial_price = prices_by_asset[asset][0]

            if initial_price > 0:
                shares[asset] = (
                    capital * weights[asset]
                ) / initial_price
            else:
                shares[asset] = 0.0

        # Calculate remaining cash after the initial investment.
        #
        # REVIEW (CRITICAL):
        # Cash must correspond to the actual amount spent buying shares.
        # Avoid computing cash through an indirect condition.
        # Instead, start with capital and deduct each purchase.
        cash = (
            capital * (
                1 - sum(weights[a] for a in asset_names)
            )
            if any(weights[a] != 1.0 for a in asset_names)
            else 0.0
        )

        equity_curve = []
        trade_log = []

        # Process the historical observations chronologically.
        for date_idx in range(date_count):

            # Calculate the market value of current holdings.
            total_value = sum(
                shares[a] * prices_by_asset[a][date_idx]
                for a in asset_names
            )

            # Rebalance only on scheduled dates after initialization.
            #
            # REVIEW:
            # Convert schedule to a set for efficient membership checks.
            # Reject indices outside the available historical range.
            if date_idx in schedule and date_idx > 0:

                # Determine the present market value of each asset.
                current_values = {
                    a: shares[a] * prices_by_asset[a][date_idx]
                    for a in asset_names
                }

                # REVIEW (CRITICAL):
                # Total rebalancing capital should include available cash.
                total_v = sum(current_values.values())

                trades = []

                for asset in asset_names:

                    # Calculate the desired dollar allocation.
                    target_value = total_v * weights[asset]

                    # Convert dollar allocation into target shares.
                    target_shares = (
                        target_value
                        / prices_by_asset[asset][date_idx]
                        if prices_by_asset[asset][date_idx] > 0
                        else 0
                    )

                    # Positive difference means buy.
                    # Negative difference means sell.
                    trade_shares = target_shares - shares[asset]

                    # Absolute trade value determines transaction fees.
                    trade_notional = abs(
                        trade_shares
                        * prices_by_asset[asset][date_idx]
                    )

                    if abs(trade_shares) > 1e-10:

                        trades.append({
                            'date': date_idx,
                            'asset': asset,
                            'shares': trade_shares,
                            'cost': (
                                trade_notional * trading_cost_rate
                            )
                        })

                        # REVIEW (CRITICAL):
                        # Updating shares must also update cash.
                        #
                        # Buying:
                        #     cash -= purchase_cost + transaction_fee
                        #
                        # Selling:
                        #     cash += sale_proceeds - transaction_fee
                        #
                        # This implementation only updates shares here.
                        shares[asset] = target_shares

                if trades:

                    # Sum all transaction fees generated by rebalancing.
                    total_cost = sum(
                        t['cost'] for t in trades
                    )

                    trade_log.extend(trades)

                    # REVIEW (CRITICAL):
                    # Fees are deducted, but actual trade cash flows
                    # are not recorded.
                    cash -= total_cost

            # REVIEW (CRITICAL):
            # Recompute portfolio value after any trades.
            #
            # Correct identity:
            # Equity = Cash + SUM(Shares * Current Price)
            #
            # The current total_value was calculated before rebalancing.
            equity_curve.append(total_value + cash)

        return {
            'equity_curve': equity_curve,
            'trade_log': trade_log,
            'final_value': (
                equity_curve[-1] if equity_curve else 0.0
            )
        }

    def momentum_backtest(
        self,
        prices_by_asset: dict[str, list[float]],
        lookback: int = 126,
        top_k: int = 5,
        trading_cost_rate: float = 0.001,
        initial_capital: float = 10000.0
    ) -> dict:
        """
        Backtest a momentum-based stock selection strategy.

        Momentum measures historical price appreciation.

        Formula:
            Momentum = Current Price / Historical Price - 1

        The highest-ranked assets are selected and assigned
        equal portfolio weights.

        Args:
            prices_by_asset: Historical adjusted closing prices.
            lookback: Number of trading intervals used for momentum.
            top_k: Number of highest-ranked assets to hold.
            trading_cost_rate: Proportional transaction costs.
            initial_capital: Starting capital.

        Returns:
            Dictionary containing:
                equity_curve
                trade_log
                final_value
                total_return
        """

        asset_names = list(prices_by_asset.keys())

        if not asset_names:
            return {
                'equity_curve': [],
                'trade_log': [],
                'final_value': 0.0
            }

        # Determine the number of historical trading observations.
        date_count = len(prices_by_asset[asset_names[0]])

        # Initially, the portfolio contains no stock positions.
        current_shares = {
            a: 0.0 for a in asset_names
        }

        cash = initial_capital

        trade_log = []
        equity_curve = []

        # REVIEW:
        # Validate lookback >= 1, top_k >= 1, and valid prices.
        # All assets must refer to matching trading dates.

        # Rebalance approximately once per month.
        # 21 trading days is a common monthly approximation.
        #
        # The first trading decision occurs after sufficient
        # momentum history is available.
        decision_dates = list(
            range(lookback + 1, date_count, 21)
        )

        for decision_date in decision_dates:

            # Calculate historical momentum for eligible assets.
            #
            # The signal uses data through decision_date - 1.
            # This avoids using the current execution price
            # to calculate the trading signal.
            scores = {}

            for asset in asset_names:

                if (
                    len(prices_by_asset[asset]) >= lookback + 1
                    and decision_date >= lookback
                ):

                    momentum = (
                        prices_by_asset[asset][decision_date - 1]
                        / prices_by_asset[asset][
                            decision_date - 1 - lookback
                        ]
                        - 1
                    )

                    scores[asset] = momentum

            # No eligible assets means no portfolio selection.
            if not scores:
                continue

            # Rank stocks by momentum, highest first.
            sorted_assets = sorted(
                scores.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Select the top-performing assets.
            selected = sorted_assets[:top_k]

            selected_assets = [
                a for a, _ in selected
            ]

            if not selected_assets:
                continue

            # Mark existing holdings to market before rebalancing.
            portfolio_value = sum(
                current_shares[a]
                * prices_by_asset[a][decision_date]
                for a in asset_names
            ) + cash

            # Equally distribute portfolio value across selected assets.
            #
            # Formula:
            # Target Value = Portfolio Equity / Number of Assets
            target_value_per_asset = (
                portfolio_value / len(selected_assets)
            )

            # REVIEW:
            # Target allocations should reserve enough money
            # to pay transaction costs.
            # Otherwise, the strategy may create a negative cash balance.

            # Sell assets that are no longer among the top performers.
            for asset in asset_names:

                if asset not in selected_assets:

                    if current_shares[asset] > 0:

                        sale_value = (
                            current_shares[asset]
                            * prices_by_asset[asset][decision_date]
                        )

                        # Selling incurs a transaction cost.
                        cost = sale_value * trading_cost_rate

                        # Add net proceeds to the cash account.
                        cash += sale_value - cost

                        trade_log.append({
                            'date': decision_date,
                            'asset': asset,
                            'action': 'sell',
                            'shares': current_shares[asset],
                            'cost': cost
                        })

                        # The position has been completely liquidated.
                        current_shares[asset] = 0.0

            # Adjust selected positions toward equal weights.
            for asset in selected_assets:

                target_shares = (
                    target_value_per_asset
                    / prices_by_asset[asset][decision_date]
                    if prices_by_asset[asset][decision_date] > 0
                    else 0
                )

                # Positive delta indicates additional purchases.
                # Negative delta indicates shares should be sold.
                delta_shares = (
                    target_shares - current_shares[asset]
                )

                if abs(delta_shares) > 1e-10:

                    trade_value = abs(
                        delta_shares
                        * prices_by_asset[asset][decision_date]
                    )

                    cost = trade_value * trading_cost_rate

                    # Update cash for the trade's notional amount.
                    #
                    # Positive delta: cash decreases.
                    # Negative delta: cash increases.
                    cash -= (
                        delta_shares
                        * prices_by_asset[asset][decision_date]
                    )

                    # Both buys and sells incur transaction costs.
                    cash -= cost

                    # Update the number of shares currently held.
                    current_shares[asset] = target_shares

                    trade_log.append({
                        'date': decision_date,
                        'asset': asset,
                        'action': (
                            'buy' if delta_shares > 0 else 'sell'
                        ),
                        'shares': abs(delta_shares),
                        'cost': cost
                    })

            # Calculate portfolio value after executing trades.
            equity_curve.append(
                sum(
                    current_shares[a]
                    * prices_by_asset[a][decision_date]
                    for a in asset_names
                ) + cash
            )

        # REVIEW (CRITICAL):
        # The following approach incorrectly reconstructs
        # historical equity after all trading decisions.
        #
        # It uses the final holdings/cash when inspecting earlier dates.
        # Instead, calculate daily portfolio value during the original
        # chronological simulation loop.
        full_equity = []
        equity_idx = 0

        for d in range(date_count):

            if d in decision_dates:

                full_equity.append(
                    equity_curve[equity_idx]
                )

                equity_idx += 1

            else:

                # REVIEW (CRITICAL):
                # This computes current value but does not append it.
                # Instead, the previous value is carried forward,
                # making the equity curve artificially flat.
                value = sum(
                    current_shares[a]
                    * prices_by_asset[a][d]
                    for a in asset_names
                ) + cash

                full_equity.append(
                    full_equity[-1]
                    if full_equity
                    else initial_capital
                )

        # Total Return:
        # Final Portfolio Equity / Initial Capital - 1
        return {
            'equity_curve': full_equity,
            'trade_log': trade_log,
            'final_value': (
                full_equity[-1] if full_equity else 0.0
            ),
            'total_return': (
                full_equity[-1] / initial_capital - 1
                if full_equity and initial_capital > 0
                else 0.0
            )
        }

    def walk_forward_test(
        self,
        prices_by_asset: dict[str, list[float]],
        train_window: int = 252,
        test_window: int = 63,
        rebalance_freq: int = 21
    ) -> dict:
        """
        Simulate rolling out-of-sample strategy evaluation.

        Walk-forward analysis separates data into:
            Training period: Historical information used to develop
                             or configure a strategy.
            Testing period: Future observations not used in training.

        Args:
            prices_by_asset: Historical asset price series.
            train_window: Number of training observations.
            test_window: Number of out-of-sample observations.
            rebalance_freq: Rebalancing frequency.

        Returns:
            Out-of-sample equity curve and performance information.
        """

        asset_names = list(prices_by_asset.keys())

        if not asset_names:
            return {
                'equity_curve': [],
                'final_value': 0.0,
                'total_return': 0.0
            }

        # REVIEW:
        # Validate aligned datasets and window parameters.
        total_length = len(prices_by_asset[asset_names[0]])

        equity_curve = []

        # Start with cash and no investments.
        cash = 10000.0

        shares = {
            a: 0.0 for a in asset_names
        }

        # Slide through historical observations.
        #
        # Each new testing period follows its training window.
        # Testing windows do not overlap because t advances
        # by test_window after each iteration.
        t = 0

        while t + train_window + test_window <= total_length:

            # Extract information available during training.
            train_data = {
                a: prices_by_asset[a][t:t + train_window]
                for a in asset_names
            }

            # The testing period starts after training.
            test_start = t + train_window

            test_end = min(
                test_start + test_window,
                total_length
            )

            # REVIEW:
            # train_data is currently unused.
            # Therefore, the strategy does not truly train
            # or optimize based on historical observations.

            # Extract the out-of-sample testing data.
            test_data = {
                a: prices_by_asset[a][test_start:test_end]
                for a in asset_names
            }

            # The existing implementation uses equal weights.
            #
            # REVIEW:
            # This is a valid benchmark allocation, but it is not
            # a trained strategy because training data is ignored.
            num_assets = len(asset_names)

            target_weight = 1.0 / num_assets

            # Process each trading day in the testing window.
            for i in range(test_end - test_start):

                current_date = test_start + i

                # Calculate the market value of existing holdings.
                portfolio_value = sum(
                    shares[a]
                    * prices_by_asset[a][current_date]
                    for a in asset_names
                ) + cash

                # Rebalance at the chosen frequency.
                if i % rebalance_freq == 0:

                    for asset in asset_names:

                        target_value = (
                            portfolio_value * target_weight
                        )

                        if prices_by_asset[asset][current_date] > 0:

                            # REVIEW (CRITICAL):
                            # Shares are overwritten here, but cash
                            # is not reduced when shares are purchased.
                            #
                            # This artificially creates portfolio wealth.
                            #
                            # Correct approach:
                            # 1. Calculate required trade quantities.
                            # 2. Sell positions and collect proceeds.
                            # 3. Buy positions using available cash.
                            # 4. Deduct transaction costs.
                            # 5. Recalculate equity.
                            shares[asset] = (
                                target_value
                                / prices_by_asset[asset][current_date]
                            )

                # Calculate portfolio equity.
                #
                # REVIEW (CRITICAL):
                # This is inaccurate because cash was not updated
                # when shares changed.
                value = sum(
                    shares[a]
                    * prices_by_asset[a][current_date]
                    for a in asset_names
                ) + cash

                equity_curve.append(value)

            # Advance to the next testing window.
            t += test_window

        final_value = (
            equity_curve[-1] if equity_curve else 0.0
        )

        return {
            'equity_curve': equity_curve,
            'final_value': final_value,
            'total_return': (
                final_value / 10000 - 1
                if final_value > 0
                else 0.0
            ),

            # REVIEW:
            # This formula does not correctly count the number
            # of testing windows completed.
            # Increment an explicit counter inside the while loop.
            'num_windows': max(
                0,
                (total_length - train_window)
                // (test_window + train_window)
            )
        }

    def stress_test(
        self,
        prices_by_asset: dict[str, list[float]],
        weights: dict[str, float],
        scenarios: dict[str, list[float]]
    ) -> dict:
        """
        Calculate hypothetical portfolio responses to market shocks.

        For a fully invested portfolio:

            Scenario Return = SUM(Weight[i] * Shock[i])

        Portfolio Multiplier:
            1 + Scenario Return

        Example:
            60% allocation to stocks with -20% shock.
            40% allocation to bonds with +2% shock.

            Scenario Return = 0.6(-0.20) + 0.4(0.02)
                            = -0.112
                            = -11.2%

        Args:
            prices_by_asset: Historical prices, currently unused.
            weights: Portfolio allocation weights.
            scenarios: Asset-specific hypothetical return shocks.

        Returns:
            Scenario results including return and multiplier.
        """

        # REVIEW:
        # The scenarios annotation should actually be:
        # dict[str, dict[str, float]]
        #
        # Each scenario maps asset names to fractional shocks.
        # Example:
        # {"crash": {"AAPL": -0.30, "MSFT": -0.25}}

        results = {}

        for scenario_name, shocks in scenarios.items():

            # Initialize the portfolio's hypothetical return.
            scenario_return = 0.0

            for asset, weight in weights.items():

                # Missing assets receive a default 0% shock.
                #
                # REVIEW:
                # Validate that each shock is finite and >= -1.
                # An asset cannot lose more than 100% under
                # a standard unlevered return model.
                shock = shocks.get(asset, 0.0)

                # Weighted contribution to the scenario return.
                scenario_return += weight * shock

            results[scenario_name] = {
                'portfolio_return': scenario_return,

                # A multiplier of 0.80 means the portfolio
                # retains 80% of its initial value.
                'portfolio_multiplier': 1 + scenario_return
            }

        return results
