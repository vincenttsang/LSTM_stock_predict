"""
Compare Benchmark and Active Trading Strategies
Generate line chart comparing daily portfolio values across all strategies
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
    df['Strategy'] = f"{ticker} ({strategy_type.capitalize()})"
    return df[['Date', 'Portfolio_Value', 'Strategy']]


def load_benchmark_data(output_dir, benchmark_ticker):
    """Load benchmark portfolio history"""
    benchmark_dir = os.path.join(output_dir, f"{benchmark_ticker}_benchmark")
    history_file = os.path.join(benchmark_dir, 'portfolio_history.csv')
    
    if not os.path.exists(history_file):
        return None
    
    df = pd.read_csv(history_file)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    df['Strategy'] = f"Benchmark ({benchmark_ticker})"
    return df[['Date', 'Portfolio_Value', 'Strategy']]


def plot_comparison(all_data, initial_capital, output_path):
    """Create comparison line chart"""
    plt.figure(figsize=(16, 10))
    
    # Define colors
    benchmark_color = '#000000'  # Black for benchmark
    conservative_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']  # Blue tones
    aggressive_colors = ['#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']     # Red tones
    
    benchmark_data = None
    conservative_data = []
    aggressive_data = []
    
    # Separate data by strategy type
    for strategy_name in all_data['Strategy'].unique():
        strategy_df = all_data[all_data['Strategy'] == strategy_name]
        
        if 'Benchmark' in strategy_name:
            benchmark_data = strategy_df
        elif 'Conservative' in strategy_name:
            conservative_data.append(strategy_df)
        elif 'Aggressive' in strategy_name:
            aggressive_data.append(strategy_df)
    
    # Plot benchmark first (thickest line)
    if benchmark_data is not None:
        plt.plot(benchmark_data['Date'], benchmark_data['Portfolio_Value'], 
                label=benchmark_data['Strategy'].iloc[0], 
                color=benchmark_color, linewidth=3, alpha=0.9, zorder=10)
    
    # Plot conservative strategies (medium lines)
    for idx, strategy_df in enumerate(conservative_data):
        color = conservative_colors[idx % len(conservative_colors)]
        plt.plot(strategy_df['Date'], strategy_df['Portfolio_Value'], 
                label=strategy_df['Strategy'].iloc[0], 
                color=color, linewidth=2, alpha=0.7, linestyle='-')
    
    # Plot aggressive strategies (thin lines)
    for idx, strategy_df in enumerate(aggressive_data):
        color = aggressive_colors[idx % len(aggressive_colors)]
        plt.plot(strategy_df['Date'], strategy_df['Portfolio_Value'], 
                label=strategy_df['Strategy'].iloc[0], 
                color=color, linewidth=1.5, alpha=0.6, linestyle='--')
    
    # Add horizontal line at initial capital
    plt.axhline(y=initial_capital, color='gray', linestyle=':', linewidth=1, alpha=0.5, label='Initial Capital')
    
    # Formatting
    plt.title('Portfolio Value Comparison: Benchmark vs Active Trading Strategies', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Portfolio Value ($)', fontsize=12)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # Format x-axis dates
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    
    # Legend - place outside plot area
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
              frameon=True, shadow=True, fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nComparison chart saved to: {output_path}")
    plt.close()


def generate_statistics_table(all_data, initial_capital):
    """Generate statistics table for all strategies"""
    stats = []
    
    for strategy_name in all_data['Strategy'].unique():
        strategy_df = all_data[all_data['Strategy'] == strategy_name]
        
        initial_value = strategy_df['Portfolio_Value'].iloc[0]
        final_value = strategy_df['Portfolio_Value'].iloc[-1]
        max_value = strategy_df['Portfolio_Value'].max()
        min_value = strategy_df['Portfolio_Value'].min()
        
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        max_gain = ((max_value - initial_capital) / initial_capital) * 100
        max_loss = ((min_value - initial_capital) / initial_capital) * 100
        
        # Calculate drawdown
        peak = strategy_df['Portfolio_Value'].cummax()
        drawdown = ((strategy_df['Portfolio_Value'] - peak) / peak * 100).min()
        
        # Calculate daily standard deviation
        returns = strategy_df['Portfolio_Value'].pct_change().dropna()
        std_dev = (returns * 100).std()  # Daily std dev as percentage
        
        # Calculate volatility
        volatility = returns.std() * (252 ** 0.5) * 100  # Annualized volatility
        
        stats.append({
            'Strategy': strategy_name,
            'Final_Value': final_value,
            'Total_Return_%': total_return,
            'Max_Gain_%': max_gain,
            'Max_Loss_%': max_loss,
            'Max_Drawdown_%': drawdown,
            'Std_Dev_%': std_dev,
            'Volatility_%': volatility
        })
    
    stats_df = pd.DataFrame(stats)
    stats_df = stats_df.sort_values('Total_Return_%', ascending=False)
    
    return stats_df


def main():
    parser = argparse.ArgumentParser(description='Compare Benchmark and Active Trading Strategies')
    parser.add_argument('--benchmark', type=str, default='2800.HK', 
                        help='Benchmark ticker (default: 2800.HK)')
    parser.add_argument('--tickers', type=str, nargs='+', required=True,
                        help='Tickers to compare (e.g., 0005.HK 0002.HK 3690.HK)')
    parser.add_argument('--output', type=str, default='trading_results', 
                        help='Output directory')
    parser.add_argument('--capital', type=float, default=100000, 
                        help='Initial capital')
    
    args = parser.parse_args()
    
    print("="*80)
    print("Strategy Comparison - Daily Portfolio Values")
    print("="*80)
    
    all_data = []
    
    # Load benchmark data
    print(f"\nLoading benchmark data: {args.benchmark}")
    benchmark_df = load_benchmark_data(args.output, args.benchmark)
    if benchmark_df is not None:
        all_data.append(benchmark_df)
        print(f"✓ Benchmark loaded: {len(benchmark_df)} days")
    else:
        print(f"✗ Benchmark not found")
    
    # Load trading strategies
    for ticker in args.tickers:
        for strategy in ['conservative', 'aggressive']:
            print(f"Loading {ticker} - {strategy}")
            strategy_df = load_strategy_data(args.output, ticker, strategy)
            if strategy_df is not None:
                all_data.append(strategy_df)
                print(f"✓ {ticker} {strategy} loaded: {len(strategy_df)} days")
            else:
                print(f"✗ {ticker} {strategy} not found")
    
    if not all_data:
        print("\n❌ No data found! Please run benchmark.py and trading.py first.")
        return
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Generate plot
    output_path = os.path.join(args.output, 'strategy_comparison_chart.png')
    plot_comparison(combined_df, args.capital, output_path)
    
    # Generate statistics table
    print("\n" + "="*80)
    print("Performance Statistics")
    print("="*80)
    
    stats_df = generate_statistics_table(combined_df, args.capital)
    
    # Print table
    print(f"\n{'Strategy':<35} {'Final Value':<15} {'Return %':<12} {'Max DD %':<12} {'Std Dev %':<12} {'Volatility %':<12}")
    print("-" * 105)
    for _, row in stats_df.iterrows():
        print(f"{row['Strategy']:<35} ${row['Final_Value']:>13,.2f} "
              f"{row['Total_Return_%']:>10.2f}% {row['Max_Drawdown_%']:>10.2f}% "
              f"{row['Std_Dev_%']:>10.2f}% {row['Volatility_%']:>10.2f}%")
    
    # Save statistics to CSV
    stats_path = os.path.join(args.output, 'strategy_comparison_stats.csv')
    stats_df.to_csv(stats_path, index=False)
    print(f"\nStatistics saved to: {stats_path}")
    
    print("\n" + "="*80)
    print("✅ Comparison complete!")
    print("="*80)


if __name__ == '__main__':
    main()
