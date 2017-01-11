from threading import Timer

from trading import Poloniex, ITradeAlgorithm, MyTradeAlgorithm, TradeCurrency, log
import time

api_key = 'JA05T2TZ-JYVRPM9G-AR07NWDI-20WXQ5NZ'
api_secret = 'd75a1522554d8ee9bd877e63a0aa38b1c32d082c8b66a556e063080ff45fe9d0eef1b1c406089408cd52216f0a6111daf756b5e56ad490cf835ecb086bc6a8d4'

update_interval = 60 * 5  # update every x seconds

# see trade_currency.py for default values
trade_items = [
    TradeCurrency(currency_pair='BTC_ETH'),
    TradeCurrency(currency_pair='BTC_XMR'),
    TradeCurrency(currency_pair='BTC_LTC'),
    TradeCurrency(currency_pair='BTC_XRP'),
    TradeCurrency(currency_pair='BTC_DASH'),
    TradeCurrency(currency_pair='BTC_SDC'),
]


def update_loop(algorithm):
    assert isinstance(algorithm, ITradeAlgorithm)
    print()
    algorithm.update()

    loop = Timer(update_interval, update_loop, [algorithm])
    loop.start()


def main():
    try:
        poloniex = Poloniex(api_key, api_secret)
        log('Welcome to the Poloniex trading bot!', True)

        for item in trade_items:
            # log('Trading: ' + item.currency_pair, True)
            algorithm = MyTradeAlgorithm(poloniex=poloniex,
                                         alt_percent=item.alt_percent,
                                         main_percent=item.main_percent,
                                         min_profit=item.min_profit,
                                         new_order_threshold=item.new_order_threshold,
                                         ema_diff=item.ema_diff,
                                         min_main=item.min_main,
                                         min_alt=item.min_alt,
                                         history_in_minutes=item.trading_history_in_minutes,
                                         currency_pair=item.currency_pair)
            update_loop(algorithm)
            time.sleep(update_interval / len(trade_items))  # separate each coin loop
    except KeyboardInterrupt:
        quit()


if __name__ == '__main__':
    main()
