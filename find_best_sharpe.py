"""
Find portfolios with the best Sharpe ratio
Analyzes trading results and calculates Sharpe ratio for each strategy
"""

import argparse
import pandas as pd
import numpy as np
import os


def calculate_sharpe_ratio(return_pct, std_dev_pct, risk_free_rate=0.02):
    """
    Calculate annualized Sharpe ratio
    
    Args:
        return_pct: Total return percentage
        std_dev_pct: Daily standard deviation percentage
        risk_free_rate: Annual risk-free rate (default 2%)
    
    Returns:
        Sharpe ratio
    """
    if std_dev_pct == 0:
        return 0
    
    # Convert daily std dev to annualized (assuming 252 trading days)
    annualized_std = std_dev_pct * np.sqrt(252)
    
    # Annualize the return (approximate based on typical 3-year period)
    # If you have the exact number of days, adjust accordingly
    annualized_return = return_pct
    
    # Calculate Sharpe ratio
    sharpe = (annualized_return - (risk_free_rate * 100)) / annualized_std
    
    return sharpe


def analyze_strategies(csv_path, risk_free_rate=0.02, top_n=5):
    """
    Analyze strategies and rank by Sharpe ratio
    
    Args:
        csv_path: Path to strategy comparison CSV
        risk_free_rate: Annual risk-free rate (default 2%)
        top_n: Number of top strategies to display
    """
    # Read the CSV
    df = pd.read_csv(csv_path)
    
    # Calculate Sharpe ratio for each strategy
    df['Sharpe_Ratio'] = df.apply(
        lambda row: calculate_sharpe_ratio(
            row['Total_Return_%'],
            row['Std_Dev_%'],
            risk_free_rate
        ),
        axis=1
    )
    
    # Sort by Sharpe ratio (descending)
    df_sorted = df.sort_values('Sharpe_Ratio', ascending=False)
    
    # Display results
    print("="*100)
    print("SHARPE RATIO ANALYSIS")
    print(f"Risk-free rate: {risk_free_rate*100:.1f}%")
    print("="*100)
    
    # Show all strategies ranked by Sharpe ratio
    print("\nAll Strategies Ranked by Sharpe Ratio:")
    print("-"*100)
    
    for idx, row in df_sorted.iterrows():
        print(f"\n{row['Strategy']}")
        print(f"  Final Value:      ${row['Final_Value']:,.2f}")
        print(f"  Total Return:     {row['Total_Return_%']:.2f}%")
        print(f"  Std Dev (daily):  {row['Std_Dev_%']:.2f}%")
        print(f"  Volatility:       {row['Volatility_%']:.2f}%")
        print(f"  Max Drawdown:     {row['Max_Drawdown_%']:.2f}%")
        print(f"  → SHARPE RATIO:   {row['Sharpe_Ratio']:.4f}")
    
    # Highlight top performers
    print("\n" + "="*100)
    print(f"TOP {top_n} STRATEGIES BY SHARPE RATIO")
    print("="*100)
    
    top_strategies = df_sorted.head(top_n)
    
    for rank, (idx, row) in enumerate(top_strategies.iterrows(), 1):
        print(f"\n#{rank}: {row['Strategy']}")
        print(f"     Sharpe Ratio:     {row['Sharpe_Ratio']:.4f}")
        print(f"     Total Return:     {row['Total_Return_%']:.2f}%")
        print(f"     Final Value:      ${row['Final_Value']:,.2f}")
        print(f"     Max Drawdown:     {row['Max_Drawdown_%']:.2f}%")
        print(f"     Volatility:       {row['Volatility_%']:.2f}%")
    
    # Additional statistics
    print("\n" + "="*100)
    print("SUMMARY STATISTICS")
    print("="*100)
    print(f"Average Sharpe Ratio:        {df['Sharpe_Ratio'].mean():.4f}")
    print(f"Median Sharpe Ratio:         {df['Sharpe_Ratio'].median():.4f}")
    print(f"Best Sharpe Ratio:           {df['Sharpe_Ratio'].max():.4f}")
    print(f"Worst Sharpe Ratio:          {df['Sharpe_Ratio'].min():.4f}")
    print(f"Std Dev of Sharpe Ratios:    {df['Sharpe_Ratio'].std():.4f}")
    
    # Save results with Sharpe ratios
    output_path = csv_path.replace('.csv', '_with_sharpe.csv')
    df_sorted.to_csv(output_path, index=False)
    print(f"\nResults saved to: {output_path}")
    
    # Save Excel file with Strategy and Sharpe Ratio only
    excel_path = csv_path.replace('.csv', '_sharpe_ranking.xlsx')
    df_excel = df_sorted[['Strategy', 'Sharpe_Ratio']].copy()
    df_excel.to_excel(excel_path, index=False, sheet_name='Sharpe Ratio')
    print(f"Excel file saved to: {excel_path}")
    
    return df_sorted


def compare_conservative_vs_aggressive(df):
    """Compare Conservative vs Aggressive strategies"""
    print("\n" + "="*100)
    print("CONSERVATIVE vs AGGRESSIVE COMPARISON")
    print("="*100)
    
    # Extract strategy type
    df['Type'] = df['Strategy'].str.extract(r'\((Conservative|Aggressive)\)')[0]
    
    conservative = df[df['Type'] == 'Conservative']
    aggressive = df[df['Type'] == 'Aggressive']
    
    if len(conservative) > 0:
        print("\nConservative Strategies:")
        print(f"  Average Sharpe Ratio:    {conservative['Sharpe_Ratio'].mean():.4f}")
        print(f"  Average Return:          {conservative['Total_Return_%'].mean():.2f}%")
        print(f"  Average Max Drawdown:    {conservative['Max_Drawdown_%'].mean():.2f}%")
        print(f"  Average Volatility:      {conservative['Volatility_%'].mean():.2f}%")
    
    if len(aggressive) > 0:
        print("\nAggressive Strategies:")
        print(f"  Average Sharpe Ratio:    {aggressive['Sharpe_Ratio'].mean():.4f}")
        print(f"  Average Return:          {aggressive['Total_Return_%'].mean():.2f}%")
        print(f"  Average Max Drawdown:    {aggressive['Max_Drawdown_%'].mean():.2f}%")
        print(f"  Average Volatility:      {aggressive['Volatility_%'].mean():.2f}%")


def main():
    parser = argparse.ArgumentParser(description='Find portfolios with best Sharpe ratio')
    parser.add_argument('--input', type=str, 
                        default='trading_results/strategy_comparison_stats.csv',
                        help='Path to strategy comparison CSV')
    parser.add_argument('--risk_free_rate', type=float, default=0.02,
                        help='Annual risk-free rate (default: 0.02 = 2%%)')
    parser.add_argument('--top_n', type=int, default=5,
                        help='Number of top strategies to highlight (default: 5)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        return
    
    # Analyze strategies
    df_sorted = analyze_strategies(args.input, args.risk_free_rate, args.top_n)
    
    # Compare strategy types
    compare_conservative_vs_aggressive(df_sorted)
    
    print("\n" + "="*100)


if __name__ == '__main__':
    main()
