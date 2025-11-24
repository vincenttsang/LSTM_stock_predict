# Benchmark Strategy 使用說明

## 概述
`benchmark.py` 腳本用於生成買入並持有（Buy and Hold）基準策略的表現，默認使用 2800.HK（盈富基金 - 恆生指數ETF）作為市場基準。

**重要更新：** 為了與主動交易策略進行公平對比，基準策略現在使用 **50% 倉位限制**（與 Conservative 策略相同），其餘 50% 資金以現金形式持有。

## 功能特點
- ✅ 計算買入並持有策略的完整表現
- ✅ 使用 50% 倉位限制，確保與主動策略公平對比
- ✅ 生成每日投資組合價值歷史（包含現金和持倉分離追蹤）
- ✅ 計算總回報率、年化回報率、最大回撤
- ✅ 與主動交易策略進行對比
- ✅ 可自定義基準股票代碼和初始資金

## 基本用法

### 1. 僅生成基準策略結果
```bash
conda run -n trading python benchmark.py \
  --ticker 2800.HK \
  --start 2022-10-27 \
  --end 2025-10-27 \
  --capital 20000
```

### 2. 生成基準並與交易策略對比
```bash
conda run -n trading python benchmark.py \
  --ticker 2800.HK \
  --start 2022-10-27 \
  --end 2025-10-27 \
  --capital 20000 \
  --compare 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK
```

## 參數說明

### 必需參數
- `--start`: 開始日期（格式：YYYY-MM-DD）
- `--end`: 結束日期（格式：YYYY-MM-DD）

### 可選參數
- `--ticker`: 基準股票代碼（默認：2800.HK）
- `--capital`: 初始資金（默認：100000）
- `--output`: 輸出目錄（默認：trading_results）
- `--compare`: 要對比的股票代碼列表（可選多個）

## 輸出文件

### 基準策略結果
```
trading_results/
└── 2800.HK_benchmark/
    ├── portfolio_history.csv    # 每日投資組合價值
    └── summary.csv               # 績效摘要
```

### 對比報告（當使用 --compare 時）
```
trading_results/
└── benchmark_comparison_2800.HK.csv  # 所有策略對比
```

## 輸出指標說明

### portfolio_history.csv
- `Date`: 交易日期
- `Price`: 股票價格
- `Shares`: 持有股數
- `Cash`: 剩餘現金（50% 資金）
- `Position_Value`: 持倉市值（50% 投資）
- `Portfolio_Value`: 投資組合總值（現金 + 持倉）

### summary.csv
- `ticker`: 股票代碼
- `start_date`: 開始日期
- `end_date`: 結束日期
- `initial_capital`: 初始資金
- `position_size_pct`: 倉位比例（固定 3%）
- `investment_amount`: 投資金額（初始資金 × 3%）
- `remaining_cash`: 剩餘現金（初始資金 × 97%）
- `initial_price`: 初始價格
- `final_price`: 最終價格
- `shares`: 購買股數
- `final_value`: 最終價值
- `total_return_pct`: 總回報率 (%)
- `annualized_return_pct`: 年化回報率 (%)
- `max_drawdown_pct`: 最大回撤 (%)
- `trading_days`: 交易日數

### benchmark_comparison.csv
包含基準策略和所有主動策略的對比：
- `Strategy`: 策略名稱
- `Ticker`: 股票代碼
- `Initial_Capital`: 初始資金
- `Final_Value`: 最終價值
- `Return_pct`: 總回報率
- `Annualized_Return_pct`: 年化回報率
- `Max_Drawdown_pct`: 最大回撤
- `Total_Trades`: 交易次數

## 使用場景

### 場景 1: 單純評估市場基準表現
```bash
# 查看恆生指數過去3年的表現
python benchmark.py --start 2022-10-27 --end 2025-10-27 --capital 20000
```

### 場景 2: 與單一股票的策略對比
```bash
# 對比 0005.HK 的主動策略 vs 市場基準
python benchmark.py --start 2022-10-27 --end 2025-10-27 --capital 20000 --compare 0005.HK
```

### 場景 3: 多股票策略全面對比
```bash
# 對比所有股票的主動策略與市場基準
python benchmark.py \
  --start 2022-10-27 \
  --end 2025-10-27 \
  --capital 20000 \
  --compare 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK
```

### 場景 4: 使用其他基準
```bash
# 使用 0388.HK（港交所）作為基準
python benchmark.py --ticker 0388.HK --start 2022-10-27 --end 2025-10-27 --capital 20000
```

## 完整工作流程示例

```bash
# 1. 先運行主動交易策略（Conservative + Aggressive）
conda run -n trading python trading.py --ticker 0005.HK --start 2022-10-27 --end 2025-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 0002.HK --start 2022-10-27 --end 2025-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 3690.HK --start 2022-10-27 --end 2025-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 0288.HK --start 2022-10-27 --end 2025-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 2318.HK --start 2022-10-27 --end 2025-10-27 --strategy both --capital 20000

# 2. 生成基準並與所有策略對比
conda run -n trading python benchmark.py \
  --ticker 2800.HK \
  --start 2022-10-27 \
  --end 2025-10-27 \
  --capital 20000 \
  --compare 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK

# 3. 查看對比結果
cat trading_results/benchmark_comparison_2800.HK.csv

conda activate trading
python compare_portfolio_aggregated.py --tickers 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK --capital-per-stock 20000
python compare_strategies.py \
  --benchmark 2800.HK \
  --tickers 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK \
  --capital 20000 \
  --output trading_results
```

## 結果解讀

### 示例結果分析
```
Strategy                            Return       Ann. Return  Max DD       Std Dev      Trades    
Benchmark (2800.HK)                      32.76%        9.94%      -19.74%        0.90%         1
0288.HK (Aggressive)                     26.76%        8.25%      -11.54%        0.92%        28
2318.HK (Conservative)                    8.75%        2.85%      -22.29%        0.80%         5
0005.HK (Conservative)                    6.21%        2.04%       -4.08%        0.21%         1
```

