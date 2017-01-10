from trading.api import Poloniex
from trading.order_history import OrderHistory


class Trade:
    buy_order = None
    sell_order = None

    def __init__(self, buy=None, sell=None):
        self.buy_order = buy
        self.sell_order = sell

    def buy(self, poloniex, rate, amount, currency_pair='BTC_LTC'):
        assert isinstance(poloniex, Poloniex)
        if self.buy_order is not None:
            raise AssertionError('Cannot place more than one buy order for a trade')

        order = poloniex.buy(currencyPair=currency_pair, rate=rate, amount=amount)
        if 'error' in order:
            print(order['error'])
            return None
        else:
            order_number = order['orderNumber']
            self.buy_order = OrderHistory(poloniex, minutes=15, currency_pair=currency_pair).get_order(order_number)

            return self.buy_order

    def sell(self, poloniex, rate, amount, currency_pair='BTC_LTC'):
        assert isinstance(poloniex, Poloniex)
        if self.sell_order is not None:
            raise AssertionError('Cannot place more than one buy order for a trade')

        order = poloniex.sell(currencyPair=currency_pair, rate=rate, amount=amount)
        if 'error' in order:
            print(order['error'])
            return None
        else:
            order_number = order['orderNumber']
            self.sell_order = OrderHistory(poloniex, minutes=15, currency_pair=currency_pair).get_order(order_number)

            return self.sell_order

    def complete(self):
        return self.buy_order is not None and self.sell_order is not None

    def empty(self):
        return self.buy_order is None and self.sell_order is None

    def is_buy(self):
        return not self.complete() and self.buy_order is not None

    def is_sell(self):
        return not self.complete() and self.sell_order is not None
