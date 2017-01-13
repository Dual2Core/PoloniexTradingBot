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

    main_percent = 'main_percent'
    alt_percent = 'alt_percent'
    min_buy_profit = 'min_buy_profit'
    min_sell_profit = 'min_sell_profit'
    new_currency_threshold = 'new_currency_threshold'
    new_order_threshold = 'new_order_threshold'
    min_main = 'min_main'
    min_alt = 'min_alt'
    trading_history = 'trading_history'

    dft_tc = TradeCurrency(currency_pair='',
                           main_percent=float(cfg['BOT'][main_percent]) / 100.0,
                           alt_percent=float(cfg['BOT'][alt_percent]) / 100.0,
                           min_buy_profit=float(cfg['BOT'][min_buy_profit]) / 100.0,
                           min_sell_profit=float(cfg['BOT'][min_sell_profit]) / 100.0,
                           new_currency_threshold=float(cfg['BOT'][new_currency_threshold]),
                           new_order_threshold=float(cfg['BOT'][new_order_threshold]) / 100.0,
                           min_main=float(cfg['BOT'][min_main]),
                           min_alt=float(cfg['BOT'][min_alt]),
                           trading_history_in_minutes=float(cfg['BOT'][trading_history]))

    for pair in currency_pairs:
        # initialize with defaults
        tc = TradeCurrency(currency_pair=pair,
                           main_percent=dft_tc.main_percent,
                           alt_percent=dft_tc.alt_percent,
                           min_buy_profit=dft_tc.min_buy_profit,
                           min_sell_profit=dft_tc.min_sell_profit,
                           new_currency_threshold=dft_tc.new_currency_threshold,
                           new_order_threshold=dft_tc.new_order_threshold,
                           min_main=dft_tc.min_main,
                           min_alt=dft_tc.min_alt,
                           trading_history_in_minutes=dft_tc.trading_history_in_minutes)
        # custom values
        if pair in cfg:
            tc.main_percent = float(cfg[pair][main_percent] if main_percent in cfg[pair] else tc.main_percent)
            tc.alt_percent = float(cfg[pair][alt_percent] if alt_percent in cfg[pair] else tc.alt_percent)
            tc.min_buy_profit = float(cfg[pair][min_buy_profit] if min_buy_profit in cfg[pair] else tc.min_buy_profit)
            tc.min_sell_profit = float(cfg[pair][min_sell_profit] if min_sell_profit in cfg[pair] else tc.min_sell_profit)
            tc.new_currency_threshold = float(cfg[pair][new_currency_threshold] if new_currency_threshold in cfg[pair] else tc.new_currency_threshold)
            tc.new_order_threshold = float(cfg[pair][new_order_threshold] if new_order_threshold in cfg[pair] else tc.new_order_threshold)
            tc.min_main = float(cfg[pair][min_main] if min_main in cfg[pair] else tc.min_main)
            tc.min_alt = float(cfg[pair][min_alt] if min_alt in cfg[pair] else tc.min_alt)
            tc.trading_history_in_minutes = float(cfg[pair][trading_history] if trading_history in cfg[pair] else tc.trading_history_in_minutes)

        trade_items.append(tc)


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
            assert isinstance(item, TradeCurrency)
            algorithm = MyTradeAlgorithm(poloniex=poloniex,
                                         alt_percent=item.alt_percent,
                                         main_percent=item.main_percent,
                                         min_buy_profit=item.min_buy_profit,
                                         min_sell_profit=item.min_sell_profit,
                                         new_currency_threshold=item.new_currency_threshold,
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
