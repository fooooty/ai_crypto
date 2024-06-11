import pandas as pd

# 데이터 불러오기
data = pd.read_csv("/Users/sonjiyeon/Desktop/ai-crypto-project-3-live-btc-krw.csv")

# 매수 및 매도 데이터 필터링
buy_data = data[data['side'] == 0]
sell_data = data[data['side'] == 1]

# 매수 및 매도 총액 계산
total_buy = (buy_data['price'] * buy_data['quantity']).sum()
total_sell = (sell_data['price'] * sell_data['quantity']).sum()

# PnL 계산
PnL = total_sell - total_buy - data['fee'].sum()

# 남은 BTC 계산
Remaining_Btc = buy_data['quantity'].sum() - sell_data['quantity'].sum()

print(f"PnL: {PnL}\nRemaining BTC: {Remaining_Btc}")
