# =========INFERENCE============
import numpy as np
import torch
from datetime import datetime, timedelta
from utils import fetch_and_add_indicators
from model import LSTMModel



device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'

ticker = '0005.HK'
target_col = 'SMA50_diff'
test_start   = '2022-10-27'
test_end     = '2022-10-28'

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
    start_pos = df_full.index.get_loc(test_start) - seq_len
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

print('Result:')
print(df_test)

