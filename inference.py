# =========INFERENCE============
import numpy as np
import torch
import argparse
import os
from datetime import datetime, timedelta
from utils import fetch_and_add_indicators
from model import LSTMModel


def parse_args():
    parser = argparse.ArgumentParser(description='LSTM Stock Prediction Inference')
    parser.add_argument('--ticker', type=str, required=True, help='Stock ticker symbol (e.g., 0005.HK)')
    parser.add_argument('--target_col', type=str, default='SMA50_diff', help='Target column for prediction')
    parser.add_argument('--start', type=str, required=True, help='Test start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True, help='Test end date (YYYY-MM-DD)')
    parser.add_argument('--output', type=str, default=None, help='Output CSV file path (default: predictions/{ticker}_predict.csv)')
    return parser.parse_args()


args = parse_args()
device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'

ticker = args.ticker
target_col = args.target_col
test_start = args.start
test_end = args.end

seq_len     = 60
batch_size  = 64
features    = ['SMA50_diff','SMA20_diff','SMA10_diff','SMA100_diff']
target_col  = 'SMA50_diff'


buffer_start = (datetime.strptime(test_start, '%Y-%m-%d') - timedelta(days=300)).strftime('%Y-%m-%d')
df_full = fetch_and_add_indicators(ticker, features ,buffer_start, test_end)

df_test = df_full[test_start:test_end]

checkpoint = torch.load(f"models/{ticker}_lstm_{target_col}.pth", map_location=device,weights_only=False)

scaler = checkpoint['scaler']

model = LSTMModel()
model.load_state_dict(checkpoint['model_state_dict'])
model.to(device)
model.eval()
preds = []

print('Start Prediction...')
with torch.no_grad():
    # Use get_indexer with 'nearest' method to handle non-trading days (weekends/holidays)
    test_start_idx = df_full.index.get_indexer([test_start], method='nearest')[0]
    if test_start_idx == -1:
        # If still not found, use the first available date after test_start
        test_start_idx = df_full.index.searchsorted(test_start)
    
    start_pos = test_start_idx - seq_len
    for i in range(len(df_test)):
        window = scaler.transform(df_full)[start_pos + i : start_pos + i + seq_len]            
        inp = torch.tensor(window).unsqueeze(0).to(device)
        pred = model(inp).item()
        preds.append(pred)

# Inverse transform
dummy = np.zeros((len(preds), len(features)))
dummy[:, 0] = preds
preds_inv = scaler.inverse_transform(dummy)[:, 0]

df_test['next_day_SMA50_diff'] = preds_inv

# Determine output path
if args.output:
    output_path = args.output
else:
    os.makedirs('predictions', exist_ok=True)
    output_path = f'predictions/{ticker}_predict.csv'

# Save to CSV
df_test.to_csv(output_path)

print('Result:')
print(df_test)
print(f'\nPredictions saved to: {output_path}')

