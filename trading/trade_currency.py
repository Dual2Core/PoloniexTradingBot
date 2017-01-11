class TradeCurrency:
    alt_percent = 0.0
    main_percent = 0.0
    min_profit = 0.0
    new_order_threshold = 0.0
    ema_diff = 0.0
    trading_history_in_minutes = 0
    currency_pair = ''
    min_main = 0.0
    min_alt = 0.0

    def __init__(self, currency_pair,
                 alt_percent=0.5,                       # (0-1) deal in 50% of alt currency
                 main_percent=0.1,                      # (0-1) deal in 10% of main currency
                 min_profit=.00035,                     # (BTC) about $0.35 (the change in BTC price since the last trade)
                 new_order_threshold=.005,              # (BTC) if the profit loss is greater than this open a new order
                 ema_diff=0.000001,                     # (BTC) only trade when the ema's are not on top of each other
                 min_main=0.0005,                       # (BTC) reserve at least this much of the main currency
                 min_alt=0.01,                          # (ALT) reserve at least this much of the alt currency
                 trading_history_in_minutes=525600):    # gather 1 year of trading history (60 * 24 * 365 * 1)

        self.alt_percent = alt_percent
        self.main_percent = main_percent
        self.min_profit = min_profit
        self.new_order_threshold = new_order_threshold
        self.ema_diff = ema_diff
        self.min_main = min_main
        self.min_alt = min_alt
        self.trading_history_in_minutes = trading_history_in_minutes
        self.currency_pair = currency_pair
