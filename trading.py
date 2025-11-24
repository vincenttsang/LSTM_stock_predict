"""
Trading System with Conservative and Aggressive Strategies
Integrates LSTM and Random Forest predictions with technical indicators
"""

import argparse
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import os
import subprocess
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands


class TradingStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, ticker, start_date, end_date, initial_capital=100000, 
                 lstm_predictions=None, rf_predictions=None):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0  # Number of shares held
        self.entry_price = 0
        self.trades = []
        self.portfolio_value = []
        
        # Load data
        self.df = self._fetch_data_with_indicators()
        self.lstm_predictions = lstm_predictions
        self.rf_predictions = rf_predictions
        
        # Merge ML predictions
        self._merge_predictions()
        
    def _fetch_data_with_indicators(self):
        """Fetch stock data and calculate technical indicators"""
        # Fetch extra data for indicator calculation
        buffer_start = (datetime.strptime(self.start_date, '%Y-%m-%d') - timedelta(days=300)).strftime('%Y-%m-%d')
        df = yf.download(self.ticker, start=buffer_start, end=self.end_date, progress=False, auto_adjust=False)
        
        if df.empty:
            raise ValueError(f"No data available for {self.ticker}")
        
        # Handle MultiIndex columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        # Calculate SMAs
        df['SMA10'] = SMAIndicator(close, window=10).sma_indicator()
        df['SMA20'] = SMAIndicator(close, window=20).sma_indicator()
        df['SMA50'] = SMAIndicator(close, window=50).sma_indicator()
        df['SMA200'] = SMAIndicator(close, window=200).sma_indicator()
        
        # Calculate MACD
        macd = MACD(close)
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_hist'] = macd.macd_diff()
        
        # Calculate RSI
        df['RSI'] = RSIIndicator(close, window=14).rsi()
        
        # Calculate Bollinger Bands
        bb = BollingerBands(close)
        df['BB_upper'] = bb.bollinger_hband()
        df['BB_middle'] = bb.bollinger_mavg()
        df['BB_lower'] = bb.bollinger_lband()
        
        # Filter to trading period
        df = df[self.start_date:self.end_date].copy()
        
        return df
    
    def _merge_predictions(self):
        """Merge LSTM and Random Forest predictions with stock data"""
        if self.lstm_predictions is not None:
            # LSTM predictions should have Date index
            self.df = self.df.join(self.lstm_predictions[['next_day_SMA50_diff']], how='left')
            self.df.rename(columns={'next_day_SMA50_diff': 'LSTM_prediction'}, inplace=True)
        
        if self.rf_predictions is not None:
            # Random Forest predictions
            rf_df = self.rf_predictions.copy()
            if 'Date' in rf_df.columns:
                # Parse date with format from Random Forest CSV (e.g., "2022/10/27 0:00")
                rf_df['Date'] = pd.to_datetime(rf_df['Date'], format='%Y/%m/%d %H:%M', errors='coerce')
                # Drop rows with invalid dates (metadata rows)
                rf_df = rf_df.dropna(subset=['Date'])
                rf_df.set_index('Date', inplace=True)
            self.df = self.df.join(rf_df[['Random Forest', 'Next Price']], how='left')
            self.df.rename(columns={'Random Forest': 'RF_prediction', 'Next Price': 'RF_actual'}, inplace=True)
    
    def _check_ml_bullish(self, row, prev_close):
        """Check if ML models predict bullish movement for next day"""
        lstm_bullish = False
        rf_bullish = False
        models_available = 0
        
        # LSTM prediction (next day's SMA50_diff)
        if pd.notna(row.get('LSTM_prediction')):
            models_available += 1
            if row['LSTM_prediction'] > 0:  # Positive next-day SMA50_diff means bullish
                lstm_bullish = True
        
        # Random Forest prediction (next day's price)
        if pd.notna(row.get('RF_prediction')):
            models_available += 1
            if row['RF_prediction'] > prev_close:  # Predicts higher next-day price
                rf_bullish = True
        
        # Require BOTH available models to agree
        if models_available == 2:
            return lstm_bullish and rf_bullish
        elif models_available == 1:
            return lstm_bullish or rf_bullish
        else:
            return False
    
    def _check_ml_bearish(self, row, current_price):
        """Check if ML models predict bearish movement for next day"""
        lstm_bearish = False
        rf_bearish = False
        models_available = 0
        
        # LSTM prediction (next day's SMA50_diff)
        if pd.notna(row.get('LSTM_prediction')):
            models_available += 1
            if row['LSTM_prediction'] < 0:  # Negative next-day SMA50_diff means bearish
                lstm_bearish = True
        
        # Random Forest prediction (next day's price)
        if pd.notna(row.get('RF_prediction')):
            models_available += 1
            if row['RF_prediction'] < current_price:  # Predicts lower next-day price
                rf_bearish = True
        
        # Require BOTH available models to agree
        if models_available == 2:
            return lstm_bearish and rf_bearish
        elif models_available == 1:
            return lstm_bearish or rf_bearish
        else:
            return False
    
    def check_entry_signals(self, row, prev_row):
        """Check for entry signals - to be overridden by subclasses"""
        raise NotImplementedError
    
    def check_exit_signals(self, row, prev_row):
        """Check for exit signals - to be overridden by subclasses"""
        raise NotImplementedError
    
    def execute_trade(self, date, action, price, reason):
        """Execute a trade"""
        if action == 'BUY':
            shares_to_buy = int((self.capital * self.position_size) / price)
            if shares_to_buy > 0:
                cost = shares_to_buy * price
                self.capital -= cost
                self.position += shares_to_buy
                self.entry_price = price
                self.trades.append({
                    'Date': date,
                    'Action': 'BUY',
                    'Price': price,
                    'Shares': shares_to_buy,
                    'Capital': self.capital,
                    'Position': self.position,
                    'Reason': reason
                })
        
        elif action == 'SELL' and self.position > 0:
            proceeds = self.position * price
            self.capital += proceeds
            profit = (price - self.entry_price) * self.position
            profit_pct = ((price - self.entry_price) / self.entry_price) * 100
            
            self.trades.append({
                'Date': date,
                'Action': 'SELL',
                'Price': price,
                'Shares': self.position,
                'Capital': self.capital,
                'Position': 0,
                'Profit': profit,
                'Profit_pct': profit_pct,
                'Reason': reason
            })
            
            self.position = 0
            self.entry_price = 0
    
    def run_backtest(self):
        """Run the trading strategy backtest"""
        prev_row = None
        
        for date, row in self.df.iterrows():
            current_price = row['Close']
            
            # Calculate portfolio value
            portfolio_val = self.capital + (self.position * current_price)
            self.portfolio_value.append({
                'Date': date,
                'Portfolio_Value': portfolio_val,
                'Capital': self.capital,
                'Position_Value': self.position * current_price,
                'Shares': self.position
            })
            
            # Skip first row
            if prev_row is None:
                prev_row = row
                continue
            
            # Check for exit signals if we have a position
            if self.position > 0:
                # Check exit signals (including stop loss and trailing stop)
                exit_signal, reason = self.check_exit_signals(row, prev_row)
                if exit_signal:
                    self.execute_trade(date, 'SELL', current_price, reason)
            
            # Check for entry signals if we don't have a position
            elif self.position == 0:
                entry_signal, reason = self.check_entry_signals(row, prev_row)
                if entry_signal:
                    self.execute_trade(date, 'BUY', current_price, reason)
            
            prev_row = row
        
        # Close any open position at the end
        if self.position > 0:
            final_price = self.df.iloc[-1]['Close']
            final_date = self.df.index[-1]
            self.execute_trade(final_date, 'SELL', final_price, 'End of Period')
        
        return self._generate_report()
    
    def _generate_report(self):
        """Generate performance report"""
        portfolio_df = pd.DataFrame(self.portfolio_value)
        trades_df = pd.DataFrame(self.trades)
        
        final_value = portfolio_df.iloc[-1]['Portfolio_Value']
        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100
        
        # Calculate max drawdown
        portfolio_df['Peak'] = portfolio_df['Portfolio_Value'].cummax()
        portfolio_df['Drawdown'] = (portfolio_df['Portfolio_Value'] - portfolio_df['Peak']) / portfolio_df['Peak'] * 100
        max_drawdown = portfolio_df['Drawdown'].min()
        
        # Calculate standard deviation of daily returns
        portfolio_df['Daily_Return'] = portfolio_df['Portfolio_Value'].pct_change() * 100
        std_dev = portfolio_df['Daily_Return'].std()
        
        # Trade statistics
        if len(trades_df) > 0:
            buy_trades = trades_df[trades_df['Action'] == 'BUY']
            sell_trades = trades_df[trades_df['Action'] == 'SELL']
            
            winning_trades = sell_trades[sell_trades['Profit'] > 0] if 'Profit' in sell_trades.columns and len(sell_trades) > 0 else pd.DataFrame()
            losing_trades = sell_trades[sell_trades['Profit'] <= 0] if 'Profit' in sell_trades.columns and len(sell_trades) > 0 else pd.DataFrame()
            
            total_trades = len(buy_trades)
            winning_count = len(winning_trades)
            losing_count = len(losing_trades)
            win_rate = (winning_count / len(sell_trades) * 100) if len(sell_trades) > 0 else 0
            avg_profit = winning_trades['Profit'].mean() if winning_count > 0 else 0
            avg_loss = losing_trades['Profit'].mean() if losing_count > 0 else 0
        else:
            total_trades = 0
            winning_count = 0
            losing_count = 0
            win_rate = 0
            avg_profit = 0
            avg_loss = 0
        
        report = {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return_pct': total_return,
            'max_drawdown_pct': max_drawdown,
            'std_dev': std_dev,
            'total_trades': total_trades,
            'winning_trades': winning_count,
            'losing_trades': losing_count,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
        }
        
        return report, portfolio_df, trades_df


