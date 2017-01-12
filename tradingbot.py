from threading import Timer

import time
from datetime import datetime

from trading import Poloniex, ITradeAlgorithm, MyTradeAlgorithm, TradeCurrency, log

from configparser import ConfigParser


api_key = ''
api_secret = ''

update_interval = 0
update_separation = 0

trade_items = []


def load_config():
    global api_key, api_secret, update_interval, update_separation, trade_items

    cfg = ConfigParser()
    cfg.read('config.cfg')

    api_key = cfg['API']['key']
    api_secret = cfg['API']['secret']

    update_interval = float(cfg['BOT']['update_interval']) * 60
    update_separation = float(cfg['BOT']['update_separation']) * 60

    currency_pairs = cfg['CURRENCY']['currency_pairs'].split(',')

    for pair in currency_pairs:
        trade_items.append(TradeCurrency(currency_pair=pair,
                                         main_percent=float(cfg['BOT']['main_percent']) / 100.0,
                                         alt_percent=float(cfg['BOT']['alt_percent']) / 100.0,
                                         min_profit=float(cfg['BOT']['min_profit']) / 100.0,
                                         max_buy_order=float(cfg['BOT']['new_currency_threshold']),
                                         new_order_threshold=float(cfg['BOT']['new_order_threshold']) / 100.0,
                                         min_main=float(cfg['BOT']['min_main']),
                                         min_alt=float(cfg['BOT']['min_alt']),
                                         trading_history_in_minutes=int(cfg['BOT']['trading_history'])))


def update_loop(algorithm):
    assert isinstance(algorithm, ITradeAlgorithm)
    algorithm.update()

    loop = Timer(update_interval, update_loop, [algorithm])
    loop.start()


def main():
    try:
        load_config()

        poloniex = Poloniex(api_key, api_secret)
        log('\n\n\n\n' + str(datetime.now()), True)
        log('Welcome to the Poloniex trading bot!', True)

        for item in trade_items:
            algorithm = MyTradeAlgorithm(poloniex=poloniex,
                                         alt_percent=item.alt_percent,
                                         main_percent=item.main_percent,
                                         min_profit=item.min_profit,
                                         max_buy_order=item.max_buy_order,
                                         new_order_threshold=item.new_order_threshold,
                                         min_main=item.min_main,
                                         min_alt=item.min_alt,
                                         history_in_minutes=item.trading_history_in_minutes,
                                         currency_pair=item.currency_pair)
            update_loop(algorithm)
            time.sleep(update_separation)  # separate each coin loop
    except KeyboardInterrupt:
        quit()


if __name__ == '__main__':
    main()
