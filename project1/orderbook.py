import time
import requests
import pandas as pd
import datetime as dt
import os

while True:
    Today = dt.datetime.now()
    fn = "book-{0}-{1}-{2}-bithumb-eth.csv".format(Today.year, Today.month, Today.day)

    book = {}
    response = requests.get('https://api.bithumb.com/public/orderbook/ETH_KRW/?count=5')
    book = response.json()

    data = book['data']

    bids = (pd.DataFrame(data['bids'])).apply(pd.to_numeric, errors='ignore')
    bids.sort_values('price', ascending=False, inplace=True)
    bids = bids.reset_index();
    del bids['index']
    bids['type'] = 0

    asks = (pd.DataFrame(data['asks'])).apply(pd.to_numeric, errors='ignore')
    asks.sort_values('price', ascending=True, inplace=True)
    asks['type'] = 1

    df = pd.concat([bids, asks], ignore_index=True)

    timestamp = dt.datetime.now()
    req_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')

    df['quantity'] = df['quantity'].round(decimals=4)
    df['timestamp'] = req_timestamp

    should_write_header = os.path.exists(fn)
    if should_write_header == False:
        df.to_csv(fn, index=False, header=True, mode='a')
    else:
        df.to_csv(fn, index=False, header=False, mode='a')

    time.sleep(5)
