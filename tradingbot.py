from threading import Timer

from trading import Poloniex, ITradeAlgorithm, MyTradeAlgorithm, log
import time


class TradeItem:
    trade_amount = 0.0
    min_profit = 0.0
    new_order_threshold = 0.0
    ema_diff = 0.0
    trading_history_in_minutes = 0
    currency_pair = ''

    def __init__(self, currency_pair,
                 trade_amount=0.5,                      # (ALT) deal in half a coin
                 min_profit=.0005,                      # (BTC) about $0.50 profit
                 new_order_threshold=.00015,            # (BTC) if the profit loss is greater than this open a new order
                 ema_diff=0.00001,                      # (BTC) only trade when the ema's are not on top of each other
                 trading_history_in_minutes=525600):    # gather 1 year of trading history (60 * 24 * 365 * 1)

        self.trade_amount = trade_amount
        self.min_profit = min_profit
        self.new_order_threshold = new_order_threshold
        self.ema_diff = ema_diff
        self.trading_history_in_minutes = trading_history_in_minutes
        self.currency_pair = currency_pair


api_key = 'JA05T2TZ-JYVRPM9G-AR07NWDI-20WXQ5NZ'
api_secret = 'd75a1522554d8ee9bd877e63a0aa38b1c32d082c8b66a556e063080ff45fe9d0eef1b1c406089408cd52216f0a6111daf756b5e56ad490cf835ecb086bc6a8d4'

update_interval = 10  # update every x seconds

trade_items = [
    TradeItem(currency_pair='BTC_DASH'),
    TradeItem(currency_pair='BTC_LTC'),  # start with a clean slate...
    # TradeItem(currency_pair='BTC_XMR')
]


def update_loop(algorithm):
    assert isinstance(algorithm, ITradeAlgorithm)
    algorithm.update()

    loop = Timer(update_interval, update_loop, [algorithm])
    loop.start()


def main():
    try:
        poloniex = Poloniex(api_key, api_secret)
        log('Welcome to poloniex trading bot!', True)

        for item in trade_items:
            log('Trading: ' + item.currency_pair, True)
            algorithm = MyTradeAlgorithm(poloniex=poloniex,
                                         trade_amount=item.trade_amount,
                                         min_profit=item.min_profit,
                                         new_order_threshold=item.new_order_threshold,
                                         ema_diff=item.ema_diff,
                                         history_in_minutes=item.trading_history_in_minutes,
                                         currency_pair=item.currency_pair)
            update_loop(algorithm)
            time.sleep(update_interval / 2.0)  # separate each coin loop
    except KeyboardInterrupt:
        quit()


if __name__ == '__main__':
    main()
