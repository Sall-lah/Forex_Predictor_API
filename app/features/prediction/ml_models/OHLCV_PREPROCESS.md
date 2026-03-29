# Feature Documentation

The `extract_ohlcv_features` function generates a comprehensive set of technical indicators and custom features from OHLCV (Open, High, Low, Close, Volume) using TA library. These features are categorized as follows:

### 1. Trend Indicators
These indicators help identify the direction and strength of price movements.
- **`ema_9`, `ema_21`, `ema_50`**: Exponential Moving Averages for 9, 21, and 50 periods, respectively. Used to identify short-term, medium-term, and long-term trends.
- **`adx`**: Average Directional Index. Measures trend strength.
- **`aroon_osc`**: Aroon Oscillator. Measures the strength of a trend and the likelihood of a trend continuation.
- **`cci`**: Commodity Channel Index. Identifies new trends or warning of extreme conditions.
- **`vortex_indicator_pos`, `vortex_indicator_neg`**: Positive and Negative Vortex Indicators. Used to identify the start of a new trend or trend reversals.
- **`macd`, `macd_signal`**: Moving Average Convergence Divergence and its signal line. Identifies momentum changes, potential trend reversals, and trend strength.
- **`kama_indicator`**: Kaufman's Adaptive Moving Average. A moving average that adapts to market volatility.
- **`awesome_oscillator`**: Awesome Oscillator. Measures market momentum.

### 2. Momentum Indicators
These indicators help assess the speed and magnitude of price changes.
- **`rsi_21h`, `rsi_14h`, `rsi_7h`**: Relative Strength Index for 21, 14, and 7 periods. Measures the speed and change of price movements, indicating overbought or oversold conditions.
- **`roc_24h`, `roc_12h`, `roc_4h`, `roc_2h`, `roc_1h`**: Rate of Change for 24, 12, 4, 2, and 1 periods. Measures the percentage change in price over a given period, indicating momentum.
- **`william_r`**: Williams %R. A momentum indicator that measures overbought and oversold levels.
- **`ultimate_oscillator`**: Ultimate Oscillator. Uses weighted averages of three different timeframes to overcome the shortcomings of other oscillators.
- **`stoch`, `stoch_signal`**: Stochastic Oscillator and its signal line. Compares a closing price to its price range over a given time period.
- **`ppo`, `ppo_signal`**: Percentage Price Oscillator and its signal line. Similar to MACD but expresses the difference as a percentage.
- **`stoch_rsi`**: Stochastic RSI. Applies the Stochastic Oscillator formula to RSI values, providing more sensitivity to RSI changes.

### 3. Volatility Indicators
These indicators measure the degree of price variation over time.
- **`atr`**: Average True Range. Measures market volatility by decomposing the entire range of an asset price for that period.
- **`boillinger_wband`, `bollinger_pband`**: Bollinger Band Width and Percentage Bandwidth. Measures the width between the upper and lower Bollinger Bands, and the position of the price relative to the bands.
- **`donchian_channel_wband`, `donchian_channel_pband`**: Donchian Channel Width and Percentage Bandwidth. Measures the range between the highest high and lowest low over a period, and the price's position within it.
- **`keltner_channel_hband`**: Keltner Channel High Band. Helps to identify trend reversals and overbought/oversold conditions.

### 4. Custom Features
These are user-defined features derived from OHLCV data to capture specific market behaviors.
- **`custom_weekly_return`**: Percentage change in close price over 168 hours (weekly).
- **`custom_hl_range_pct`**: The percentage range between high and low price relative to the close price.
- **`custom_trend_consistency`**: A measure of how consistently the close price has been above its 50-period moving average over the last 24 periods.
- **`custom_24h_volatility`, `custom_12h_volatility`, `custom_4h_volatility`, `custom_2h_volatility`**: Rolling standard deviation of percentage change in close price over 24, 12, 4, and 2 hours, respectively. Measures short-term volatility.
- **`custom_close_pos_24h`, `custom_close_pos_12h`, `custom_close_pos_4h`, `custom_close_pos_2h`**: The position of the close price within the rolling high-low range over 24, 12, 6, and 4 hours, respectively. Normalized to be between 0 and 1.
- **`custom_24h_vol_adj_return`, `custom_12h_vol_adj_return`, `custom_4h_vol_adj_return`, `custom_2h_vol_adj_return`**: Volatility-adjusted returns over 24, 12, 4, and 2 hours, calculated by dividing the percentage change in close price by the corresponding rolling volatility.
- **`asset`**: The asset name. either BTCUSD OR ETHUSD. user will send the asset name when doing api request

### 5.Label To Drop
- **`open`**, **`high`**, **`low`**, **`close`**: Drop unnecessary column