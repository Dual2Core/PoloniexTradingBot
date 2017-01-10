class Order:
    number = ''
    rate = 0.0
    total = 0.0     # BTC
    amount = 0.0    # LTC
    currency_pair = 'BTC_LTC'
    fee = 0.0

    def __init__(self, order, currency_pair):
        assert isinstance(order, dict)
        self.number = order['orderNumber']
        self.rate = float(order['rate'])
        self.total = float(order['total'])
        self.amount = float(order['amount'])
        self.fee = float(order['fee'])
        self.currency_pair = currency_pair

        if order['type'] == 'buy':
            self.total *= -1
        else:
            self.amount *= -1

    def type(self):
        if self.total > 0:
            return 'sell'
        return 'buy'
