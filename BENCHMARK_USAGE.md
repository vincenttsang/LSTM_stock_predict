# Benchmark Strategy 使用說明

## 概述
本項目提供兩種基準策略來評估主動交易策略的表現：

### 1. 市場基準 (`benchmark.py`)
使用 2800.HK（盈富基金 - 恆生指數ETF）作為市場基準。

**重要更新：** 為了與主動交易策略進行公平對比，基準策略現在使用 **50% 倉位限制**（與 Conservative 策略相同），其餘 50% 資金以現金形式持有。

### 2. 多股票買入持有基準 (`benchmark_multi_stock.py`) ⭐ 新增
買入並持有 5 支股票本身，每支股票分配相同資金（例如各 $20,000），在第一個交易日買入後持有整個期間。這提供了更公平的對比基準，因為使用與主動策略相同的股票池。

## 功能特點

### 市場基準 (benchmark.py)
- ✅ 計算買入並持有策略的完整表現
- ✅ 使用 50% 倉位限制，確保與主動策略公平對比
- ✅ 生成每日投資組合價值歷史（包含現金和持倉分離追蹤）
- ✅ 計算總回報率、年化回報率、最大回撤、標準差
- ✅ 與主動交易策略進行對比
- ✅ 可自定義基準股票代碼和初始資金

### 多股票基準 (benchmark_multi_stock.py)
- ✅ 同時買入並持有多支股票（默認 5 支）
- ✅ 每支股票平均分配資金
- ✅ 追蹤整體投資組合和個別股票表現
- ✅ 計算夏普比率、標準差等風險指標
- ✅ 提供個別股票表現明細
- ✅ 適合與主動策略的聚合投資組合對比

## 基本用法

### 方案 A: 市場基準 (benchmark.py)

#### 1. 僅生成基準策略結果
```bash
conda run -n trading python benchmark.py \
  --ticker 2800.HK \
  --start 2022-10-27 \
  --end 2025-10-27 \
  --capital 20000
```

#### 2. 生成基準並與交易策略對比
```bash
conda run -n trading python benchmark.py \
  --ticker 2800.HK \
  --start 2022-10-27 \
  --end 2025-10-27 \
  --capital 20000 \
  --compare 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK
```

### 方案 B: 多股票買入持有基準 (benchmark_multi_stock.py) ⭐ 推薦

#### 1. 生成 5 支股票的買入持有基準
```bash
conda run -n trading python benchmark_multi_stock.py \
  --tickers 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK \
  --start 2022-10-27 \
  --end 2024-10-27 \
  --capital-per-stock 20000
```

**說明：**
- 每支股票分配 $20,000
- 總資金：5 × $20,000 = $100,000
- 第一天買入所有股票並持有至結束

## 參數說明

### benchmark.py 參數

#### 必需參數
- `--start`: 開始日期（格式：YYYY-MM-DD）
- `--end`: 結束日期（格式：YYYY-MM-DD）

#### 可選參數
- `--ticker`: 基準股票代碼（默認：2800.HK）
- `--capital`: 初始資金（默認：100000）
- `--output`: 輸出目錄（默認：trading_results）
- `--compare`: 要對比的股票代碼列表（可選多個）

### benchmark_multi_stock.py 參數

#### 必需參數
- `--tickers`: 股票代碼列表（例如：0005.HK 0002.HK 3690.HK）
- `--start`: 開始日期（格式：YYYY-MM-DD）
- `--end`: 結束日期（格式：YYYY-MM-DD）

#### 可選參數
- `--capital-per-stock`: 每支股票的初始資金（默認：20000）
- `--output`: 輸出目錄（默認：trading_results）

## 輸出文件

### 市場基準結果 (benchmark.py)
```
trading_results/
└── 2800.HK_benchmark/
    ├── portfolio_history.csv    # 每日投資組合價值
    └── summary.csv               # 績效摘要
```

