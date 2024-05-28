import pandas as pd
import math

mid_type = ''


# CSV 파일을 로드하고 'timestamp' 열로 그룹화하는 함수
def get_sim_df(fn):
    print('loading... %s' % fn)
    df = pd.read_csv(fn).apply(pd.to_numeric, errors='ignore')  # CSV 파일을 읽고 숫자형으로 변환
    group = df.groupby(['timestamp'])  # 'timestamp'로 그룹화

    return group


def get_diff_count_units(diff):
    _count_1 = _count_0 = _units_traded_1 = _units_traded_0 = 0
    _price_1 = _price_0 = 0

    diff_len = len(diff)
    if diff_len == 1:
        row = diff.iloc[0]
        if row['type'] == 1:
            _count_1 = row['count']
            _units_traded_1 = row['units_traded']
            _price_1 = row['price']
        else:
            _count_0 = row['count']
            _units_traded_0 = row['units_traded']
            _price_0 = row['price']

        return (_count_1, _count_0, _units_traded_1, _units_traded_0, _price_1, _price_0)

    elif diff_len == 2:
        row_1 = diff.iloc[1]
        row_0 = diff.iloc[0]
        _count_1 = row_1['count']
        _count_0 = row_0['count']

        _units_traded_1 = row_1['units_traded']
        _units_traded_0 = row_0['units_traded']

        _price_1 = row_1['price']
        _price_0 = row_0['price']

        return (_count_1, _count_0, _units_traded_1, _units_traded_0, _price_1, _price_0)


# mid price를 계산하는 함수
def cal_mid_price(gr_bid_level, gr_ask_level, mid_type):
    level = 5

    if len(gr_bid_level) > 0 and len(gr_ask_level) > 0:
        bid_top_price = gr_bid_level.iloc[0].price
        bid_top_level_qty = gr_bid_level.iloc[0].quantity
        ask_top_price = gr_ask_level.iloc[0].price
        ask_top_level_qty = gr_ask_level.iloc[0].quantity
        mid_price = (bid_top_price + ask_top_price) * 0.5

        if mid_type == 'wt':  # 가중치 중간 가격 계산
            mid_price = ((gr_bid_level.head(level))['price'].mean() + (gr_ask_level.head(level))['price'].mean()) * 0.5
        elif mid_type == 'mkt':  # 시장 중간 가격 계산
            mid_price = ((bid_top_price * ask_top_level_qty) + (ask_top_price * bid_top_level_qty)) / (bid_top_level_qty + ask_top_level_qty)
        return (mid_price)

    else:
        print('Error: serious cal_mid_price')
        return (-1)


# B/A ratio를 계산하는 함수
def cal_bid_ask_ratio(gr_ask_level, gr_bid_level):
    bid_top_price = gr_bid_level.iloc[0].price
    ask_top_price = gr_ask_level.iloc[0].price

    ratio = bid_top_price / ask_top_price
    return ratio


# book-imbalance를 계산하는 함수
def live_cal_book_i_v1(param, gr_bid_level, gr_ask_level, diff, var, mid):
    mid_price = mid

    ratio = param[0]
    level = param[1]
    interval = param[2]

    _flag = var['_flag']

    if _flag:  # 첫 줄 건너뛰기
        var['_flag'] = False
        return 0.0

    quant_v_bid = gr_bid_level.quantity ** ratio
    price_v_bid = gr_bid_level.price * quant_v_bid

    quant_v_ask = gr_ask_level.quantity ** ratio
    price_v_ask = gr_ask_level.price * quant_v_ask

    askQty = quant_v_ask.values.sum()
    bidPx = price_v_bid.values.sum()
    bidQty = quant_v_bid.values.sum()
    askPx = price_v_ask.values.sum()
    bid_ask_spread = interval

    book_price = 0  # 0으로 나누기 경고 방지
    if bidQty > 0 and askQty > 0:
        book_price = (((askQty * bidPx) / bidQty) + ((bidQty * askPx) / askQty)) / (bidQty + askQty)

    book_imbalance = (book_price - mid_price) / bid_ask_spread

    return book_imbalance


