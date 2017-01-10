from trading import Poloniex, Trade, Order, OrderHistory
from trading.logger import log
from datetime import datetime, timedelta
from enum import Enum


class TradeResult(Enum):
    none = 0
    success = 1
    failure = 2


class ITradeAlgorithm:
    poloniex = None
    currency_pair = ''
    trade_amount = 0.0
    min_profit = 0.0
    new_order_threshold = 0.0
    ema_diff = 0.0
    history_in_minutes = 0
    start_time = datetime.now()
    highest_bid = 0.0
    lowest_ask = 0.0
    ema1 = 0.0
    ema2 = 0.0

    def __init__(self, poloniex, trade_amount, min_profit, new_order_threshold, ema_diff, history_in_minutes, currency_pair):
        assert isinstance(poloniex, Poloniex)
        self.poloniex = poloniex
        self.trade_amount = trade_amount
        self.min_profit = min_profit
        self.new_order_threshold = new_order_threshold
        self.ema_diff = ema_diff
        self.history_in_minutes = history_in_minutes
        self.currency_pair = currency_pair
        self.start_time = datetime.now()

    def update(self):
        raise NotImplementedError()


class MyTradeAlgorithm(ITradeAlgorithm):
    trades = []
    last_trade_type = TradeResult.none

    def update_trade_history(self):
        self.trades.clear()

        time_diff = datetime.now() - self.start_time
        minutes = self.history_in_minutes + (time_diff.total_seconds() / 60.0)
        history = OrderHistory(self.poloniex, minutes, self.currency_pair)

        found = []
        for i, order in enumerate(history.orders):
            assert isinstance(order, Order)
            if i not in found:
                found.append(i)
                if order.total > 0:
                    trade = Trade(sell=order)
                    self.trades.insert(0, trade)
                    for j, matching_order in enumerate(history.orders, i):
                        assert isinstance(matching_order, Order)
                        if j not in found:
                            if matching_order.total < 0 and matching_order.rate < order.rate:
                                found.append(j)
                                trade.buy_order = matching_order
                                break
                elif order.total < 0:
                    trade = Trade(buy=order)
                    self.trades.insert(0, trade)
                    for j, matching_order in enumerate(history.orders, i):
                        assert isinstance(matching_order, Order)
                        if j not in found:
                            if matching_order.total > 0 and matching_order.rate > order.rate:
                                found.append(j)
                                trade.sell_order = matching_order
                                break

    def update_chart_data(self):
        ticker = self.poloniex.returnTicker()
        if 'error' in ticker:
            log(ticker['error'], True)
        else:
            self.highest_bid = float(ticker[self.currency_pair]['highestBid'])
            self.lowest_ask = float(ticker[self.currency_pair]['lowestAsk'])

            start1 = datetime.now() + timedelta(hours=2)
            start2 = datetime.now() + timedelta(hours=4)
            scd = self.poloniex.returnChartData(currencyPair=self.currency_pair, period=900, start=start1)
            lcd = self.poloniex.returnChartData(currencyPair=self.currency_pair, period=900, start=start2)

            ma1 = []
            ma2 = []
            for data in scd:
                ma1.append(data['weightedAverage'])
            for data in lcd:
                ma2.append(data['weightedAverage'])

            self.ema1 = self.ema(ma1)
            self.ema2 = self.ema(ma2)

    def update(self):
        try:
            self.update_trade_history()
            self.update_chart_data()
            incomplete_trades = []

            for trade in self.trades:
                assert isinstance(trade, Trade)
                if not trade.complete():
                    incomplete_trades.append(trade)

            log('Open ' + self.currency_pair + ' trades: ' + str(len(incomplete_trades)))
            if len(incomplete_trades) > 0:
                for trade in incomplete_trades:
                    self.last_trade_type = self.trade_when_profitable(trade)
                    if self.last_trade_type == TradeResult.success:
                        break  # only perform one successful trade per update
            else:
                self.last_trade_type = self.open_new_position()

        except AttributeError as e:
            log(e.args)

    def open_new_position(self):
        self.trades.insert(0, Trade())
        return self.trade_when_profitable(self.trades[0])

    def trade_when_profitable(self, trade):
        assert isinstance(trade, Trade)
        can_sell, can_buy = self.can_buy_or_sell()

        if can_sell and (trade.empty() or trade.is_buy()):
            if trade.empty():
                if self.last_trade_type != TradeResult.failure:
                    log('Opening new sell position for ' + self.currency_pair + ' at ' + str(self.highest_bid), True)
                return self.sell(trade)
            else:
                profit = self.highest_bid - trade.buy_order.rate
                log('can sell ' + self.currency_pair + ' at a profit of ' + "{0:.9f}".format(profit))
                if profit < -self.new_order_threshold:
                    return self.open_new_position()
                elif profit > self.min_profit:
                    return self.sell(trade)

        elif can_buy and (trade.empty() or trade.is_sell()):
            if trade.empty():
                if self.last_trade_type != TradeResult.failure:
                    log('Opening new buy position for ' + self.currency_pair + ' at ' + str(self.lowest_ask), True)
                return self.buy(trade)
            else:
                profit = trade.sell_order.rate - self.lowest_ask
                log('can buy ' + self.currency_pair + ' at a profit of ' + "{0:.9f}".format(profit))
                if profit < -self.new_order_threshold:
                    return self.open_new_position()
                elif profit > self.min_profit:
                    return self.buy(trade)

        return TradeResult.none

    def sell(self, trade):
        assert isinstance(trade, Trade)
        if float(self.poloniex.returnBalances()[self.currency_pair.split('_')[1]]) > self.trade_amount:
            log(datetime.now(), True)
            log('Selling ' + self.currency_pair + ' at: ' + str(self.highest_bid))
            order = trade.sell(self.poloniex, self.highest_bid, self.trade_amount, self.currency_pair)
            if order is not None:
                assert isinstance(order, Order)
                log('Sold ' + str(order.amount) + ' ' + self.currency_pair + ' for ' + str(order.total) + ' at ' + str(order.rate), True)
                return TradeResult.success
        elif self.last_trade_type != TradeResult.failure:
            log('Not enough funds in your ' + self.currency_pair + ' account!', True)
        return TradeResult.failure

    def buy(self, trade):
        assert isinstance(trade, Trade)
        if float(self.poloniex.returnBalances()[self.currency_pair.split('_')[0]]) > self.lowest_ask:
            log(datetime.now(), True)
            log('Buying ' + self.currency_pair + ' at: ' + str(self.lowest_ask))
            order = trade.buy(self.poloniex, self.lowest_ask, self.trade_amount, self.currency_pair)
            if order is not None:
                assert isinstance(order, Order)
                log('Bought ' + str(order.amount) + ' ' + self.currency_pair + ' for ' + str(order.total) + ' at ' + str(order.rate), True)
                return TradeResult.success
        elif self.last_trade_type != TradeResult.failure:
            log('Not enough funds in your ' + self.currency_pair + ' account!', True)
        return TradeResult.failure

    def can_buy_or_sell(self):
        can_buy = False
        can_sell = False

        if self.ema1 > 0 and self.ema2 > 0:
            # ignore areas where the ema's are on top of each other
            ema_diff = abs(self.ema1 - self.ema2)
            if ema_diff > self.ema_diff:
                if self.highest_bid > self.ema1 and self.highest_bid > self.ema2:
                    can_sell = True
                if self.lowest_ask < self.ema1 and self.lowest_ask < self.ema2:
                    can_buy = True

        return can_sell, can_buy

    @staticmethod
    def sma(data, window):
        if len(data) < window:
            return None
        return sum(data[-window:]) / float(window)

    def ema(self, data):
        window = int(len(data) / 2)
        c = 2.0 / (window + 1)
        current_ema = self.sma(data[-window * 2:-window], window)
        for value in data[-window:]:
            current_ema = (c * value) + ((1 - c) * current_ema)
        return current_ema


