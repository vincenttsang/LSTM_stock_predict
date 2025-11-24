### Trading Strategies

## Conservative
# Entry Indicators (Buy/Long):
Trend confirmation: Price > 200-day SMA and Price > 50-day SMA
Momentum: MACD crosses below the zero line first (confirming oversold), then crosses above the signal line with a positive histogram.
Oversold: RSI < 40 or price touches the lower Bollinger Band.
ML model predicts a price increase for the next day/week, aligning with the signal. Use as the final filter—only enter if all prior indicators align and ML confirms.
Require at least 3 indicators/ML aligning (up from 2) to maintain conservatism.
# Exit Indicators (Sell/Close Long):
Take profits when RSI >70 and price hits the upper Bollinger Band, or MACD crosses below the signal line.
Accelerate exit if ML predicts a price decrease (bearish signal) even if indicators are mixed.
Stop-loss: 5% below entry
Trailing stop: Use the 50-period SMA.
# Risk Management:
Portion size: 50% of portfolio

## Aggressive
Here, the ML model enables more proactive entries, using its predictions for timing or overriding minor indicator weaknesses in strong trends.
# Entry Rules (Buy/Long):
Trend confirmation: Price > 200-day SMA and Price > 50-day SMA
Momentum: MACD crosses below the zero line first (confirming oversold), then crosses above the signal line with a positive histogram.
Oversold: RSI < 40 or price touches the lower Bollinger Band.
ML model predicts a price increase for the next day/week, aligning with the signal. Use as the final filter—only enter if all prior indicators align and ML confirms.
Require at least 2 indicators/ML aligning (up from 1) to maintain aggressiveness.
# Exit Rules (Sell/Close Long):
Take profits on RSI >70 or MACD bearish crossover, or when price closes below the lower Bollinger Band.
Accelerate exit if ML predicts a price decrease (bearish signal) even if indicators are mixed.
Stop-loss: 3% below entry 
Trailing stop: Use the 50-period SMA.
# Risk Management:
Portion size: 70% of portfolio

# Steps:
Load ML predictions (LSTM from inference.py CSV output)
Load Random Forest predictions
Fetch historical stock data with technical indicators
Implement Conservative and Aggressive strategies
Simulate trades and track portfolio performance

# Generate LSTM predictions first
python inference.py --ticker 0005.HK --target_col SMA50_diff --start 2022-10-27 --end 2022-11-28

# Run trading simulation
python trading.py --ticker 0005.HK --start 2022-10-27 --end 2025-10-27 --strategy both

conda run -n trading python trading.py --ticker 0005.HK --start 2022-10-27 --end 2025-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 0002.HK --start 2022-10-27 --end 2025-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 3690.HK --start 2022-10-27 --end 2025-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 0288.HK --start 2022-10-27 --end 2025-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 2318.HK --start 2022-10-27 --end 2025-10-27 --strategy both --capital 20000
conda run -n trading python benchmark.py --ticker 2800.HK --start 2022-10-27 --end 2025-10-27 --capital 20000
conda run -n trading python benchmark.py --ticker 2800.HK --start 2022-10-27 --end 2025-10-27 --capital 20000 --compare 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK