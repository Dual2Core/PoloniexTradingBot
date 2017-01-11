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
    alt_percent = 0.0
    main_percent = 0.0
    min_profit = 0.0
    new_order_threshold = 0.0
    ema_diff = 0.0
    min_main = 0.0
    min_alt = 0.0
    history_in_minutes = 0
    start_time = datetime.now()
    highest_bid = 0.0
    lowest_ask = 0.0
    ema1 = 0.0
    ema2 = 0.0
    main_balance = 0.0
    alt_balance = 0.0

    def __init__(self, poloniex, alt_percent, main_percent, min_profit, new_order_threshold, ema_diff, min_main, min_alt, history_in_minutes, currency_pair):
        assert isinstance(poloniex, Poloniex)
        self.poloniex = poloniex
        self.alt_percent = alt_percent
        self.main_percent = main_percent
        self.min_profit = min_profit
        self.new_order_threshold = new_order_threshold
        self.ema_diff = ema_diff
        self.min_main = min_main
        self.min_alt = min_alt
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
                    for j, matching_order in enumerate(history.orders):
                        assert isinstance(matching_order, Order)
                        if j not in found:
                            if matching_order.total < 0 and matching_order.rate < order.rate:
                                found.append(j)
                                trade.buy_order = matching_order
                                break
                elif order.total < 0:
                    trade = Trade(buy=order)
                    self.trades.insert(0, trade)
                    for j, matching_order in enumerate(history.orders):
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
            scd = self.poloniex.returnChartData(currencyPair=self.currency_pair, period=300, start=start1)
            lcd = self.poloniex.returnChartData(currencyPair=self.currency_pair, period=300, start=start2)

            ma1 = []
            ma2 = []
            for data in scd:
                ma1.append(data['weightedAverage'])
            for data in lcd:
                ma2.append(data['weightedAverage'])

            self.ema1 = self.ema(ma1)  # self.sma(ma1, len(ma1))
            self.ema2 = self.ema(ma2)

    def update_balances(self):
        balances = self.poloniex.returnBalances()

        cp_split = self.currency_pair.split('_')
        main_currency = cp_split[0]
        alt_currency = cp_split[1]

        self.main_balance = float(balances[main_currency])
        self.alt_balance = float(balances[alt_currency])

    def update(self):
        try:
            self.update_trade_history()
            self.update_chart_data()
            self.update_balances()
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
                trade = Trade()
                if len(self.trades):
                    trade = self.trades[0]
                self.last_trade_type = self.open_new_position(trade)

        except AttributeError as e:
            log(e.args)

    def open_new_position(self, trade):
        self.trades.insert(0, trade)
        return self.trade_when_profitable(trade)

    def trade_when_profitable(self, trade):
        assert isinstance(trade, Trade)
        can_sell, can_buy = self.can_buy_or_sell()

        if can_sell:
            if trade.empty():
                if self.last_trade_type != TradeResult.failure:
                    log('Opening new sell position for ' + self.currency_pair + ' at ' + str(self.highest_bid), True)
                return self.sell(trade)
            elif trade.is_buy() or trade.complete():
                profit = (self.highest_bid - (self.highest_bid * 0.0025)) - trade.buy_order.rate  # assume a fee of 0.25%
                log('Can sell ' + self.currency_pair + ' at a profit of ' + "{0:.9f}".format(profit))
                if profit < -self.new_order_threshold:
                    return self.open_new_position(Trade())
                elif profit > self.min_profit:
                    return self.sell(trade)

        elif can_buy:
            if trade.empty():
                if self.last_trade_type != TradeResult.failure:
                    log('Opening new buy position for ' + self.currency_pair + ' at ' + str(self.lowest_ask), True)
                return self.buy(trade)
            elif trade.is_sell() or trade.complete():
                profit = trade.sell_order.rate - (self.lowest_ask + (self.lowest_ask * 0.0025))  # assume a fee of 0.25%
                log('Can buy ' + self.currency_pair + ' at a profit of ' + "{0:.9f}".format(profit))
                if profit < -self.new_order_threshold:
                    return self.open_new_position(Trade())
                elif profit > self.min_profit:
                    return self.buy(trade)

        return TradeResult.none

    def sell(self, trade):
        assert isinstance(trade, Trade)
        # if the balance can afford it, sell the full amount of the previous buy otherwise, percent of alt balance
        amount = self.alt_balance * self.alt_percent
        if (trade.is_buy() or trade.complete()) and self.alt_balance > trade.buy_order.amount:
            amount = trade.buy_order.amount
        if (self.alt_balance - amount) > self.min_alt:
            log('Selling ' + str(amount) + ' ' + self.currency_pair + ' at: ' + str(self.highest_bid))
            order = trade.sell(self.poloniex, self.highest_bid, amount, self.currency_pair)
            if order is not None:
                assert isinstance(order, Order)
                log(str(datetime.now()) + ' - Sold ' + str(order.amount) + ' ' + self.currency_pair + ' for ' + str(order.total) + ' at ' + str(order.rate), True)
                return TradeResult.success
        elif self.last_trade_type != TradeResult.failure:
            log('Not enough funds in your ' + self.currency_pair + ' account!', True)

        return TradeResult.failure

    def buy(self, trade):
        assert isinstance(trade, Trade)
        main_amount = self.main_balance * self.main_percent # the amount of main to spend on this order
        if (self.main_balance - main_amount) > self.min_main:
            amount = main_amount / self.lowest_ask
            log('Buying ' + str(amount) + ' ' + self.currency_pair + ' at: ' + str(self.lowest_ask))
            order = trade.buy(self.poloniex, self.lowest_ask, amount, self.currency_pair)
            if order is not None:
                assert isinstance(order, Order)
                log(str(datetime.now()) + ' - Bought ' + str(order.amount) + ' ' + self.currency_pair + ' for ' + str(order.total) + ' at ' + str(order.rate), True)
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
                if self.highest_bid > max(self.ema1, self.ema2):
                    can_sell = True
                if self.lowest_ask < min(self.ema1, self.ema2):
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


