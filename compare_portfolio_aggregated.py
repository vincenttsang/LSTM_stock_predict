"""
Compare Aggregated Portfolios: Benchmark vs Combined Conservative vs Combined Aggressive
Each portfolio has 100,000 initial capital (5 stocks × 20,000 each)
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime


def load_strategy_data(output_dir, ticker, strategy_type):
    """Load portfolio history for a specific strategy"""
    strategy_dir = os.path.join(output_dir, f"{ticker}_{strategy_type}")
    history_file = os.path.join(strategy_dir, 'portfolio_history.csv')
    
    if not os.path.exists(history_file):
        return None
    
    df = pd.read_csv(history_file)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    return df[['Date', 'Portfolio_Value']]


def load_benchmark_data(output_dir, benchmark_ticker):
    """Load benchmark portfolio history"""
    benchmark_dir = os.path.join(output_dir, f"{benchmark_ticker}_benchmark")
    history_file = os.path.join(benchmark_dir, 'portfolio_history.csv')
    
    if not os.path.exists(history_file):
        return None
    
    df = pd.read_csv(history_file)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    return df[['Date', 'Portfolio_Value']]


def aggregate_strategies(all_strategy_data, strategy_type):
    """Aggregate multiple strategies by date"""
    if not all_strategy_data:
        return None
    
    # Merge all dataframes on Date
    merged = all_strategy_data[0].copy()
    merged = merged.rename(columns={'Portfolio_Value': 'Value_1'})
    
    for i, df in enumerate(all_strategy_data[1:], start=2):
        df_renamed = df.rename(columns={'Portfolio_Value': f'Value_{i}'})
        merged = merged.merge(df_renamed, on='Date', how='outer')
    
    # Sum all portfolio values
    value_cols = [col for col in merged.columns if col.startswith('Value_')]
    merged['Total_Portfolio_Value'] = merged[value_cols].sum(axis=1)
    
    return merged[['Date', 'Total_Portfolio_Value']].sort_values('Date').reset_index(drop=True)


def plot_aggregated_comparison(benchmark_df, conservative_df, aggressive_df, 
                               total_capital, output_path):
    """Create comparison line chart for aggregated portfolios"""
    plt.figure(figsize=(16, 10))
    
    # Plot benchmark (black, thickest)
    if benchmark_df is not None:
        plt.plot(benchmark_df['Date'], benchmark_df['Total_Portfolio_Value'], 
                label='Benchmark (2800.HK)', 
                color='#000000', linewidth=3.5, alpha=0.9, zorder=10)
    
    # Plot conservative portfolio (blue, medium)
    if conservative_df is not None:
        plt.plot(conservative_df['Date'], conservative_df['Total_Portfolio_Value'], 
                label='Conservative Portfolio (5 stocks combined)', 
                color='#1f77b4', linewidth=2.5, alpha=0.8, zorder=8)
    
    # Plot aggressive portfolio (red, medium)
    if aggressive_df is not None:
        plt.plot(aggressive_df['Date'], aggressive_df['Total_Portfolio_Value'], 
                label='Aggressive Portfolio (5 stocks combined)', 
                color='#d62728', linewidth=2.5, alpha=0.8, zorder=8, linestyle='--')
    
    # Add horizontal line at initial capital
    plt.axhline(y=total_capital, color='gray', linestyle=':', linewidth=1.5, 
               alpha=0.6, label=f'Initial Capital (${total_capital:,.0f})')
    
    # Formatting
    plt.title('Aggregated Portfolio Comparison: Benchmark vs Conservative vs Aggressive\n(Each portfolio: 5 stocks × $20,000 = $100,000)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Date', fontsize=13)
    plt.ylabel('Total Portfolio Value ($)', fontsize=13)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # Format y-axis with thousands separator
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    
    # Legend
    plt.legend(loc='best', frameon=True, shadow=True, fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nAggregated comparison chart saved to: {output_path}")
    plt.close()


def calculate_portfolio_stats(df, initial_capital, portfolio_name):
    """Calculate statistics for a portfolio"""
    if df is None or df.empty:
        return None
    
    initial_value = df['Total_Portfolio_Value'].iloc[0]
    final_value = df['Total_Portfolio_Value'].iloc[-1]
    max_value = df['Total_Portfolio_Value'].max()
    min_value = df['Total_Portfolio_Value'].min()
    
    total_return = ((final_value - initial_capital) / initial_capital) * 100
    max_gain = ((max_value - initial_capital) / initial_capital) * 100
    max_loss = ((min_value - initial_capital) / initial_capital) * 100
    
    # Calculate drawdown
    peak = df['Total_Portfolio_Value'].cummax()
    drawdown = ((df['Total_Portfolio_Value'] - peak) / peak * 100).min()
    
    # Calculate daily standard deviation
    returns = df['Total_Portfolio_Value'].pct_change().dropna()
    std_dev = (returns * 100).std()  # Daily std dev as percentage
    
    # Calculate volatility (annualized)
    volatility = returns.std() * (252 ** 0.5) * 100
    
    # Calculate Sharpe ratio (assuming 0% risk-free rate)
    sharpe = (returns.mean() / returns.std() * (252 ** 0.5)) if returns.std() > 0 else 0
    
    # Calculate annualized return
    days = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days
    years = days / 365.25
    annualized_return = ((final_value / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
    
    return {
        'Portfolio': portfolio_name,
        'Initial_Value': initial_capital,
        'Final_Value': final_value,
        'Total_Return_%': total_return,
        'Annualized_Return_%': annualized_return,
        'Max_Gain_%': max_gain,
        'Max_Loss_%': max_loss,
        'Max_Drawdown_%': drawdown,
        'Std_Dev_%': std_dev,
        'Volatility_%': volatility,
        'Sharpe_Ratio': sharpe,
        'Trading_Days': len(df)
    }


def main():
    parser = argparse.ArgumentParser(description='Compare Aggregated Portfolios')
    parser.add_argument('--benchmark', type=str, default='2800.HK', 
                        help='Benchmark ticker (default: 2800.HK)')
    parser.add_argument('--tickers', type=str, nargs='+', required=True,
                        help='Tickers to aggregate (e.g., 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK)')
    parser.add_argument('--output', type=str, default='trading_results', 
                        help='Output directory')
    parser.add_argument('--capital-per-stock', type=float, default=20000, 
                        help='Initial capital per stock (default: 20000)')
    
    args = parser.parse_args()
    
    total_capital = args.capital_per_stock * len(args.tickers)
    
    print("="*80)
    print("Aggregated Portfolio Comparison")
    print("="*80)
    print(f"Number of stocks: {len(args.tickers)}")
    print(f"Capital per stock: ${args.capital_per_stock:,.2f}")
    print(f"Total capital: ${total_capital:,.2f}")
    print("="*80)
    
    # Load and scale benchmark data to match total capital
    print(f"\nLoading benchmark data: {args.benchmark}")
    benchmark_original = load_benchmark_data(args.output, args.benchmark)
    
    if benchmark_original is not None:
        # Scale benchmark from 20,000 to 100,000 (5x)
        scale_factor = total_capital / args.capital_per_stock
        benchmark_df = benchmark_original.copy()
        benchmark_df['Total_Portfolio_Value'] = benchmark_df['Portfolio_Value'] * scale_factor
        benchmark_df = benchmark_df[['Date', 'Total_Portfolio_Value']]
        print(f"✓ Benchmark loaded and scaled: {len(benchmark_df)} days")
        print(f"  Initial: ${benchmark_df['Total_Portfolio_Value'].iloc[0]:,.2f}")
        print(f"  Final: ${benchmark_df['Total_Portfolio_Value'].iloc[-1]:,.2f}")
    else:
        print(f"✗ Benchmark not found")
        benchmark_df = None
    
    # Load conservative strategies
    print(f"\nLoading Conservative strategies:")
    conservative_data = []
    for ticker in args.tickers:
        df = load_strategy_data(args.output, ticker, 'conservative')
        if df is not None:
            conservative_data.append(df)
            print(f"✓ {ticker}: ${df['Portfolio_Value'].iloc[0]:,.2f} → ${df['Portfolio_Value'].iloc[-1]:,.2f}")
        else:
            print(f"✗ {ticker} not found")
    
    # Aggregate conservative
    if conservative_data:
        conservative_df = aggregate_strategies(conservative_data, 'conservative')
        print(f"\n✓ Conservative Portfolio Aggregated:")
        print(f"  Initial: ${conservative_df['Total_Portfolio_Value'].iloc[0]:,.2f}")
        print(f"  Final: ${conservative_df['Total_Portfolio_Value'].iloc[-1]:,.2f}")
    else:
        conservative_df = None
        print(f"\n✗ No conservative strategies found")
    
    # Load aggressive strategies
    print(f"\nLoading Aggressive strategies:")
    aggressive_data = []
    for ticker in args.tickers:
        df = load_strategy_data(args.output, ticker, 'aggressive')
        if df is not None:
            aggressive_data.append(df)
            print(f"✓ {ticker}: ${df['Portfolio_Value'].iloc[0]:,.2f} → ${df['Portfolio_Value'].iloc[-1]:,.2f}")
        else:
            print(f"✗ {ticker} not found")
    
    # Aggregate aggressive
    if aggressive_data:
        aggressive_df = aggregate_strategies(aggressive_data, 'aggressive')
        print(f"\n✓ Aggressive Portfolio Aggregated:")
        print(f"  Initial: ${aggressive_df['Total_Portfolio_Value'].iloc[0]:,.2f}")
        print(f"  Final: ${aggressive_df['Total_Portfolio_Value'].iloc[-1]:,.2f}")
    else:
        aggressive_df = None
        print(f"\n✗ No aggressive strategies found")
    
    # Generate plot
    output_path = os.path.join(args.output, 'aggregated_portfolio_comparison.png')
    plot_aggregated_comparison(benchmark_df, conservative_df, aggressive_df, 
                               total_capital, output_path)
    
    # Generate statistics
    print("\n" + "="*80)
    print("Performance Statistics")
    print("="*80)
    
    stats_list = []
    
    if benchmark_df is not None:
        stats = calculate_portfolio_stats(benchmark_df, total_capital, 'Benchmark (2800.HK)')
        if stats:
            stats_list.append(stats)
    
    if conservative_df is not None:
        stats = calculate_portfolio_stats(conservative_df, total_capital, 'Conservative Portfolio')
        if stats:
            stats_list.append(stats)
    
    if aggressive_df is not None:
        stats = calculate_portfolio_stats(aggressive_df, total_capital, 'Aggressive Portfolio')
        if stats:
            stats_list.append(stats)
    
    if stats_list:
        stats_df = pd.DataFrame(stats_list)
        stats_df = stats_df.sort_values('Total_Return_%', ascending=False)
        
        # Print table
        print(f"\n{'Portfolio':<30} {'Initial':<15} {'Final':<15} {'Return %':<12} {'Ann. Ret %':<12} {'Max DD %':<12} {'Std Dev %':<12} {'Sharpe':<10}")
        print("-" * 125)
        for _, row in stats_df.iterrows():
            print(f"{row['Portfolio']:<30} ${row['Initial_Value']:>13,.0f} ${row['Final_Value']:>13,.0f} "
                  f"{row['Total_Return_%']:>10.2f}% {row['Annualized_Return_%']:>10.2f}% "
                  f"{row['Max_Drawdown_%']:>10.2f}% {row['Std_Dev_%']:>10.2f}% {row['Sharpe_Ratio']:>8.2f}")
        
        # Save statistics to CSV
        stats_path = os.path.join(args.output, 'aggregated_portfolio_stats.csv')
        stats_df.to_csv(stats_path, index=False)
        print(f"\nStatistics saved to: {stats_path}")
        
        # Print detailed comparison
        print("\n" + "="*80)
        print("Detailed Analysis")
        print("="*80)
        
        for _, row in stats_df.iterrows():
            print(f"\n{row['Portfolio']}:")
            print(f"  Total Return:      {row['Total_Return_%']:>8.2f}%")
            print(f"  Annualized Return: {row['Annualized_Return_%']:>8.2f}%")
            print(f"  Max Gain:          {row['Max_Gain_%']:>8.2f}%")
            print(f"  Max Loss:          {row['Max_Loss_%']:>8.2f}%")
            print(f"  Max Drawdown:      {row['Max_Drawdown_%']:>8.2f}%")
            print(f"  Std Dev (daily):   {row['Std_Dev_%']:>8.2f}%")
            print(f"  Volatility:        {row['Volatility_%']:>8.2f}%")
            print(f"  Sharpe Ratio:      {row['Sharpe_Ratio']:>8.2f}")
            print(f"  Final Value:       ${row['Final_Value']:>,.2f}")
    
    print("\n" + "="*80)
    print("✅ Aggregated comparison complete!")
    print("="*80)


if __name__ == '__main__':
    main()
