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
    min_buy_profit = 0.0
    min_sell_profit = 0.0
    new_currency_threshold = 0.0
    new_order_threshold = 0.0
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

    def __init__(self, poloniex, alt_percent, main_percent, min_buy_profit, min_sell_profit, new_currency_threshold, new_order_threshold, min_main, min_alt, history_in_minutes, currency_pair):
        assert isinstance(poloniex, Poloniex)
        self.poloniex = poloniex
        self.alt_percent = alt_percent
        self.main_percent = main_percent
        self.min_buy_profit = min_buy_profit
        self.min_sell_profit = min_sell_profit
        self.new_currency_threshold = new_currency_threshold
        self.new_order_threshold = new_order_threshold
        self.min_main = min_main
        self.min_alt = min_alt
        self.history_in_minutes = history_in_minutes
        self.currency_pair = currency_pair
        self.start_time = datetime.now()

    def update(self):
        raise NotImplementedError()


class MyTradeAlgorithmOld(ITradeAlgorithm):
    # trades = []
    combined_trade = None
    last_trade_type = TradeResult.none

    def update_trade_history(self):
        # self.trades.clear()

        time_diff = datetime.now() - self.start_time
        minutes = self.history_in_minutes + (time_diff.total_seconds() / 60.0)
        history = OrderHistory(self.poloniex, minutes, self.currency_pair)

        # self.combine_trades(history.orders)
        self.combine_orders(history.orders)

        # found = []
        # for i, order in enumerate(history.orders):
        #     assert isinstance(order, Order)
        #     if i not in found:
        #         found.append(i)
        #
        #         if order.total > 0:
        #             trade = Trade(sell=order)
        #             self.trades.insert(0, trade)
        #             for j, matching_order in enumerate(history.orders):
        #                 assert isinstance(matching_order, Order)
        #                 if j not in found:
        #                     if matching_order.total < 0 and matching_order.rate < order.rate:
        #                         found.append(j)
        #                         trade.buy_order = matching_order
        #                         break
        #         elif order.total < 0:
        #             trade = Trade(buy=order)
        #             self.trades.insert(0, trade)
        #             for j, matching_order in enumerate(history.orders):
        #                 assert isinstance(matching_order, Order)
        #                 if j not in found:
        #                     if matching_order.total > 0 and matching_order.rate > order.rate:
        #                         found.append(j)
        #                         trade.sell_order = matching_order
        #                         break

    def combine_orders(self, orders):
        if len(orders):
            order = orders[0]
            for i, nxt_order in enumerate(orders, 1):
                order.combine(nxt_order)

            if order.amount > 0 > order.total:
                self.combined_trade = Trade(buy=order)
            elif order.amount < 0 < order.total:
                self.combined_trade = Trade(sell=order)
            else:
                self.combined_trade = None

    # def combine_trades(self, orders):
    #     if len(orders) < 2:
    #         return orders
    #
    #     found = []
    #     for i, order in enumerate(orders):
    #         if i not in found:
    #             assert isinstance(order, Order)
    #             found.append(i)
    #             trade = Trade(buy=order) if order.is_buy() else Trade(sell=order)
    #             matching_order = Order.from_currency_pair(('sell' if order.is_buy() else 'buy'), self.currency_pair)
    #
    #             is_buy_trade = trade.is_buy()
    #
    #             for j, nxt_order in enumerate(orders):
    #                 if j not in found:
    #                     assert isinstance(nxt_order, Order)
    #                     if is_buy_trade:
    #                         if nxt_order.is_buy():
    #                             trade.buy_order = trade.buy_order.combine(nxt_order)
    #                             found.append(j)
    #                         else:
    #                             if trade.buy_order.amount + matching_order.amount > 0:
    #                                 matching_order = matching_order.combine(nxt_order)
    #                                 trade.sell_order = matching_order
    #                                 found.append(j)
    #                                 if trade.total_amount() <= 0:
    #                                     break
    #                     else:
    #                         if nxt_order.is_sell():
    #                             trade.sell_order = trade.sell_order.combine(nxt_order)
    #                             found.append(j)
    #                         else:
    #                             if trade.sell_order.amount + matching_order.amount < 0:
    #                                 matching_order = matching_order.combine(nxt_order)
    #                                 trade.buy_order = matching_order
    #                                 found.append(j)
    #                                 if trade.total_amount() >= 0:
    #                                     break
    #             self.trades.insert(0, trade)

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
            log('Updating ' + self.currency_pair)
            try:
                self.update_trade_history()
                self.update_balances()
                self.update_chart_data()
            except Exception:
                log('an error occurred while updating from the server', True)
            # incomplete_trades = []
            #
            # for trade in self.trades:
            #     assert isinstance(trade, Trade)
            #     if not trade.complete():
            #         incomplete_trades.append(trade)

            # log('Open ' + self.currency_pair + ' trades: ' + str(len(incomplete_trades)))
            # if len(incomplete_trades) > 0:
            #     for trade in incomplete_trades:
            #         self.last_trade_type = self.trade_when_profitable(trade)
            #         if self.last_trade_type == TradeResult.success:
            #             break  # only perform one successful trade per update
            # else:
            #     # Go by the last trade if its order wasn't filled
            #     trade = Trade()
            #     if len(self.trades):
            #         if self.trades[0].buy_order.amount - self.trades[0].sell_order.amount > self.min_alt:
            #             log('comparing against last complete trade')
            #             trade = self.trades[0]
            #     self.last_trade_type = self.open_new_position(trade)

            if self.combined_trade is not None:
                self.last_trade_type = self.trade_when_profitable(self.combined_trade)
            else:
                self.last_trade_type = self.open_new_position(Trade())

        except AttributeError as e:
            log(e.args)

    def open_new_position(self, trade):
        # self.trades.insert(0, trade)
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
                elif profit > self.min_sell_profit:
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
                elif profit > self.min_buy_profit:
                    return self.buy(trade)

        return TradeResult.none

    def sell(self, trade):
        assert isinstance(trade, Trade)
        # if the balance can afford it, sell the full amount of the previous buy, otherwise percent of alt balance
        amount = self.alt_balance * self.alt_percent
        if trade.is_buy() or trade.complete():
            amount = min(self.alt_balance - self.min_alt, trade.buy_order.amount)
        if (self.alt_balance - amount) >= self.min_alt:
            log('Selling ' + str(amount) + ' ' + self.currency_pair + ' at: ' + str(self.highest_bid), True)
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
        main_amount = self.main_balance * self.main_percent  # the amount of main to spend on this order
        if (self.main_balance - main_amount) >= self.min_main:
            amount = main_amount / self.lowest_ask
            log('Buying ' + str(amount) + ' ' + self.currency_pair + ' at: ' + str(self.lowest_ask), True)
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


