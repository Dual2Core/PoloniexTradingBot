class TradeCurrency:
    alt_percent = 0.0
    main_percent = 0.0
    min_profit = 0.0
    max_buy_order = 0.0
    new_order_threshold = 0.0
    trading_history_in_minutes = 0
    currency_pair = ''
    min_main = 0.0
    min_alt = 0.0

    def __init__(self, currency_pair,
                 alt_percent,                    # (0-1) sell with 20% of alt currency
                 main_percent,                   # (0-1) buy with 10% of main currency
                 min_profit,                     # (0-1) about 2.3% (the change in BTC price since the last trade)
                 max_buy_order,                  # (BTC) when starting with a new currency don't spend more than this on buy orders
                 new_order_threshold,            # (0-1) if the profit loss is greater than this open a new order
                 min_main,                       # (BTC) reserve at least this much of the main currency
                 min_alt,                        # (ALT) reserve at least this much of the alt currency
                 trading_history_in_minutes):    # gather 1 year of trading history (60 * 24 * 365 * 1)

        self.alt_percent = alt_percent
        self.main_percent = main_percent
        self.min_profit = min_profit
        self.max_buy_order = max_buy_order
        self.new_order_threshold = new_order_threshold
        self.min_main = min_main
        self.min_alt = min_alt
        self.trading_history_in_minutes = trading_history_in_minutes
        self.currency_pair = currency_pair