### 多股票基準結果 (benchmark_multi_stock.py)
```
trading_results/
└── multi_stock_benchmark/
    ├── portfolio_history.csv    # 每日整體投資組合價值
    ├── summary.csv               # 整體績效摘要
    └── individual_stocks.csv     # 個別股票表現明細
```

### 對比報告（當使用 --compare 時）
```
trading_results/
└── benchmark_comparison_2800.HK.csv  # 所有策略對比
```

## 輸出指標說明

### 市場基準 (benchmark.py)

#### portfolio_history.csv
- `Date`: 交易日期
- `Price`: 股票價格
- `Shares`: 持有股數
- `Cash`: 剩餘現金（50% 資金）
- `Position_Value`: 持倉市值（50% 投資）
- `Portfolio_Value`: 投資組合總值（現金 + 持倉）

#### summary.csv
- `ticker`: 股票代碼
- `start_date`: 開始日期
- `end_date`: 結束日期
- `initial_capital`: 初始資金
- `position_size_pct`: 倉位比例（固定 50%）
- `investment_amount`: 投資金額（初始資金 × 50%）
- `remaining_cash`: 剩餘現金（初始資金 × 50%）
- `initial_price`: 初始價格
- `final_price`: 最終價格
- `shares`: 購買股數
- `final_value`: 最終價值
- `total_return_pct`: 總回報率 (%)
- `annualized_return_pct`: 年化回報率 (%)
- `max_drawdown_pct`: 最大回撤 (%)
- `std_dev`: 每日回報標準差 (%)
- `trading_days`: 交易日數

### 多股票基準 (benchmark_multi_stock.py)

#### portfolio_history.csv
- `Date`: 交易日期
- `Portfolio_Value`: 所有股票持倉總市值
- `Peak`: 累計最高價值
- `Drawdown`: 當前回撤 (%)
- `Daily_Return`: 每日回報率 (%)

#### summary.csv
- `tickers`: 股票代碼列表
- `num_stocks`: 股票數量
- `start_date`: 開始日期
- `end_date`: 結束日期
- `capital_per_stock`: 每支股票資金
- `total_capital`: 總資金
- `initial_value`: 初始總值
- `final_value`: 最終總值
- `total_return_pct`: 總回報率 (%)
- `annualized_return_pct`: 年化回報率 (%)
- `max_drawdown_pct`: 最大回撤 (%)
- `std_dev`: 每日回報標準差 (%)
- `sharpe_ratio`: 夏普比率
- `trading_days`: 交易日數

#### individual_stocks.csv
- `Ticker`: 股票代碼
- `Shares`: 購買股數
- `Entry_Price`: 買入價格
- `Exit_Price`: 最終價格
- `Initial_Value`: 初始投資金額
- `Final_Value`: 最終價值
- `Return_%`: 個別股票回報率 (%)

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

### 工作流程 1: 使用市場基準 (2800.HK)

```bash
# 1. 先運行主動交易策略（Conservative + Aggressive）
conda run -n trading python trading.py --ticker 0005.HK --start 2022-10-27 --end 2024-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 0002.HK --start 2022-10-27 --end 2024-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 3690.HK --start 2022-10-27 --end 2024-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 0288.HK --start 2022-10-27 --end 2024-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 2318.HK --start 2022-10-27 --end 2024-10-27 --strategy both --capital 20000

# 2. 生成市場基準並與所有策略對比
conda run -n trading python benchmark.py \
  --ticker 2800.HK \
  --start 2022-10-27 \
  --end 2024-10-27 \
  --capital 20000 \
  --compare 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK

# 3. 生成策略對比圖表
conda activate trading
python compare_strategies.py \
  --benchmark 2800.HK \
  --tickers 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK \
  --capital 20000 \
  --output trading_results

# 4. 生成聚合投資組合對比
python compare_portfolio_aggregated.py \
  --benchmark 2800.HK \
  --tickers 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK \
  --capital-per-stock 20000
```