class MyTradeAlgorithm(ITradeAlgorithm):
    # combined_order = None
    combined_buy = None
    combined_sell = None
    last_trade_type = TradeResult.none

    def update_trade_history(self):
        time_diff = datetime.now() - self.start_time
        minutes = self.history_in_minutes + (time_diff.total_seconds() / 60.0)
        history = OrderHistory(self.poloniex, minutes, self.currency_pair)

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

        if self.combined_sell is not None:
            self.combined_sell.rate = self.ema(sell_order_rates)

        if self.combined_buy is not None and self.combined_sell is not None:
            if abs(self.combined_buy.amount + self.combined_sell.amount) <= (self.alt_balance * self.alt_percent):
                log('Combined buys and sells cancel each other for ' + self.currency_pair, True)
                self.combined_buy = None
                self.combined_sell = None

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

        if 'error' in balances:
            log(balances['error'], True)
        else:
            cp_split = self.currency_pair.split('_')
            main_currency = cp_split[0]
            alt_currency = cp_split[1]

            self.main_balance = float(balances[main_currency])
            self.alt_balance = float(balances[alt_currency])

    def update(self):
        try:
            try:
                self.update_balances()
                self.update_trade_history()
                self.update_chart_data()
            except Exception as e:
                log('an error occurred while updating from the server: ' + str(e.args), True)

            self.last_trade_type = self.trade_when_profitable()

        except AttributeError as e:
            log(e.args)

    def open_new_position(self):
        can_sell, can_buy = self.can_buy_or_sell()

        if can_sell:
            main_amount, amount = self.calculate_sell_amount()
            log('Opening a new sell order for ' + self.currency_pair, True)
            return self.sell(amount, 0)
        elif can_buy:
            main_amount, amount = self.calculate_buy_amount()
            log('Opening a new buy order for ' + self.currency_pair, True)
            return self.buy(main_amount, amount, 0)

    def trade_when_profitable(self):
        can_sell, can_buy = self.can_buy_or_sell()

        if can_sell:
            main_amount, amount = self.calculate_sell_amount()
            if self.combined_buy is not None:
                # sell rate / buy rate (assume a fee of 0.25%)
                profit_percent = ((self.highest_bid - (self.highest_bid * 0.0025)) / self.combined_buy.rate) - 1
                log('Can sell ' + self.currency_pair + ' at a profit of ' + "{0:.2f}".format(profit_percent * 100) + '% / ' + "{0:.2f}".format(self.min_sell_profit * 100) + '%')

                if profit_percent < -self.new_order_threshold:
                    log('Profit percent has fallen below the threshold', True)
                    return self.open_new_position()
                elif profit_percent > self.min_sell_profit:
                    return self.sell(amount, profit_percent)
            else:
                log(self.currency_pair + ': No previous buys to compare against', True)
                self.open_new_position()

        elif can_buy:
            main_amount, amount = self.calculate_buy_amount()
            # 0.0001 is the min btc order amount
            if main_amount > 0.0001:
                if self.combined_sell is not None:
                    # sell rate / buy rate (assume a fee of 0.25%)
                    profit_percent = (self.combined_sell.rate / (self.lowest_ask + (self.lowest_ask * 0.0025))) - 1
                    log('Can buy ' + self.currency_pair + ' at a profit of ' + "{0:.2f}".format(profit_percent * 100) + '% / ' + "{0:.2f}".format(self.min_buy_profit * 100) + '%')

                    if profit_percent < -self.new_order_threshold:
                        log('Profit percent has fallen below the threshold', True)
                        return self.open_new_position()
                    elif profit_percent > self.min_buy_profit:
                        return self.buy(main_amount, amount, profit_percent)
                elif self.combined_buy is None or -self.combined_buy.total < self.new_currency_threshold:
                    log(self.currency_pair + ': No previous sells to compare against', True)
                    self.open_new_position()

        return TradeResult.none

    # make sure the minimum trade amount is reached
    def calculate_sell_amount(self):
        min_trade_offset = 0.0
        main_amount = 0.0
        amount = 0.0
        while main_amount < 0.0001 and self.alt_balance > 0:
            amount = (self.alt_balance * (self.alt_percent + min_trade_offset))
            main_amount = amount * self.highest_bid
            min_trade_offset += 0.01  # keep going up by 1% until the minimum trade is reached

        return main_amount, amount

    # make sure the minimum trade amount is reached
    def calculate_buy_amount(self):
        main_amount = max(self.main_balance * self.main_percent, 0.0001)
        amount = main_amount / self.lowest_ask

        return main_amount, amount

    def sell(self, amount, profit_percent):
        if (self.alt_balance - amount) >= self.min_alt and amount > 0:
            log('Selling ' + str(amount) + ' ' + self.currency_pair + ' at: ' + str(self.highest_bid), True)
            order = Trade().sell(self.poloniex, self.highest_bid, amount, self.currency_pair)
            if order is not None:
                assert isinstance(order, Order)
                log(str(datetime.now()) + ' - Sold ' + str(order.amount) + ' ' + self.currency_pair + ' for ' + str(
                    order.total) + ' at ' + str(order.rate) + ' for a ' + "{0:.2f}".format(profit_percent * 100) + '% profit', True)
                return TradeResult.success
        elif self.last_trade_type != TradeResult.failure:
            log('Not enough funds in your ' + self.currency_pair.split('_')[1] + ' account!', True)

        return TradeResult.failure

    def buy(self, main_amount, amount, profit_percent):
        if (self.main_balance - main_amount) >= self.min_main:
            log('Buying ' + str(amount) + ' ' + self.currency_pair + ' at: ' + str(self.lowest_ask), True)
            order = Trade().buy(self.poloniex, self.lowest_ask, amount, self.currency_pair)
            if order is not None:
                assert isinstance(order, Order)
                log(str(datetime.now()) + ' - Bought ' + str(order.amount) + ' ' + self.currency_pair + ' for ' + str(
                    order.total) + ' at ' + str(order.rate) + ' for a ' + "{0:.2f}".format(profit_percent * 100) + '% profit', True)
                return TradeResult.success
        elif self.last_trade_type != TradeResult.failure:
            log('Not enough funds in your ' + self.currency_pair.split('_')[0] + ' account!', True)

        return TradeResult.failure

    def can_buy_or_sell(self):
        can_buy = False
        can_sell = False

        if self.ema1 > 0 and self.ema2 > 0:
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
        if len(data) == 0:
            return 0
        elif len(data) == 1:
            return data[0]

        window = int(len(data) / 2)
        c = 2.0 / (window + 1)
        current_ema = self.sma(data[-window * 2:-window], window)
        for value in data[-window:]:
            current_ema = (c * value) + ((1 - c) * current_ema)
        return current_ema