class ConservativeStrategy(TradingStrategy):
    """Conservative trading strategy"""
    
    def __init__(self, *args, **kwargs):
        self.position_size = 0.50  # 50% of portfolio
        self.stop_loss_pct = 0.05  # 5% stop loss
        self.trailing_stop_sma = 'SMA50'
        super().__init__(*args, **kwargs)
    
    def check_entry_signals(self, row, prev_row):
        """
        Conservative Entry: Require at least 3 indicators + ML confirmation
        1. Trend: Price > 200-day SMA and Price > 50-day SMA
        2. MACD: crosses below zero first, then crosses above signal with positive histogram
        3. Oversold: RSI < 40 or price touches lower Bollinger Band
        4. ML: predicts next-day price increase
        """
        signals = []
        
        # Skip if missing critical data
        if pd.isna(row['SMA200']) or pd.isna(row['SMA50']):
            return False, ""
        
        # 1. Trend confirmation
        if row['Close'] > row['SMA200'] and row['Close'] > row['SMA50']:
            signals.append('Trend')
        
        # 2. MACD momentum
        if (pd.notna(prev_row['MACD']) and pd.notna(row['MACD']) and 
            pd.notna(prev_row['MACD_signal']) and pd.notna(row['MACD_signal'])):
            # MACD crosses above signal line with positive histogram
            if (prev_row['MACD'] <= prev_row['MACD_signal'] and 
                row['MACD'] > row['MACD_signal'] and 
                row['MACD_hist'] > 0):
                signals.append('MACD')
        
        # 3. Oversold condition
        if pd.notna(row['RSI']) and row['RSI'] < 40:
            signals.append('RSI_oversold')
        elif pd.notna(row['BB_lower']) and row['Close'] <= row['BB_lower'] * 1.01:  # Within 1% of lower band
            signals.append('BB_oversold')
        
        # 4. ML confirmation (both models must agree)
        if self._check_ml_bullish(row, prev_row['Close']):
            signals.append('ML_bullish')
        
        # Conservative: Need at least 3 signals including ML
        if len(signals) >= 3 and 'ML_bullish' in signals:
            return True, f"Conservative Entry: {', '.join(signals)}"
        
        return False, ""
    
    def check_exit_signals(self, row, prev_row):
        """
        Conservative Exit: Require at least 3 indicators + ML confirmation
        1. Stop Loss: price <= entry * (1 - stop_loss_pct)
        2. Trailing Stop: price < trailing stop SMA
        3. Overbought: RSI > 70
        4. Upper BB: price hits upper Bollinger Band
        5. MACD bearish crossover
        6. ML predicts next-day decrease (both models must agree)
        """
        signals = []
        current_price = row['Close']
        
        # 1. Stop Loss
        if current_price <= self.entry_price * (1 - self.stop_loss_pct):
            signals.append('Stop_Loss')
        
        # 2. Trailing Stop
        if pd.notna(row[self.trailing_stop_sma]) and current_price < row[self.trailing_stop_sma]:
            signals.append('Trailing_Stop')
        
        # 3. Overbought RSI
        if pd.notna(row['RSI']) and row['RSI'] > 70:
            signals.append('RSI_overbought')
        
        # 4. Upper Bollinger Band
        if pd.notna(row['BB_upper']) and row['Close'] >= row['BB_upper'] * 0.99:
            signals.append('BB_upper')
        
        # 5. MACD bearish crossover
        if (pd.notna(prev_row['MACD']) and pd.notna(row['MACD']) and 
            pd.notna(prev_row['MACD_signal']) and pd.notna(row['MACD_signal'])):
            if prev_row['MACD'] >= prev_row['MACD_signal'] and row['MACD'] < row['MACD_signal']:
                signals.append('MACD_bearish')
        
        # 6. ML bearish signal (both models must agree)
        if self._check_ml_bearish(row, row['Close']):
            signals.append('ML_bearish')
        
        # Conservative: Need at least 3 signals including ML
        if len(signals) >= 3 and 'ML_bearish' in signals:
            return True, f"Conservative Exit: {', '.join(signals)}"
        
        return False, ""


