class TradeCurrency:
    alt_percent = 0.0
    main_percent = 0.0
    min_buy_profit = 0.0
    min_sell_profit = 0.0
    new_currency_threshold = 0.0
    new_order_threshold = 0.0
    trading_history_in_minutes = 0
    currency_pair = ''
    min_main = 0.0
    min_alt = 0.0

    def __init__(self, currency_pair,
                 alt_percent,
                 main_percent,
                 min_buy_profit,
                 min_sell_profit,
                 new_currency_threshold,
                 new_order_threshold,
                 min_main,
                 min_alt,
                 trading_history_in_minutes):

        self.alt_percent = alt_percent
        self.main_percent = main_percent
        self.min_buy_profit = min_buy_profit
        self.min_sell_profit = min_sell_profit
        self.new_currency_threshold = new_currency_threshold
        self.new_order_threshold = new_order_threshold
        self.min_main = min_main
        self.min_alt = min_alt
        self.trading_history_in_minutes = trading_history_in_minutes
        self.currency_pair = currency_pair