# book-delta를 계산하는 함수
def live_cal_book_d_v1(param, gr_bid_level, gr_ask_level, diff, var, mid):
    ratio = param[0]
    level = param[1]
    interval = param[2]

    decay = math.exp(-1.0 / interval)

    _flag = var['_flag']
    prevBidQty = var['prevBidQty']
    prevAskQty = var['prevAskQty']
    prevBidTop = var['prevBidTop']
    prevAskTop = var['prevAskTop']
    bidSideAdd = var['bidSideAdd']
    bidSideDelete = var['bidSideDelete']
    askSideAdd = var['askSideAdd']
    askSideDelete = var['askSideDelete']
    bidSideTrade = var['bidSideTrade']
    askSideTrade = var['askSideTrade']
    bidSideFlip = var['bidSideFlip']
    askSideFlip = var['askSideFlip']
    bidSideCount = var['bidSideCount']
    askSideCount = var['askSideCount']

    curBidQty = gr_bid_level['quantity'].sum()
    curAskQty = gr_ask_level['quantity'].sum()
    curBidTop = gr_bid_level.iloc[0].price
    curAskTop = gr_ask_level.iloc[0].price

    if _flag:
        var['prevBidQty'] = curBidQty
        var['prevAskQty'] = curAskQty
        var['prevBidTop'] = curBidTop
        var['prevAskTop'] = curAskTop
        var['_flag'] = False
        return 0.0

    if curBidQty > prevBidQty:
        bidSideAdd += 1
        bidSideCount += 1
    if curBidQty < prevBidQty:
        bidSideDelete += 1
        bidSideCount += 1
    if curAskQty > prevAskQty:
        askSideAdd += 1
        askSideCount += 1
    if curAskQty < prevAskQty:
        askSideDelete += 1
        askSideCount += 1

    if curBidTop < prevBidTop:
        bidSideFlip += 1
        bidSideCount += 1
    if curAskTop > prevAskTop:
        askSideFlip += 1
        askSideCount += 1

    (_count_1, _count_0, _units_traded_1, _units_traded_0, _price_1, _price_0) = diff

    bidSideTrade += _count_1
    bidSideCount += _count_1

    askSideTrade += _count_0
    askSideCount += _count_0

    if bidSideCount == 0:
        bidSideCount = 1
    if askSideCount == 0:
        askSideCount = 1

    bidBookV = (-bidSideDelete + bidSideAdd - bidSideFlip) / (bidSideCount ** ratio)
    askBookV = (askSideDelete - askSideAdd + askSideFlip) / (askSideCount ** ratio)
    tradeV = (askSideTrade / askSideCount ** ratio) - (bidSideTrade / bidSideCount ** ratio)
    bookDIndicator = askBookV + bidBookV + tradeV

    var['bidSideCount'] = bidSideCount * decay  # 지수 감쇠
    var['askSideCount'] = askSideCount * decay
    var['bidSideAdd'] = bidSideAdd * decay
    var['bidSideDelete'] = bidSideDelete * decay
    var['askSideAdd'] = askSideAdd * decay
    var['askSideDelete'] = askSideDelete * decay
    var['bidSideTrade'] = bidSideTrade * decay
    var['askSideTrade'] = askSideTrade * decay
    var['bidSideFlip'] = bidSideFlip * decay
    var['askSideFlip'] = askSideFlip * decay
    var['prevBidQty'] = curBidQty
    var['prevAskQty'] = curAskQty
    var['prevBidTop'] = curBidTop
    var['prevAskTop'] = curAskTop

    return bookDIndicator


# 입력 파일과 출력 파일 경로 설정
df = '2024-05-01-upbit-BTC-book.csv'
df_trade = '2024-05-01-upbit-BTC-trade.csv'
output_csv_file = '2024-05-01-BTC-Upbit-feature.csv'

# book-delta와 book-imbalance를 위한 변수 초기화
var_delta = {'_flag': True, 'prevBidQty': 0, 'prevAskQty': 0, 'prevBidTop': 0, 'prevAskTop': 0, 'bidSideAdd': 0,
             'bidSideDelete': 0, 'askSideAdd': 0, 'askSideDelete': 0, 'bidSideTrade': 0, 'askSideTrade': 0,
             'bidSideFlip': 0, 'askSideFlip': 0, 'bidSideCount': 0, 'askSideCount': 0}
var = {'_flag': True}


# Main
def main():
    group = get_sim_df(df)  # 입찰/요청 데이터 로드 및 그룹화
    group_trade = get_sim_df(df_trade)  # 거래 데이터 로드 및 그룹화

    output_data = []

    for (timestamp_o, gr_o), (timestamp_t, gr_t) in zip(group, group_trade):
        gr_bid_level = gr_o[(gr_o.type == 0)]  # 입찰 레벨 데이터
        gr_ask_level = gr_o[(gr_o.type == 1)]  # 요청 레벨 데이터

        # mid_price 계산
        mid_price = cal_mid_price(gr_bid_level, gr_ask_level, None)

        # mid_price_wt 계산
        mid_price_wt = cal_mid_price(gr_bid_level, gr_ask_level, 'wt')

        # mid_price_mkt 계산
        mid_price_mkt = cal_mid_price(gr_bid_level, gr_ask_level, 'mkt')

        # book-delta-v1-0.2-5-1 계산
        param_delta = [0.2, 5, 1]
        book_delta = live_cal_book_d_v1(param_delta, gr_bid_level, gr_ask_level, get_diff_count_units(gr_t), var_delta, mid_price)

        # book-imbalance 비율 0.2/0.4/0.6/0.8 레벨 5 간격 1 로 하여 계산
        param = [0.2, 5, 1]  # 비율, 레벨, 간격(초)
        book_imbalance_a = live_cal_book_i_v1(param, gr_bid_level, gr_ask_level, None, var, mid_price)
        param = [0.4, 5, 1]
        book_imbalance_b = live_cal_book_i_v1(param, gr_bid_level, gr_ask_level, None, var, mid_price)
        param = [0.6, 5, 1]
        book_imbalance_c = live_cal_book_i_v1(param, gr_bid_level, gr_ask_level, None, var, mid_price)
        param = [0.8, 5, 1]
        book_imbalance_d = live_cal_book_i_v1(param, gr_bid_level, gr_ask_level, None, var, mid_price)

        # spread 계산
        spread = gr_ask_level['price'].iloc[0] - gr_bid_level['price'].iloc[0]

        # B/A ratio 계산
        ratio = cal_bid_ask_ratio(gr_bid_level, gr_ask_level)

        # 결과 데이터를 리스트에 추가
        output_data.append([book_delta, book_imbalance_a, book_imbalance_b, book_imbalance_c, book_imbalance_d, mid_price, mid_price_wt, mid_price_mkt, ratio, spread, timestamp_t[0]])

    # 결과 데이터를 데이터프레임으로 변환 및 CSV 파일로 저장
    output_df = pd.DataFrame(output_data, columns=['book-delta-v1-0.2-5-1', 'book-imbalance-0.2-5-1', 'book-imbalance-0.4-5-1', 'book-imbalance-0.6-5-1', 'book-imbalance-0.8-5-1', 'mid_price', 'mid_price_wt', 'mid_price_mkt', 'B/A ratio', 'spread', 'timestamp'])
    output_df.to_csv(output_csv_file, index=False, header=True)


if __name__ == '__main__':
    main()
