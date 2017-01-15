from trading import Poloniex, Trade, Order, OrderHistory
from trading.trade_currency import TradeCurrency
from trading.logger import log
import random
import time
from datetime import datetime, timedelta
from enum import Enum


class TradeResult(Enum):
    none = 0
    success = 1
    failure = 2


class ITradeAlgorithm:
    poloniex = None
    currency = None
    start_time = datetime.now()
    highest_bid = 0.0
    lowest_ask = 0.0
    ema1 = 0.0
    ema2 = 0.0
    main_balance = 0.0
    alt_balance = 0.0

    def __init__(self, poloniex, currency):
        assert isinstance(poloniex, Poloniex)
        assert isinstance(currency, TradeCurrency)
        self.poloniex = poloniex
        self.currency = currency
        self.start_time = datetime.now()

        cp_split = currency.currency_pair.split('_')
        self.currency_main = cp_split[0]
        self.currency_alt = cp_split[1]

    def update(self):
        raise NotImplementedError()


class MyTradeAlgorithm(ITradeAlgorithm):
    # combined_order = None
    combined_buy = None
    combined_sell = None
    last_trade_type = TradeResult.none

    def update(self):
            self.update_balances()
            self.update_trade_history()
            self.update_chart_data()

            self.last_trade_type = self.trade_when_profitable()

    def update_trade_history(self):
        time_diff = datetime.now() - self.start_time
        minutes = self.currency.trading_history_in_minutes + (time_diff.total_seconds() / 60.0)
        history = OrderHistory(self.poloniex, minutes, self.currency.currency_pair)

        self.combine_buy_sell_orders(history.orders)

    def combine_buy_sell_orders(self, orders):
        buy_order_rates = []
        sell_order_rates = []

        for i, order in enumerate(orders):
            if order.is_buy():
                buy_order_rates.append(order.rate)
                self.combined_buy = order if self.combined_buy is None else self.combined_buy.combine(order)
            else:
                sell_order_rates.append(order.rate)
                self.combined_sell = order if self.combined_sell is None else self.combined_sell.combine(order)

        # assign more weight to recent trades
        if self.combined_buy is not None:
            self.combined_buy.rate = self.ema(buy_order_rates)
        elif self.currency.initial_buy_rate > 0:
            log(self.currency.currency_pair + ': No previous buys. Using initial rate of ' + str(self.currency.initial_buy_rate) + ' ' + self.currency_main)
            self.combined_buy = Order.from_currency_pair('buy', self.currency.currency_pair)
            self.combined_buy.rate = self.currency.initial_buy_rate

        if self.combined_sell is not None:
            self.combined_sell.rate = self.ema(sell_order_rates)
        elif self.currency.initial_sell_rate > 0:
            log(self.currency.currency_pair + ': No previous sells. Using initial rate of ' + str(self.currency.initial_sell_rate))
            self.combined_sell = Order.from_currency_pair('sell', self.currency.currency_pair)
            self.combined_sell.rate = self.currency.initial_sell_rate

    def update_chart_data(self):
        ticker = self.poloniex.returnTicker()
        if 'error' in ticker:
            raise RuntimeError(ticker['error'])
        else:
            self.highest_bid = float(ticker[self.currency.currency_pair]['highestBid'])
            self.lowest_ask = float(ticker[self.currency.currency_pair]['lowestAsk'])

            start = datetime.now() - timedelta(hours=16)
            chart_data = self.poloniex.returnChartData(currencyPair=self.currency.currency_pair, period=300, start=start)

            ma = []
            for data in chart_data:
                ma.append(data['weightedAverage'])

            self.ema1 = self.ema(ma, int(len(ma) / 2))
            self.ema2 = self.ema(ma, int(len(ma) / 4))

    def update_balances(self):
        balances = self.poloniex.returnBalances()

        if 'error' in balances:
            raise RuntimeError(balances['error'])
        else:
            self.main_balance = float(balances[self.currency_main])
            self.alt_balance = float(balances[self.currency_alt])

    def open_new_position(self):
        can_sell, can_buy = self.can_buy_or_sell()

        if can_sell:
            main_amount, amount = self.calculate_sell_amount()
            if self.last_trade_type != TradeResult.failure:
                log('Attempting to open a new sell order for ' + self.currency.currency_pair, True)
            return self.sell(amount, 0)
        elif can_buy:
            main_amount, amount = self.calculate_buy_amount()
            if self.last_trade_type != TradeResult.failure:
                log('Attempting to open a new buy order for ' + self.currency.currency_pair, True)
            return self.buy(main_amount, amount, 0)

        return TradeResult.none

    def trade_when_profitable(self):
        can_sell, can_buy = self.can_buy_or_sell()

        if can_sell:
            main_amount, amount = self.calculate_sell_amount()
            if self.combined_buy is not None:
                # sell rate / buy rate (assume a fee of 0.25%)
                profit_percent = ((self.highest_bid - (self.highest_bid * 0.0025)) / self.combined_buy.rate) - 1
                combined_buy_amount = (abs(self.combined_buy.amount) + abs(self.combined_buy.amount * profit_percent))
                make_sell = profit_percent > self.currency.min_sell_profit and (self.combined_sell is None or self.combined_sell.amount < combined_buy_amount)
                stop_loss = profit_percent < -self.currency.new_order_threshold and -0.99 > profit_percent < -1.01

                if profit_percent > 0:
                    log('Can sell ' + self.currency.currency_pair + ' at a profit of ' + "{0:.2f}".format(
                        profit_percent * 100) + '% / ' + "{0:.2f}".format(self.currency.min_sell_profit * 100) + '%', make_sell)
                else:
                    log('Can sell ' + self.currency.currency_pair + ' at a loss of ' + "{0:.2f}".format(
                        profit_percent * 100) + '% / ' + "{0:.2f}".format(self.currency.new_order_threshold * -100) + '%', stop_loss)

                if stop_loss:
                    log('Profit percent has fallen below the threshold', True)
                    return self.open_new_position()
                elif make_sell:
                    return self.sell(amount, profit_percent)
            else:
                if self.last_trade_type != TradeResult.failure:
                    log(self.currency.currency_pair + ': No previous buys to compare against')
                if self.combined_sell is None:
                    return self.open_new_position()  # only open one speculative position if none have been opened before
                return TradeResult.failure

        elif can_buy:
            main_amount, amount = self.calculate_buy_amount()
            # 0.0001 is the min btc order amount
            if main_amount >= 0.0001:
                if self.combined_sell is not None:
                    # sell rate / buy rate (assume a fee of 0.25%)
                    profit_percent = (self.combined_sell.rate / (self.lowest_ask + (self.lowest_ask * 0.0025))) - 1
                    combined_sell_amount = (abs(self.combined_sell.amount) + abs(self.combined_sell.amount * profit_percent))
                    make_buy = profit_percent > self.currency.min_buy_profit and (self.combined_buy is None or self.combined_buy.amount < combined_sell_amount)
                    stop_loss = profit_percent < -self.currency.new_order_threshold and -0.99 > profit_percent < -1.01

                    if profit_percent > 0:
                        log('Can buy ' + self.currency.currency_pair + ' at a profit of ' + "{0:.2f}".format(
                            profit_percent * 100) + '% / ' + "{0:.2f}".format(self.currency.min_buy_profit * 100) + '%', make_buy)
                    else:
                        log('Can buy ' + self.currency.currency_pair + ' at a loss of ' + "{0:.2f}".format(
                            profit_percent * 100) + '% / ' + "{0:.2f}".format(self.currency.new_order_threshold * -100) + '%', stop_loss)

                    if stop_loss:
                        log('Profit percent has fallen below the threshold', True)
                        return self.open_new_position()
                    elif make_buy:
                        return self.buy(main_amount, amount, profit_percent)
                else:
                    if self.last_trade_type != TradeResult.failure:
                        log(self.currency.currency_pair + ': No previous sells to compare against')
                    # only open one speculative position if none have been opened before
                    # or if the amount purchased is less than the minimum alt currency specified
                    if self.combined_buy is None or self.combined_buy.amount <= self.currency.min_alt:
                        return self.open_new_position()
                    return TradeResult.failure

        return TradeResult.none

    # make sure the minimum trade amount is reached
    def calculate_sell_amount(self):
        min_trade_offset = 0.0
        main_amount = 0.0
        amount = 0.0
        while main_amount < 0.0001 and self.alt_balance > 0:
            amount = (self.alt_balance * (self.currency.alt_percent + min_trade_offset))
            main_amount = amount * self.highest_bid
            min_trade_offset += 0.01  # keep going up by 1% until the minimum trade is reached

        return main_amount, amount

    # make sure the minimum trade amount is reached
    def calculate_buy_amount(self):
        main_amount = max(self.main_balance * self.currency.main_percent, 0.0001)
        amount = main_amount / self.lowest_ask

        return main_amount, amount

    def sell(self, amount, profit_percent):
        if (self.alt_balance - amount) >= self.currency.min_alt and amount > 0:
            log('Selling ' + str(amount) + ' ' + self.currency_alt + ' at a rate of ' + str(self.highest_bid) + ' ' + self.currency_main, True)
            order = Trade().sell(self.poloniex, self.highest_bid, amount, self.currency.currency_pair)
            if order is not None:
                assert isinstance(order, Order)
                log(str(datetime.now()) + ' - Sold ' + str(order.amount) + ' ' + self.currency_alt + ' for ' + str(
                    order.total) + ' ' + self.currency_main + ' at ' + str(order.rate) + ' ' + self.currency_main + ' for a ' + "{0:.2f}".format(profit_percent * 100) + '% profit', True)
                return TradeResult.success
        elif self.last_trade_type != TradeResult.failure:
            if self.last_trade_type != TradeResult.failure:
                log('Not enough funds in your ' + self.currency_alt + ' account! You need at least ' + str(self.currency.min_alt) + ' ' + self.currency_alt, True)

        return TradeResult.failure

    def buy(self, main_amount, amount, profit_percent):
        if (self.main_balance - main_amount) >= self.currency.min_main:
            log('Buying ' + str(amount) + ' ' + self.currency_alt + ' at a rate of ' + str(self.lowest_ask) + ' ' + self.currency_main, True)
            order = Trade().buy(self.poloniex, self.lowest_ask, amount, self.currency.currency_pair)
            if order is not None:
                assert isinstance(order, Order)
                log(str(datetime.now()) + ' - Bought ' + str(order.amount) + ' ' + self.currency_alt + ' for ' + str(
                    order.total) + ' ' + self.currency_main + ' at ' + str(order.rate) + ' ' + self.currency_main + ' for a ' + "{0:.2f}".format(profit_percent * 100) + '% profit', True)
                return TradeResult.success
        elif self.last_trade_type != TradeResult.failure:
            if self.last_trade_type != TradeResult.failure:
                log('Not enough funds in your ' + self.currency_main + ' account! You need at least ' + str(self.currency.min_main) + ' ' + self.currency_main, True)

        return TradeResult.failure

    def can_buy_or_sell(self):
        can_buy = False
        can_sell = False

        if self.ema1 > 0 and self.ema2 > 0:
            if self.highest_bid > max(self.ema1, self.ema2):
                can_sell = True
            if self.lowest_ask < min(self.ema1, self.ema2):
                can_buy = True
        else:
            log('Error! ema value is not greater than zero', True)

        return can_sell, can_buy

    @staticmethod
    def sma(data, window):
        if len(data) < window:
            return None
        return sum(data[-window:]) / float(window)

    def ema(self, data, window=-1):
        if len(data) == 0:
            return 0
        elif len(data) == 1:
            return data[0]

        if window < 0:
            window = int(len(data) / 2)

        c = 2.0 / (window + 1)
        current_ema = self.sma(data[-window * 2:-window], window)
        for value in data[-window:]:
            current_ema = (c * value) + ((1 - c) * current_ema)
        return current_ema