class AggressiveStrategy(TradingStrategy):
    """Aggressive trading strategy"""
    
    def __init__(self, *args, **kwargs):
        self.position_size = 0.70  # 70% of portfolio
        self.stop_loss_pct = 0.05  # 5% stop loss
        self.trailing_stop_sma = 'SMA50'
        super().__init__(*args, **kwargs)
    
    def check_entry_signals(self, row, prev_row):
        """
        Aggressive Entry: Require at least 2 indicators + ML confirmation
        Same conditions as conservative but more permissive
        """
        signals = []
        
        # Skip if missing critical data
        if pd.isna(row['SMA200']) or pd.isna(row['SMA50']):
            return False, ""
        
        # 1. Trend confirmation
        if row['Close'] > row['SMA200'] and row['Close'] > row['SMA50']:
            signals.append('Trend')
        
        # 2. MACD momentum
        if (pd.notna(prev_row['MACD']) and pd.notna(row['MACD']) and 
            pd.notna(prev_row['MACD_signal']) and pd.notna(row['MACD_signal'])):
            if (prev_row['MACD'] <= prev_row['MACD_signal'] and 
                row['MACD'] > row['MACD_signal'] and 
                row['MACD_hist'] > 0):
                signals.append('MACD')
        
        # 3. Oversold condition (more lenient)
        if pd.notna(row['RSI']) and row['RSI'] < 45:  # Higher threshold
            signals.append('RSI_oversold')
        elif pd.notna(row['BB_lower']) and row['Close'] <= row['BB_lower'] * 1.02:
            signals.append('BB_oversold')
        
        # 4. ML confirmation (both models must agree)
        if self._check_ml_bullish(row, prev_row['Close']):
            signals.append('ML_bullish')
        
        # Aggressive: Need at least 2 signals including ML
        if len(signals) >= 2 and 'ML_bullish' in signals:
            return True, f"Aggressive Entry: {', '.join(signals)}"
        
        return False, ""
    
    def check_exit_signals(self, row, prev_row):
        """
        Aggressive Exit: Require at least 2 indicators + ML confirmation
        1. Stop Loss: price <= entry * (1 - stop_loss_pct)
        2. Trailing Stop: price < trailing stop SMA
        3. RSI > 70 (overbought)
        4. MACD bearish crossover
        5. Price closes below lower Bollinger Band
        6. ML predicts next-day decrease (both models must agree)
        """
        signals = []
        current_price = row['Close']
        
        # 1. Stop Loss
        if current_price <= self.entry_price * (1 - self.stop_loss_pct):
            signals.append('Stop_Loss')
        
        # 2. Trailing Stop
        if pd.notna(row[self.trailing_stop_sma]) and current_price < row[self.trailing_stop_sma]:
            signals.append('Trailing_Stop')
        
        # 3. Overbought RSI
        if pd.notna(row['RSI']) and row['RSI'] > 70:
            signals.append('RSI_overbought')
        
        # 4. MACD bearish crossover
        if (pd.notna(prev_row['MACD']) and pd.notna(row['MACD']) and 
            pd.notna(prev_row['MACD_signal']) and pd.notna(row['MACD_signal'])):
            if prev_row['MACD'] >= prev_row['MACD_signal'] and row['MACD'] < row['MACD_signal']:
                signals.append('MACD_bearish')
        
        # 5. Price below lower BB
        if pd.notna(row['BB_lower']) and row['Close'] < row['BB_lower']:
            signals.append('BB_lower')
        
        # 6. ML bearish signal (both models must agree)
        if self._check_ml_bearish(row, row['Close']):
            signals.append('ML_bearish')
        
        # Aggressive: Need at least 2 signals including ML
        if len(signals) >= 2 and 'ML_bearish' in signals:
            return True, f"Aggressive Exit: {', '.join(signals)}"
        
        return False, ""