# The same as MyTradeAlgorithm, but it doesn't worry about past trades
# Do not use yet!
class GunbotTradeAlgorithm(MyTradeAlgorithm):
    def trade_when_profitable(self, trade):
        assert isinstance(trade, Trade)
        can_sell, can_buy = self.can_buy_or_sell()

        if can_sell:
            profit = self.highest_bid - trade.buy_order.rate
            log('Can sell ' + self.currency_pair + ' at a profit of ' + "{0:.9f}".format(profit))
            if profit < -self.new_order_threshold:
                return self.open_new_position()
            elif profit > self.min_profit:
                return self.sell(trade)

        if can_sell:
            if trade.empty():
                if self.last_trade_type != TradeResult.failure:
                    log('Opening new sell position for ' + self.currency_pair + ' at ' + str(self.highest_bid), True)
                return self.sell(trade)
            else:
                profit = self.highest_bid - trade.buy_order.rate
                log('Can sell ' + self.currency_pair + ' at a profit of ' + "{0:.9f}".format(profit))
                if profit < -self.new_order_threshold:
                    return self.open_new_position()
                elif profit > self.min_profit:
                    return self.sell(trade)

        elif can_buy:
            if trade.empty():
                if self.last_trade_type != TradeResult.failure:
                    log('Opening new buy position for ' + self.currency_pair + ' at ' + str(self.lowest_ask), True)
                return self.buy(trade)
            else:
                profit = trade.sell_order.rate - self.lowest_ask
                log('Can buy ' + self.currency_pair + ' at a profit of ' + "{0:.9f}".format(profit))
                if profit < -self.new_order_threshold:
                    return self.open_new_position()
                elif profit > self.min_profit:
                    return self.buy(trade)

        return TradeResult.none

    def sell(self, trade):
        assert isinstance(trade, Trade)
        # if the balance can afford it, sell the full amount of the previous buy otherwise, 10% of alt balance
        amount = self.alt_balance * self.alt_percent
        log(datetime.now(), True)
        log('Selling ' + str(amount) + ' ' + self.currency_pair + ' at: ' + str(self.highest_bid))
        order = trade.sell(self.poloniex, self.highest_bid, amount, self.currency_pair)
        if order is not None:
            assert isinstance(order, Order)
            log('Sold ' + str(order.amount) + ' ' + self.currency_pair + ' for ' + str(order.total) + ' at ' + str(order.rate), True)
            return TradeResult.success
        return TradeResult.failure
