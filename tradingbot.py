import threading
from threading import Timer

from datetime import datetime

from configparser import ConfigParser

from trading import Poloniex, ITradeAlgorithm, MyTradeAlgorithm, TradeCurrency, log


api_key = ''
api_secret = ''

update_interval = 0

trade_currencies = []

lock = threading.Lock()


def load_config():
    global api_key, api_secret, update_interval, trade_currencies

    cfg = ConfigParser()
    cfg.read('config.cfg')

    api_key = cfg['API']['key']
    api_secret = cfg['API']['secret']

    update_interval = float(cfg['BOT']['update_interval']) * 60

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
    initial_buy_rate = 'initial_buy_rate'
    initial_sell_rate = 'initial_sell_rate'

    dft_tc = TradeCurrency(currency_pair='',
                           main_percent=float(cfg['BOT'][main_percent]) / 100.0,
                           alt_percent=float(cfg['BOT'][alt_percent]) / 100.0,
                           min_buy_profit=float(cfg['BOT'][min_buy_profit]) / 100.0,
                           min_sell_profit=float(cfg['BOT'][min_sell_profit]) / 100.0,
                           new_currency_threshold=float(cfg['BOT'][new_currency_threshold]),
                           new_order_threshold=float(cfg['BOT'][new_order_threshold]) / 100.0,
                           min_main=float(cfg['BOT'][min_main]),
                           min_alt=float(cfg['BOT'][min_alt]),
                           trading_history_in_minutes=float(cfg['BOT'][trading_history]),
                           initial_buy_rate=float(cfg['BOT'][initial_buy_rate]),
                           initial_sell_rate=float(cfg['BOT'][initial_sell_rate]))

    for pair in currency_pairs:
        # initialize with defaults
        tc = TradeCurrency.from_tc(dft_tc)
        tc.currency_pair = pair

        # custom values
        if pair in cfg:
            tc.main_percent = float(cfg[pair][main_percent]) / 100 if main_percent in cfg[pair] else tc.main_percent
            tc.alt_percent = float(cfg[pair][alt_percent]) / 100.0 if alt_percent in cfg[pair] else tc.alt_percent
            tc.min_buy_profit = float(cfg[pair][min_buy_profit]) / 100.0 if min_buy_profit in cfg[pair] else tc.min_buy_profit
            tc.min_sell_profit = float(cfg[pair][min_sell_profit]) / 100.0 if min_sell_profit in cfg[pair] else tc.min_sell_profit
            tc.new_currency_threshold = float(cfg[pair][new_currency_threshold] if new_currency_threshold in cfg[pair] else tc.new_currency_threshold)
            tc.new_order_threshold = float(cfg[pair][new_order_threshold]) / 100.0 if new_order_threshold in cfg[pair] else tc.new_order_threshold
            tc.min_main = float(cfg[pair][min_main] if min_main in cfg[pair] else tc.min_main)
            tc.min_alt = float(cfg[pair][min_alt] if min_alt in cfg[pair] else tc.min_alt)
            tc.trading_history_in_minutes = float(cfg[pair][trading_history] if trading_history in cfg[pair] else tc.trading_history_in_minutes)
            tc.initial_buy_rate = float(cfg[pair][initial_buy_rate] if initial_buy_rate in cfg[pair] else tc.initial_buy_rate)
            tc.initial_sell_rate = float(cfg[pair][initial_sell_rate] if initial_sell_rate in cfg[pair] else tc.initial_sell_rate)

        trade_currencies.append(tc)


def update_loop(algorithm):
    with lock:
        assert isinstance(algorithm, ITradeAlgorithm)
        try:
            algorithm.update()
        except Exception as e:
            log('An error occured: ' + str(e.args), True)

        loop = Timer(update_interval, update_loop, [algorithm])
        loop.start()


def main():
    try:
        load_config()

        poloniex = Poloniex(api_key, api_secret)
        log('\n\n\n\n' + str(datetime.now()), True)
        log('Welcome to the Poloniex trading bot!', True)

        for currency in trade_currencies:
            algorithm = MyTradeAlgorithm(poloniex, currency)
            update_loop(algorithm)
    except KeyboardInterrupt:
        quit()


if __name__ == '__main__':
    main()
