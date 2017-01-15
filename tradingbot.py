import threading
from threading import Timer
import random
import time

from datetime import datetime

from configparser import ConfigParser

from trading import Poloniex, ITradeAlgorithm, MyTradeAlgorithm, TradeCurrency, log


api_key = ''
api_secret = ''

update_interval = 0

trade_currencies = []

lock = threading.Lock()

main_percent = 'main_percent'
alt_percent = 'alt_percent'
min_buy_profit = 'min_buy_profit'
min_sell_profit = 'min_sell_profit'
new_order_threshold = 'new_order_threshold'
min_main = 'min_main'
min_alt = 'min_alt'
trading_history = 'trading_history'
initial_buy_rate = 'initial_buy_rate'
initial_sell_rate = 'initial_sell_rate'


def load_defaults(cfg, currency):
    dft_tc = TradeCurrency(currency_pair='',
                           main_percent=float(cfg[currency][main_percent]) / 100.0,
                           alt_percent=float(cfg[currency][alt_percent]) / 100.0,
                           min_buy_profit=float(cfg[currency][min_buy_profit]) / 100.0,
                           min_sell_profit=float(cfg[currency][min_sell_profit]) / 100.0,
                           new_order_threshold=float(cfg[currency][new_order_threshold]) / 100.0,
                           min_main=float(cfg[currency][min_main]),
                           min_alt=float(cfg[currency][min_alt]),
                           trading_history_in_minutes=float(cfg[currency][trading_history]),
                           initial_buy_rate=float(cfg[currency][initial_buy_rate]),
                           initial_sell_rate=float(cfg[currency][initial_sell_rate]))
    return dft_tc


def load_custom(cfg, dft_tc, pair):
    # initialize with defaults
    tc = TradeCurrency.from_tc(dft_tc)
    tc.currency_pair = pair

    # custom values
    if pair in cfg:
        tc.main_percent = float(cfg[pair][main_percent]) / 100 if main_percent in cfg[pair] else tc.main_percent
        tc.alt_percent = float(cfg[pair][alt_percent]) / 100.0 if alt_percent in cfg[pair] else tc.alt_percent
        tc.min_buy_profit = float(cfg[pair][min_buy_profit]) / 100.0 if min_buy_profit in cfg[pair] else tc.min_buy_profit
        tc.min_sell_profit = float(cfg[pair][min_sell_profit]) / 100.0 if min_sell_profit in cfg[pair] else tc.min_sell_profit
        tc.new_order_threshold = float(cfg[pair][new_order_threshold]) / 100.0 if new_order_threshold in cfg[pair] else tc.new_order_threshold
        tc.min_main = float(cfg[pair][min_main] if min_main in cfg[pair] else tc.min_main)
        tc.min_alt = float(cfg[pair][min_alt] if min_alt in cfg[pair] else tc.min_alt)
        tc.trading_history_in_minutes = float(cfg[pair][trading_history] if trading_history in cfg[pair] else tc.trading_history_in_minutes)
        tc.initial_buy_rate = float(cfg[pair][initial_buy_rate] if initial_buy_rate in cfg[pair] else tc.initial_buy_rate)
        tc.initial_sell_rate = float(cfg[pair][initial_sell_rate] if initial_sell_rate in cfg[pair] else tc.initial_sell_rate)

    return tc


def load_config():
    global api_key, api_secret, update_interval, trade_currencies

    cfg = ConfigParser()
    cfg.read('config.cfg')

    api_key = cfg['API']['key']
    api_secret = cfg['API']['secret']

    update_interval = float(cfg['PROCESS']['update_interval']) * 60

    btc_pairs = cfg['CURRENCY']['btc_pairs'].split(',') if 'btc_pairs' in cfg['CURRENCY'] else []
    usdt_pairs = cfg['CURRENCY']['usdt_pairs'].split(',') if 'usdt_pairs' in cfg['CURRENCY'] else []

    dft_tc_btc = load_defaults(cfg, 'BTC')
    dft_tc_usdt = load_defaults(cfg, 'USDT')

    for pair in btc_pairs:
        trade_currencies.append(load_custom(cfg, dft_tc_btc, pair))

    for pair in usdt_pairs:
        trade_currencies.append(load_custom(cfg, dft_tc_usdt, pair))


def update_loop(algorithm):
    with lock:
        assert isinstance(algorithm, ITradeAlgorithm)
        try:
            algorithm.update()
        except Exception as e:
            log('An error occurred: ' + str(e.args), True)

        loop = Timer(update_interval + random.randint(1, 10), update_loop, [algorithm])
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
            time.sleep(random.randint(1, 10))
    except KeyboardInterrupt:
        quit()


if __name__ == '__main__':
    main()