### 工作流程 2: 使用多股票基準 ⭐ 推薦

```bash
# 1. 先運行主動交易策略（同上）
conda run -n trading python trading.py --ticker 0005.HK --start 2022-10-27 --end 2024-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 0002.HK --start 2022-10-27 --end 2024-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 3690.HK --start 2022-10-27 --end 2024-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 0288.HK --start 2022-10-27 --end 2024-10-27 --strategy both --capital 20000
conda run -n trading python trading.py --ticker 2318.HK --start 2022-10-27 --end 2024-10-27 --strategy both --capital 20000

# 2. 生成多股票買入持有基準
conda run -n trading python benchmark_multi_stock.py \
  --tickers 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK \
  --start 2022-10-27 \
  --end 2024-10-27 \
  --capital-per-stock 20000

# 3. 生成對比圖表（包含多股票基準）
conda activate trading
python compare_portfolio_aggregated.py \
  --tickers 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK \
  --capital-per-stock 20000

# 輸出: trading_results/aggregated_portfolio_comparison.png
#       trading_results/aggregated_portfolio_stats.csv
```

**說明：** `compare_portfolio_aggregated.py` 現在可以自動載入 `multi_stock_benchmark` 的結果並繪製在對比圖表中。

## 圖表生成命令

### 生成包含多股票基準的對比圖表

```bash
conda activate trading

# 方案 1: 生成個別策略對比圖（含 2800.HK 基準）
python compare_strategies.py \
  --benchmark 2800.HK \
  --tickers 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK \
  --capital 20000

# 方案 2: 生成聚合投資組合對比圖（自動載入 multi_stock_benchmark）⭐ 推薦
python compare_portfolio_aggregated.py \
  --tickers 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK \
  --capital-per-stock 20000
```

**輸出文件：**
- `trading_results/aggregated_portfolio_comparison.png` - 包含以下三條曲線：
  - 🔴 Aggressive Portfolio (5 stocks combined)
  - 🔵 Conservative Portfolio (5 stocks combined)
  - ⚫ Multi-Stock Buy & Hold Benchmark (5 stocks combined)
  
- `trading_results/aggregated_portfolio_stats.csv` - 詳細統計對比

### 如何在圖表中顯示多股票基準

`compare_portfolio_aggregated.py` 腳本會自動檢測並載入 `trading_results/multi_stock_benchmark/` 目錄中的數據。只需確保：

1. 先運行 `benchmark_multi_stock.py` 生成基準數據
2. 再運行 `compare_portfolio_aggregated.py` 即可在圖表中看到基準線

## 結果解讀

### 示例結果分析（市場基準）
```
Strategy                            Return       Ann. Return  Max DD       Std Dev      Trades    
Benchmark (2800.HK)                      32.76%        9.94%      -19.74%        0.90%         1
0288.HK (Aggressive)                     26.76%        8.25%      -11.54%        0.92%        28
2318.HK (Conservative)                    8.75%        2.85%      -22.29%        0.80%         5
0005.HK (Conservative)                    6.21%        2.04%       -4.08%        0.21%         1
```

### 示例結果分析（聚合投資組合對比）
```
Portfolio                      Initial         Final           Return %    Ann. Ret %  Max DD %    Std Dev %   Sharpe
Multi-Stock Benchmark          $100,000        $128,450        28.45%      13.45%      -15.23%     1.12%       1.18
Aggressive Portfolio           $100,000        $124,320        24.32%      11.58%      -18.67%     1.34%       0.95
Conservative Portfolio         $100,000        $115,680        15.68%       7.52%      -12.45%     0.89%       0.82
```

**解讀要點：**
- **多股票基準** 使用與主動策略相同的 5 支股票，但採用簡單買入持有
- 如果主動策略回報高於多股票基準，表示交易策略成功增值
- 如果低於基準，建議直接買入持有即可，無需主動交易
- 標準差和夏普比率幫助評估風險調整後的回報