def load_predictions(ticker, start_date, end_date, lstm_path=None, rf_path=None, generate_lstm=True):
    """Load LSTM and Random Forest predictions"""
    lstm_pred = None
    rf_pred = None
    
    # Load or generate LSTM predictions
    if lstm_path and os.path.exists(lstm_path):
        lstm_pred = pd.read_csv(lstm_path, index_col=0)
        lstm_pred.index = pd.to_datetime(lstm_pred.index, format='%Y-%m-%d', errors='coerce')
        print(f"Loaded LSTM predictions from {lstm_path}")
    elif generate_lstm:
        # Generate LSTM predictions by calling inference.py
        print(f"\nGenerating LSTM predictions for {ticker}...")
        default_lstm = f"predictions/{ticker}_predict.csv"
        
        try:
            # Call inference.py with appropriate parameters
            cmd = [
                'python', 'inference.py',
                '--ticker', ticker,
                '--target_col', 'SMA50_diff',
                '--start', start_date,
                '--end', end_date
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("LSTM prediction generation completed.")
            
            # Load the generated predictions
            if os.path.exists(default_lstm):
                lstm_pred = pd.read_csv(default_lstm, index_col=0)
                lstm_pred.index = pd.to_datetime(lstm_pred.index, format='%Y-%m-%d', errors='coerce')
                print(f"Loaded generated LSTM predictions from {default_lstm}")
            else:
                print(f"Warning: Expected LSTM predictions file not found at {default_lstm}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating LSTM predictions: {e}")
            print(f"stderr: {e.stderr}")
        except Exception as e:
            print(f"Error running inference.py: {e}")
    else:
        # Try default path without generation
        default_lstm = f"predictions/{ticker}_predict.csv"
        if os.path.exists(default_lstm):
            lstm_pred = pd.read_csv(default_lstm, index_col=0)
            lstm_pred.index = pd.to_datetime(lstm_pred.index, format='%Y-%m-%d', errors='coerce')
            print(f"Loaded LSTM predictions from {default_lstm}")
    
    # Load Random Forest predictions (skip metadata rows)
    if rf_path and os.path.exists(rf_path):
        rf_pred = pd.read_csv(rf_path, skiprows=[1, 2])  # Skip metadata rows
        print(f"Loaded Random Forest predictions from {rf_path}")
    else:
        # Try default path
        default_rf = f"random_forest/{ticker}_predict.csv"
        if os.path.exists(default_rf):
            rf_pred = pd.read_csv(default_rf, skiprows=[1, 2])  # Skip metadata rows
            print(f"Loaded Random Forest predictions from {default_rf}")
    
    return lstm_pred, rf_pred


def main():
    parser = argparse.ArgumentParser(description='Trading System with ML Integration')
    parser.add_argument('--ticker', type=str, required=True, help='Stock ticker (e.g., 0005.HK)')
    parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--strategy', type=str, choices=['conservative', 'aggressive', 'both'], 
                        default='both', help='Trading strategy')
    parser.add_argument('--capital', type=float, default=100000, help='Initial capital')
    parser.add_argument('--lstm_path', type=str, default=None, help='Path to LSTM predictions CSV')
    parser.add_argument('--rf_path', type=str, default=None, help='Path to Random Forest predictions CSV')
    parser.add_argument('--no_generate_lstm', action='store_true', help='Skip automatic LSTM generation (only load existing)')
    parser.add_argument('--output', type=str, default='trading_results', help='Output directory for results')
    
    args = parser.parse_args()
    
    print("="*80)
    print(f"Trading System for {args.ticker}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Initial Capital: ${args.capital:,.2f}")
    print("="*80)
    
    # Load predictions (with automatic generation if needed)
    lstm_pred, rf_pred = load_predictions(
        ticker=args.ticker,
        start_date=args.start,
        end_date=args.end,
        lstm_path=args.lstm_path,
        rf_path=args.rf_path,
        generate_lstm=not args.no_generate_lstm
    )
    
    if lstm_pred is None and rf_pred is None:
        print("\nWARNING: No ML predictions found. Trading will be based on technical indicators only.")
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    strategies_to_run = []
    if args.strategy in ['conservative', 'both']:
        strategies_to_run.append(('Conservative', ConservativeStrategy))
    if args.strategy in ['aggressive', 'both']:
        strategies_to_run.append(('Aggressive', AggressiveStrategy))
    
    results_summary = []
    
    for strategy_name, StrategyClass in strategies_to_run:
        print(f"\n{'='*80}")
        print(f"Running {strategy_name} Strategy")
        print(f"{'='*80}")
        
        try:
            strategy = StrategyClass(
                ticker=args.ticker,
                start_date=args.start,
                end_date=args.end,
                initial_capital=args.capital,
                lstm_predictions=lstm_pred,
                rf_predictions=rf_pred
            )
            
            report, portfolio_df, trades_df = strategy.run_backtest()
            
            # Print report
            print(f"\n{strategy_name} Strategy Results:")
            print("-" * 50)
            print(f"Initial Capital:      ${report['initial_capital']:,.2f}")
            print(f"Final Value:          ${report['final_value']:,.2f}")
            print(f"Total Return:         {report['total_return_pct']:.2f}%")
            print(f"Max Drawdown:         {report['max_drawdown_pct']:.2f}%")
            print(f"Std Dev (daily):      {report['std_dev']:.2f}%")
            print(f"Total Trades:         {report['total_trades']}")
            print(f"Winning Trades:       {report['winning_trades']}")
            print(f"Losing Trades:        {report['losing_trades']}")
            print(f"Win Rate:             {report['win_rate']:.2f}%")
            print(f"Avg Profit (wins):    ${report['avg_profit']:,.2f}")
            print(f"Avg Loss (losses):    ${report['avg_loss']:,.2f}")
            
            # Save results
            strategy_dir = os.path.join(args.output, f"{args.ticker}_{strategy_name.lower()}")
            os.makedirs(strategy_dir, exist_ok=True)
            
            portfolio_df.to_csv(os.path.join(strategy_dir, 'portfolio_history.csv'))
            trades_df.to_csv(os.path.join(strategy_dir, 'trades.csv'))
            
            # Save report
            report_df = pd.DataFrame([report])
            report_df.to_csv(os.path.join(strategy_dir, 'summary.csv'), index=False)
            
            print(f"\nResults saved to: {strategy_dir}/")
            
            results_summary.append({
                'Strategy': strategy_name,
                'Ticker': args.ticker,
                'Initial_Capital': report['initial_capital'],
                'Final_Value': report['final_value'],
                'Return_pct': report['total_return_pct'],
                'Max_Drawdown_pct': report['max_drawdown_pct'],
                'Total_Trades': report['total_trades'],
                'Win_Rate': report['win_rate']
            })
            
        except Exception as e:
            print(f"Error running {strategy_name} strategy: {e}")
            import traceback
            traceback.print_exc()
    
    # Save combined summary
    if results_summary:
        summary_df = pd.DataFrame(results_summary)
        summary_path = os.path.join(args.output, f"{args.ticker}_strategies_comparison.csv")
        summary_df.to_csv(summary_path, index=False)
        print(f"\n{'='*80}")
        print(f"Strategy comparison saved to: {summary_path}")
        print(f"{'='*80}")


if __name__ == '__main__':
    main()
