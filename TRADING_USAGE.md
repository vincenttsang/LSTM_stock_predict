# Trading System Usage Guide

## Overview
The `trading.py` program implements Conservative and Aggressive trading strategies that integrate:
- LSTM predictions (from `inference.py`)
- Random Forest predictions (from `random_forest/` directory)
- Technical indicators (SMA, MACD, RSI, Bollinger Bands)

## Quick Start

### 1. Generate LSTM Predictions
First, run inference to generate LSTM predictions:
```bash
python inference.py --ticker 0005.HK --target_col SMA50_diff --start 2022-10-27 --end 2022-11-28
```
This creates: `predictions/0005.HK_predict.csv`

### 2. Run Trading Simulation
Run the trading system with both strategies:
```bash
python trading.py --ticker 0005.HK --start 2022-10-01 --end 2022-12-01 --strategy both
```

## Command Line Arguments

### Required Arguments
- `--ticker`: Stock ticker symbol (e.g., `0005.HK`)
- `--start`: Trading period start date (format: `YYYY-MM-DD`)
- `--end`: Trading period end date (format: `YYYY-MM-DD`)

### Optional Arguments
- `--strategy`: Choose trading strategy
  - `conservative`: Conservative strategy only (1% position, 5% stop loss)
  - `aggressive`: Aggressive strategy only (3% position, 3% stop loss)
  - `both`: Run both strategies (default)
- `--capital`: Initial capital (default: `100000`)
- `--lstm_path`: Custom path to LSTM predictions CSV (default: auto-detect from `predictions/`)
- `--rf_path`: Custom path to Random Forest predictions CSV (default: auto-detect from `random_forest/`)
- `--output`: Output directory for results (default: `trading_results`)

## Examples

### Example 1: Conservative Strategy Only
```bash
python trading.py --ticker 0005.HK --start 2022-10-01 --end 2022-12-01 --strategy conservative --capital 50000
```

### Example 2: Aggressive Strategy with Custom Paths
```bash
python trading.py --ticker 2318.HK --start 2022-10-01 --end 2022-12-01 \
  --strategy aggressive \
  --lstm_path predictions/2318.HK_predict.csv \
  --rf_path random_forest/2318.HK_predict.csv
```

### Example 3: Both Strategies with Custom Output
```bash
python trading.py --ticker 0288.HK --start 2022-10-01 --end 2022-12-01 \
  --strategy both \
  --capital 200000 \
  --output my_results
```

## Output Files

The program generates the following output structure:
```
trading_results/
├── 0005.HK_conservative/
│   ├── portfolio_history.csv    # Daily portfolio value tracking
│   ├── trades.csv                # All trade records with entry/exit details
│   └── summary.csv               # Performance summary
├── 0005.HK_aggressive/
│   ├── portfolio_history.csv
│   ├── trades.csv
│   └── summary.csv
└── 0005.HK_strategies_comparison.csv  # Side-by-side comparison
```

### File Descriptions

#### portfolio_history.csv
- `Date`: Trading date
- `Portfolio_Value`: Total portfolio value (cash + position)
- `Capital`: Available cash
- `Position_Value`: Value of stock holdings
- `Shares`: Number of shares held

#### trades.csv
- `Date`: Trade execution date
- `Action`: BUY or SELL
- `Price`: Execution price
- `Shares`: Number of shares traded
- `Capital`: Cash after trade
- `Position`: Shares held after trade
- `Profit`: Profit/loss (for SELL trades)
- `Profit_pct`: Percentage profit/loss
- `Reason`: Trading signal that triggered the trade

#### summary.csv
- `initial_capital`: Starting capital
- `final_value`: Ending portfolio value
- `total_return_pct`: Total return percentage
- `max_drawdown_pct`: Maximum drawdown
- `total_trades`: Number of trades executed
- `winning_trades`: Number of profitable trades
- `losing_trades`: Number of losing trades
- `win_rate`: Percentage of winning trades
- `avg_profit`: Average profit per winning trade
- `avg_loss`: Average loss per losing trade

## Strategy Details

### Conservative Strategy
**Position Size:** 50% of portfolio  
**Stop Loss:** 5% below entry  
**Trailing Stop:** 50-day SMA  

**Entry Requirements (need ≥3 + ML):**
1. Trend: Price > 200-day SMA AND Price > 50-day SMA
2. MACD: Crosses above signal line with positive histogram
3. Oversold: RSI < 40 OR price at lower Bollinger Band
4. ML: Both LSTM and Random Forest predict bullish

**Exit Conditions:**
- RSI > 70 AND price at upper Bollinger Band
- MACD bearish crossover
- ML predicts bearish movement
- 5% stop loss triggered
- Price drops below 50-day SMA (trailing stop)

### Aggressive Strategy
**Position Size:** 70% of portfolio  
**Stop Loss:** 3% below entry  
**Trailing Stop:** 20-day SMA  

**Entry Requirements (need ≥2 + ML):**
1. Trend: Price > 200-day SMA AND Price > 50-day SMA
2. MACD: Crosses above signal line with positive histogram
3. Oversold: RSI < 45 OR price at lower Bollinger Band
4. ML: Both LSTM and Random Forest predict bullish

**Exit Conditions:**
- RSI > 70
- MACD bearish crossover
- Price closes below lower Bollinger Band
- ML predicts bearish movement
- 5% stop loss triggered
- Price drops below 50-day SMA (trailing stop)

## Complete Workflow

### Step-by-Step Example for Multiple Tickers

```bash
# 1. Generate LSTM predictions for all tickers
for ticker in 0002.HK 0005.HK 0288.HK 2318.HK 3690.HK; do
  python inference.py --ticker $ticker --target_col SMA50_diff \
    --start 2022-10-27 --end 2022-11-28
done

# 2. Run trading simulations
for ticker in 0002.HK 0005.HK 0288.HK 2318.HK 3690.HK; do
  python trading.py --ticker $ticker \
    --start 2022-10-01 --end 2022-12-01 \
    --strategy both --capital 100000
done

# 3. Review results
ls -la trading_results/
```

## Tips

1. **Date Ranges**: Ensure your inference date range overlaps with your trading date range
2. **ML Predictions**: The system works with or without ML predictions (will use technical indicators only if ML predictions are missing)
3. **Buffer Period**: The system automatically fetches 300 days of historical data before the start date for indicator calculation
4. **Multiple Runs**: You can run the same ticker with different strategies separately or together with `--strategy both`

## Troubleshooting

### No ML predictions found
If you see "WARNING: No ML predictions found", ensure:
- LSTM predictions exist in `predictions/{ticker}_predict.csv`
- Random Forest predictions exist in `random_forest/{ticker}_predict.csv`
- Or specify custom paths with `--lstm_path` and `--rf_path`

### No trades executed
If the strategy doesn't execute any trades:
- Check that the date range has sufficient historical data
- Verify ML predictions cover the trading period
- The entry conditions might be too strict for the given period
- Try the aggressive strategy which has more lenient entry criteria

### Import errors
Make sure you're using the correct conda environment:
```bash
conda activate trading
```
