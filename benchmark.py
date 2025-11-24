"""
Buy and Hold Benchmark Strategy
Generate benchmark performance by buying and holding 2800.HK (Hang Seng Index ETF)
"""

import argparse
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import os


def calculate_buy_and_hold_benchmark(ticker, start_date, end_date, initial_capital):
    """
    Calculate buy and hold benchmark performance
    
    Args:
        ticker: Stock ticker for benchmark (default: 2800.HK - Hang Seng Index ETF)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        initial_capital: Initial investment amount
    
    Returns:
        portfolio_df: Daily portfolio values
        summary: Performance summary
    """
    print(f"\nFetching {ticker} data for benchmark...")
    
    # Fetch stock data
    df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
    
    if df.empty:
        raise ValueError(f"No data available for {ticker} in the specified period")
    
    # Handle MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    
    # Get the first available trading day
    first_price = df['Close'].iloc[0]
    last_price = df['Close'].iloc[-1]
    
    # Calculate number of shares we can buy (limited to 50% position size like conservative strategy)
    position_size = 0.50  # 50% of portfolio
    investment_amount = initial_capital * position_size
    shares = investment_amount / first_price
    remaining_cash = initial_capital - investment_amount
    
    # Calculate daily portfolio values
    portfolio_values = []
    for date, row in df.iterrows():
        current_price = row['Close']
        position_value = shares * current_price
        portfolio_value = remaining_cash + position_value
        portfolio_values.append({
            'Date': date,
            'Price': current_price,
            'Shares': shares,
            'Cash': remaining_cash,
            'Position_Value': position_value,
            'Portfolio_Value': portfolio_value
        })
    
    portfolio_df = pd.DataFrame(portfolio_values)
    
    # Calculate performance metrics
    final_value = portfolio_df.iloc[-1]['Portfolio_Value']
    total_return_pct = ((final_value - initial_capital) / initial_capital) * 100
    
    # Calculate max drawdown
    portfolio_df['Peak'] = portfolio_df['Portfolio_Value'].cummax()
    portfolio_df['Drawdown'] = (portfolio_df['Portfolio_Value'] - portfolio_df['Peak']) / portfolio_df['Peak'] * 100
    max_drawdown_pct = portfolio_df['Drawdown'].min()
    
    # Calculate standard deviation of daily returns
    portfolio_df['Daily_Return'] = portfolio_df['Portfolio_Value'].pct_change() * 100
    std_dev = portfolio_df['Daily_Return'].std()
    
    # Calculate annualized return
    days = (portfolio_df.iloc[-1]['Date'] - portfolio_df.iloc[0]['Date']).days
    years = days / 365.25
    annualized_return = ((final_value / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
    
    summary = {
        'ticker': ticker,
        'start_date': portfolio_df.iloc[0]['Date'].strftime('%Y-%m-%d'),
        'end_date': portfolio_df.iloc[-1]['Date'].strftime('%Y-%m-%d'),
        'initial_capital': initial_capital,
        'position_size_pct': position_size * 100,
        'investment_amount': investment_amount,
        'initial_price': first_price,
        'final_price': last_price,
        'shares': shares,
        'remaining_cash': remaining_cash,
        'final_value': final_value,
        'total_return_pct': total_return_pct,
        'annualized_return_pct': annualized_return,
        'max_drawdown_pct': max_drawdown_pct,
        'std_dev': std_dev,
        'trading_days': len(portfolio_df)
    }
    
    return portfolio_df, summary


def main():
    parser = argparse.ArgumentParser(description='Buy and Hold Benchmark Strategy')
    parser.add_argument('--ticker', type=str, default='2800.HK', 
                        help='Benchmark ticker (default: 2800.HK - Hang Seng Index ETF)')
    parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--capital', type=float, default=100000, help='Initial capital')
    parser.add_argument('--output', type=str, default='trading_results', help='Output directory')
    parser.add_argument('--compare', type=str, nargs='*', 
                        help='Tickers to compare with (e.g., 0005.HK 0002.HK)')
    
    args = parser.parse_args()
    
    print("="*80)
    print(f"Buy and Hold Benchmark Strategy")
    print(f"Ticker: {args.ticker}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Initial Capital: ${args.capital:,.2f}")
    print("="*80)
    
    # Calculate benchmark
    portfolio_df, summary = calculate_buy_and_hold_benchmark(
        ticker=args.ticker,
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital
    )
    
    # Print summary
    print(f"\nBenchmark Results ({args.ticker}):")
    print("-" * 50)
    print(f"Trading Period:       {summary['start_date']} to {summary['end_date']}")
    print(f"Initial Capital:      ${summary['initial_capital']:,.2f}")
    print(f"Position Size:        {summary['position_size_pct']:.1f}% (${summary['investment_amount']:,.2f})")
    print(f"Remaining Cash:       ${summary['remaining_cash']:,.2f}")
    print(f"Initial Price:        ${summary['initial_price']:.2f}")
    print(f"Final Price:          ${summary['final_price']:.2f}")
    print(f"Shares Purchased:     {summary['shares']:.2f}")
    print(f"Final Value:          ${summary['final_value']:,.2f}")
    print(f"Total Return:         {summary['total_return_pct']:.2f}%")
    print(f"Annualized Return:    {summary['annualized_return_pct']:.2f}%")
    print(f"Max Drawdown:         {summary['max_drawdown_pct']:.2f}%")
    print(f"Std Dev (daily):      {summary['std_dev']:.2f}%")
    print(f"Trading Days:         {summary['trading_days']}")
    
    # Save results
    benchmark_dir = os.path.join(args.output, f"{args.ticker}_benchmark")
    os.makedirs(benchmark_dir, exist_ok=True)
    
    portfolio_df.to_csv(os.path.join(benchmark_dir, 'portfolio_history.csv'), index=False)
    
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(os.path.join(benchmark_dir, 'summary.csv'), index=False)
    
    print(f"\nResults saved to: {benchmark_dir}/")
    
    # Compare with trading strategies if specified
    if args.compare:
        print(f"\n{'='*80}")
        print("Comparison with Trading Strategies")
        print(f"{'='*80}")
        
        comparison_data = [{
            'Strategy': f'Benchmark ({args.ticker})',
            'Ticker': args.ticker,
            'Initial_Capital': summary['initial_capital'],
            'Final_Value': summary['final_value'],
            'Return_pct': summary['total_return_pct'],
            'Annualized_Return_pct': summary['annualized_return_pct'],
            'Max_Drawdown_pct': summary['max_drawdown_pct'],
            'Std_Dev': summary['std_dev'],
            'Total_Trades': 1  # Buy and hold = 1 trade (buy at start)
        }]
        
        # Load trading strategy results
        for ticker in args.compare:
            for strategy in ['conservative', 'aggressive']:
                result_path = os.path.join(args.output, f"{ticker}_{strategy}", 'summary.csv')
                if os.path.exists(result_path):
                    strategy_df = pd.read_csv(result_path)
                    
                    # Calculate annualized return for strategy
                    total_return = strategy_df['total_return_pct'].iloc[0]
                    # Estimate years from benchmark
                    years = (portfolio_df.iloc[-1]['Date'] - portfolio_df.iloc[0]['Date']).days / 365.25
                    annualized = ((1 + total_return/100) ** (1/years) - 1) * 100 if years > 0 else 0
                    
                    comparison_data.append({
                        'Strategy': f'{ticker} ({strategy.capitalize()})',
                        'Ticker': ticker,
                        'Initial_Capital': strategy_df['initial_capital'].iloc[0],
                        'Final_Value': strategy_df['final_value'].iloc[0],
                        'Return_pct': strategy_df['total_return_pct'].iloc[0],
                        'Annualized_Return_pct': annualized,
                        'Max_Drawdown_pct': strategy_df['max_drawdown_pct'].iloc[0],
                        'Std_Dev': strategy_df['std_dev'].iloc[0] if 'std_dev' in strategy_df.columns else 0.0,
                        'Total_Trades': strategy_df['total_trades'].iloc[0]
                    })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Sort by return
        comparison_df = comparison_df.sort_values('Return_pct', ascending=False)
        
        # Print comparison table
        print("\nPerformance Comparison:")
        print("-" * 135)
        print(f"{'Strategy':<35} {'Return':<12} {'Ann. Return':<12} {'Max DD':<12} {'Std Dev':<12} {'Trades':<10}")
        print("-" * 135)
        
        for _, row in comparison_df.iterrows():
            print(f"{row['Strategy']:<35} {row['Return_pct']:>10.2f}%  {row['Annualized_Return_pct']:>10.2f}%  "
                  f"{row['Max_Drawdown_pct']:>10.2f}%  {row['Std_Dev']:>10.2f}%  {row['Total_Trades']:>8.0f}")
        
        # Save comparison
        comparison_path = os.path.join(args.output, f'benchmark_comparison_{args.ticker}.csv')
        comparison_df.to_csv(comparison_path, index=False)
        print(f"\nComparison saved to: {comparison_path}")
        print("="*80)


if __name__ == '__main__':
    main()
