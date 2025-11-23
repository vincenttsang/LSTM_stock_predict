# Benchmark Strategy 使用說明

## 概述
`benchmark.py` 腳本用於生成買入並持有（Buy and Hold）基準策略的表現，默認使用 2800.HK（盈富基金 - 恆生指數ETF）作為市場基準。

**重要更新：** 為了與主動交易策略進行公平對比，基準策略現在使用 **3% 倉位限制**（與 Aggressive 策略相同），其餘 97% 資金以現金形式持有。

## 功能特點
- ✅ 計算買入並持有策略的完整表現
- ✅ **使用 3% 倉位限制，確保與主動策略公平對比**
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
- `Cash`: 剩餘現金（97% 資金）
- `Position_Value`: 持倉市值（3% 投資）
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

conda run -n trading python compare_portfolio_aggregated.py --tickers 0005.HK 0002.HK 3690.HK 0288.HK 2318.HK --capital-per-stock 20000
```

## 結果解讀

### 示例結果分析
```
Strategy                            Return       Ann. Return  Max DD       Trades    
Benchmark (2800.HK)                  1.97%        0.65%       -1.41%         1
0005.HK (Aggressive)                 0.85%        0.28%       -0.54%       270
0288.HK (Aggressive)                 0.71%        0.24%       -0.68%       113
```

**關鍵觀察：**
1. **基準回報（1.97%）** - 使用 3% 倉位買入並持有2800.HK的3年回報
2. **年化回報（0.65%）** - 平均每年的回報率
3. **最大回撤（-1.41%）** - 投資期間的最大跌幅（因97%資金為現金，波動較小）
4. **主動策略對比** - 在相同 3% 倉位限制下，基準策略（1.97%）略優於主動策略（0.85%）
5. **公平對比** - 現在基準與 Aggressive 策略使用相同的倉位限制，對比更具參考價值

### Alpha 計算
主動策略的 Alpha（超額回報）= 主動策略回報 - 基準回報
- 0005.HK Aggressive Alpha = 0.85% - 1.97% = **-1.12%**（略遜於被動投資）

**注意：** 舊版本基準使用 100% 倉位，3年回報約 65.53%，但這與主動策略的 3% 倉位限制不具可比性。

### 何時主動策略有價值？
- ✅ 當主動策略回報 > 基準回報
- ✅ 當主動策略有較低的最大回撤
- ✅ 當主動策略的夏普比率更高

## 常見問題

### Q: 為什麼使用 2800.HK？
A: 2800.HK（盈富基金）追蹤恆生指數，是香港市場最具代表性的被動投資工具，適合作為港股投資的基準。

### Q: 可以使用其他基準嗎？
A: 可以，使用 `--ticker` 參數指定其他股票或ETF，例如：
   - 0388.HK（港交所）
   - 0700.HK（騰訊）
   - SPY（標普500 ETF - 需要美股數據）

### Q: 如何計算夏普比率？
A: 目前腳本未計算夏普比率，但可以手動計算：
   夏普比率 = (年化回報 - 無風險利率) / 年化波動率

### Q: 交易成本如何處理？
A: 基準策略假設買入並持有，只有一次買入交易，交易成本可忽略不計。主動策略的交易成本需要在 trading.py 中設定。

### Q: 為什麼使用 3% 倉位而不是全倉投資？
A: 為了與 Aggressive 策略進行公平對比。主動策略使用 3% 單筆倉位限制來控制風險，如果基準使用 100% 倉位，會因為槓桿差異而無法公平比較。使用相同的 3% 倉位限制，可以真實評估策略的選股和擇時能力。

### Q: 3% 倉位限制下，基準的預期回報如何？
A: 基準回報 ≈ 股票漲幅 × 3%。例如 2800.HK 三年上漲 65.53%，則 3% 倉位的回報約為 1.97%（65.53% × 3% ≈ 1.97%），其餘 97% 現金回報為 0。

## 技巧建議

1. **定期更新基準** - 建議每季度運行一次以追蹤最新表現
2. **多基準對比** - 考慮使用多個基準（如個股、行業ETF、大盤指數）
3. **風險調整回報** - 不僅看回報率，也要考慮波動性和回撤
4. **長期視角** - 至少使用3年以上數據評估策略效果
5. **理解倉位限制影響** - 3% 倉位限制確保公平對比，但也意味著基準回報會較全倉投資低很多
6. **現金管理** - 97% 現金持有意味著基準策略非常保守，主要測試的是「3% 被動投資 vs 3% 主動交易」的效果
