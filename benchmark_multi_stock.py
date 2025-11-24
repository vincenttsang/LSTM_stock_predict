"""
Multi-Stock Buy and Hold Benchmark Strategy
Buy 5 stocks on the first trading day and hold throughout the entire period
Each stock gets equal allocation (e.g., $20,000 each for $100,000 total)
"""

import argparse
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import os


def calculate_multi_stock_benchmark(tickers, start_date, end_date, capital_per_stock):
    """
    Calculate buy and hold performance for multiple stocks
    
    Args:
        tickers: List of stock tickers
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        capital_per_stock: Capital allocated per stock
    
    Returns:
        combined_portfolio_df: Daily portfolio values for all stocks combined
        individual_portfolios: Dictionary of individual stock portfolios
        summary: Performance summary
    """
    print(f"\nFetching data for {len(tickers)} stocks...")
    print(f"Capital per stock: ${capital_per_stock:,.2f}")
    print(f"Total capital: ${capital_per_stock * len(tickers):,.2f}")
    
    individual_portfolios = {}
    all_dates = set()
    
    # Fetch data for each stock
    for ticker in tickers:
        print(f"  Loading {ticker}...")
        df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
        
        if df.empty:
            print(f"  ✗ No data available for {ticker}")
            continue
        
        # Handle MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        
        # Get first price and calculate shares to buy
        first_price = df['Close'].iloc[0]
        shares = capital_per_stock / first_price
        
        # Calculate daily portfolio values for this stock
        portfolio_values = []
        for date, row in df.iterrows():
            current_price = row['Close']
            position_value = shares * current_price
            portfolio_values.append({
                'Date': date,
                'Price': current_price,
                'Shares': shares,
                'Position_Value': position_value
            })
            all_dates.add(date)
        
        stock_df = pd.DataFrame(portfolio_values)
        individual_portfolios[ticker] = {
            'df': stock_df,
            'first_price': first_price,
            'last_price': df['Close'].iloc[-1],
            'shares': shares,
            'initial_value': capital_per_stock,
            'final_value': stock_df['Position_Value'].iloc[-1]
        }
        
        print(f"  ✓ {ticker}: {shares:.2f} shares @ ${first_price:.2f} = ${capital_per_stock:,.2f}")
    
    if not individual_portfolios:
        raise ValueError("No valid stock data found!")
    
    # Combine all portfolios by date
    all_dates = sorted(list(all_dates))
    combined_data = []
    
    for date in all_dates:
        total_value = 0
        date_valid = True
        
        # Sum portfolio values for this date across all stocks
        for ticker, portfolio in individual_portfolios.items():
            stock_df = portfolio['df']
            date_row = stock_df[stock_df['Date'] == date]
            
            if not date_row.empty:
                total_value += date_row['Position_Value'].iloc[0]
            else:
                # If any stock is missing data for this date, skip it
                date_valid = False
                break
        
        if date_valid:
            combined_data.append({
                'Date': date,
                'Portfolio_Value': total_value
            })
    
    combined_portfolio_df = pd.DataFrame(combined_data)
    
    # Calculate performance metrics
    total_capital = capital_per_stock * len(tickers)
    initial_value = combined_portfolio_df['Portfolio_Value'].iloc[0]
    final_value = combined_portfolio_df['Portfolio_Value'].iloc[-1]
    total_return_pct = ((final_value - total_capital) / total_capital) * 100
    
    # Calculate max drawdown
    combined_portfolio_df['Peak'] = combined_portfolio_df['Portfolio_Value'].cummax()
    combined_portfolio_df['Drawdown'] = (combined_portfolio_df['Portfolio_Value'] - combined_portfolio_df['Peak']) / combined_portfolio_df['Peak'] * 100
    max_drawdown_pct = combined_portfolio_df['Drawdown'].min()
    
    # Calculate standard deviation of daily returns
    combined_portfolio_df['Daily_Return'] = combined_portfolio_df['Portfolio_Value'].pct_change() * 100
    std_dev = combined_portfolio_df['Daily_Return'].std()
    
    # Calculate annualized return
    days = (combined_portfolio_df['Date'].iloc[-1] - combined_portfolio_df['Date'].iloc[0]).days
    years = days / 365.25
    annualized_return = ((final_value / total_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
    
    # Calculate Sharpe ratio (assuming 0% risk-free rate)
    returns = combined_portfolio_df['Daily_Return'].dropna()
    sharpe_ratio = (returns.mean() / returns.std() * (252 ** 0.5)) if returns.std() > 0 else 0
    
    summary = {
        'tickers': ', '.join(tickers),
        'num_stocks': len(tickers),
        'start_date': combined_portfolio_df['Date'].iloc[0].strftime('%Y-%m-%d'),
        'end_date': combined_portfolio_df['Date'].iloc[-1].strftime('%Y-%m-%d'),
        'capital_per_stock': capital_per_stock,
        'total_capital': total_capital,
        'initial_value': initial_value,
        'final_value': final_value,
        'total_return_pct': total_return_pct,
        'annualized_return_pct': annualized_return,
        'max_drawdown_pct': max_drawdown_pct,
        'std_dev': std_dev,
        'sharpe_ratio': sharpe_ratio,
        'trading_days': len(combined_portfolio_df)
    }
    
    return combined_portfolio_df, individual_portfolios, summary


def main():
    parser = argparse.ArgumentParser(description='Multi-Stock Buy and Hold Benchmark')
    parser.add_argument('--tickers', type=str, nargs='+', required=True,
                        help='Stock tickers (e.g., 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK)')
    parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--capital-per-stock', type=float, default=20000, 
                        help='Initial capital per stock (default: 20000)')
    parser.add_argument('--output', type=str, default='trading_results', 
                        help='Output directory')
    
    args = parser.parse_args()
    
    total_capital = args.capital_per_stock * len(args.tickers)
    
    print("="*80)
    print(f"Multi-Stock Buy and Hold Benchmark")
    print(f"Stocks: {', '.join(args.tickers)}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Capital per stock: ${args.capital_per_stock:,.2f}")
    print(f"Total capital: ${total_capital:,.2f}")
    print("="*80)
    
    # Calculate benchmark
    combined_df, individual_portfolios, summary = calculate_multi_stock_benchmark(
        tickers=args.tickers,
        start_date=args.start,
        end_date=args.end,
        capital_per_stock=args.capital_per_stock
    )
    
    # Print summary
    print(f"\n{'='*80}")
    print("Multi-Stock Benchmark Results")
    print(f"{'='*80}")
    print(f"Stocks:               {summary['num_stocks']} ({summary['tickers']})")
    print(f"Trading Period:       {summary['start_date']} to {summary['end_date']}")
    print(f"Total Capital:        ${summary['total_capital']:,.2f}")
    print(f"Final Value:          ${summary['final_value']:,.2f}")
    print(f"Total Return:         {summary['total_return_pct']:.2f}%")
    print(f"Annualized Return:    {summary['annualized_return_pct']:.2f}%")
    print(f"Max Drawdown:         {summary['max_drawdown_pct']:.2f}%")
    print(f"Std Dev (daily):      {summary['std_dev']:.2f}%")
    print(f"Sharpe Ratio:         {summary['sharpe_ratio']:.2f}")
    print(f"Trading Days:         {summary['trading_days']}")
    
    # Print individual stock performance
    print(f"\n{'='*80}")
    print("Individual Stock Performance")
    print(f"{'='*80}")
    print(f"{'Ticker':<12} {'Shares':<12} {'Entry Price':<15} {'Exit Price':<15} {'Return %':<12}")
    print("-" * 80)
    
    for ticker, portfolio in individual_portfolios.items():
        stock_return = ((portfolio['final_value'] - portfolio['initial_value']) / portfolio['initial_value']) * 100
        print(f"{ticker:<12} {portfolio['shares']:<12.2f} ${portfolio['first_price']:<14.2f} "
              f"${portfolio['last_price']:<14.2f} {stock_return:>10.2f}%")
    
    # Save results
    benchmark_name = "multi_stock_benchmark"
    benchmark_dir = os.path.join(args.output, benchmark_name)
    os.makedirs(benchmark_dir, exist_ok=True)
    
    # Save combined portfolio history
    combined_df.to_csv(os.path.join(benchmark_dir, 'portfolio_history.csv'), index=False)
    
    # Save summary
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(os.path.join(benchmark_dir, 'summary.csv'), index=False)
    
    # Save individual stock details
    individual_details = []
    for ticker, portfolio in individual_portfolios.items():
        stock_return = ((portfolio['final_value'] - portfolio['initial_value']) / portfolio['initial_value']) * 100
        individual_details.append({
            'Ticker': ticker,
            'Shares': portfolio['shares'],
            'Entry_Price': portfolio['first_price'],
            'Exit_Price': portfolio['last_price'],
            'Initial_Value': portfolio['initial_value'],
            'Final_Value': portfolio['final_value'],
            'Return_%': stock_return
        })
    
    individual_df = pd.DataFrame(individual_details)
    individual_df.to_csv(os.path.join(benchmark_dir, 'individual_stocks.csv'), index=False)
    
    print(f"\n{'='*80}")
    print(f"Results saved to: {benchmark_dir}/")
    print(f"  - portfolio_history.csv: Daily combined portfolio values")
    print(f"  - summary.csv: Overall performance summary")
    print(f"  - individual_stocks.csv: Individual stock performance")
    print("="*80)


if __name__ == '__main__':
    main()
