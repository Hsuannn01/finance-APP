import os
# os.chdir(r'C:\Users\user\Dropbox\系務\專題實作\112\金融看板\for students')
#import haohaninfo
#from order_Lo8 import Record
import numpy as np
#from talib.abstract import SMA,EMA, WMA, RSI, BBANDS, MACD
#import sys
import indicator_f_Lo2_short, datetime, indicator_forKBar_short
import datetime
import pandas as pd
import streamlit as st 
import streamlit.components.v1 as stc 


###### (1) 開始設定 ######
html_temp = """
		<div style="background-color:#3872fb;padding:10px;border-radius:10px">
		<h1 style="color:white;text-align:center;">金融資料視覺化呈現 (金融看板) </h1>
		<h2 style="color:white;text-align:center;">Financial Dashboard </h2>
		</div>
		"""
stc.html(html_temp)

#df = pd.read_excel("kbars_台積電_1100701_1100708_2.xlsx")
#df = pd.read_excel("kbars_2330_2022-07-01-2022-07-31.xlsx")

# ## 讀取 excel 檔
# df_original = pd.read_excel("kbars_2330_2022-01-01-2022-11-18.xlsx")

# ## 保存为Pickle文件:
# df_original.to_pickle('kbars_2330_2022-01-01-2022-11-18.pkl')

## 读取Pickle文件
@st.cache(ttl=3600, show_spinner="正在加載資料...")
def load_data(url):
    df = pd.read_pickle(url)
    return df 

df_original = load_data('kbars_2330_2022-01-01-2022-11-18.pkl')

df_original = df_original.drop('Unnamed: 0', axis=1)

##### 選擇資料區間
st.subheader("選擇開始與結束的日期, 區間:2022-01-03 至 2022-11-18")
start_date = st.text_input('選擇開始日期 (日期格式: 2022-01-03)', '2022-01-03')
end_date = st.text_input('選擇結束日期 (日期格式: 2022-11-18)', '2022-11-18')
start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
df = df_original[(df_original['time'] >= start_date) & (df_original['time'] <= end_date)]

###### (2) 轉化為字典 ######
KBar_dic = df.to_dict()
KBar_open_list = list(KBar_dic['open'].values())
KBar_dic['open'] = np.array(KBar_open_list)
KBar_dic['product'] = np.repeat('tsmc', KBar_dic['open'].size)
KBar_time_list = list(KBar_dic['time'].values())
KBar_time_list = [i.to_pydatetime() for i in KBar_time_list]
KBar_dic['time'] = np.array(KBar_time_list)
KBar_low_list = list(KBar_dic['low'].values())
KBar_dic['low'] = np.array(KBar_low_list)
KBar_high_list = list(KBar_dic['high'].values())
KBar_dic['high'] = np.array(KBar_high_list)
KBar_close_list = list(KBar_dic['close'].values())
KBar_dic['close'] = np.array(KBar_close_list)
KBar_volume_list = list(KBar_dic['volume'].values())
KBar_dic['volume'] = np.array(KBar_volume_list)
KBar_amount_list = list(KBar_dic['amount'].values())
KBar_dic['amount'] = np.array(KBar_amount_list)

###### (3) 改變 KBar 時間長度 ######
Date = start_date.strftime("%Y-%m-%d")
st.subheader("設定一根 K 棒的時間長度")

##### 新增下拉式選單 ####
cycle_duration_value = st.number_input('輸入一根 K 棒的時間數值', value=1, key="KBar_duration_value")
cycle_duration_unit = st.selectbox('選擇一根 K 棒的時間單位', options=['月', '週', '日', '小時', '分鐘'], key="KBar_duration_unit")

if cycle_duration_unit == '小時':
    cycle_duration_minutes = cycle_duration_value * 60
elif cycle_duration_unit == '日':
    cycle_duration_minutes = cycle_duration_value * 60 * 24
elif cycle_duration_unit == '週':
    cycle_duration_minutes = cycle_duration_value * 60 * 24 * 7
elif cycle_duration_unit == '月':
    cycle_duration_minutes = cycle_duration_value * 60 * 24 * 30
else:
    cycle_duration_minutes = cycle_duration_value

KBar = indicator_forKBar_short.KBar(Date, cycle_duration_minutes)

for i in range(KBar_dic['time'].size):
    time = KBar_dic['time'][i]
    open_price = KBar_dic['open'][i]
    close_price = KBar_dic['close'][i]
    low_price = KBar_dic['low'][i]
    high_price = KBar_dic['high'][i]
    qty = KBar_dic['volume'][i]
    KBar.AddPrice(time, open_price, close_price, low_price, high_price, qty)

###### 形成新的 KBar 字典 ######
KBar_dic = {
    'time': KBar.TAKBar['time'],
    'product': np.repeat('tsmc', KBar.TAKBar['time'].size),
    'open': KBar.TAKBar['open'],
    'high': KBar.TAKBar['high'],
    'low': KBar.TAKBar['low'],
    'close': KBar.TAKBar['close'],
    'volume': KBar.TAKBar['volume']
}

###### (4) 計算各種技術指標 ######
KBar_df = pd.DataFrame(KBar_dic)

##### (i) 移動平均線策略 #####
st.subheader("設定計算長移動平均線(MA)的 K 棒數目")
LongMAPeriod = st.slider('選擇一個整數', 0, 100, 10)
st.subheader("設定計算短移動平均線(MA)的 K 棒數目")
ShortMAPeriod = st.slider('選擇一個整數', 0, 100, 2)

KBar_df['MA_long'] = KBar_df['close'].rolling(window=LongMAPeriod).mean()
KBar_df['MA_short'] = KBar_df['close'].rolling(window=ShortMAPeriod).mean()
last_nan_index_MA = KBar_df['MA_long'][::-1].index[KBar_df['MA_long'][::-1].apply(pd.isna)][0]

##### (ii) RSI 策略 #####
st.subheader("設定計算長RSI的 K 棒數目")
LongRSIPeriod = st.slider('選擇一個整數', 0, 1000, 10)
st.subheader("設定計算短RSI的 K 棒數目")
ShortRSIPeriod = st.slider('選擇一個整數', 0, 1000, 2)

def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

KBar_df['RSI_long'] = calculate_rsi(KBar_df, LongRSIPeriod)
KBar_df['RSI_short'] = calculate_rsi(KBar_df, ShortRSIPeriod)
KBar_df['RSI_Middle'] = np.array([50] * len(KBar_dic['time']))
last_nan_index_RSI = KBar_df['RSI_long'][::-1].index[KBar_df['RSI_long'][::-1].apply(pd.isna)][0]

###### (5) 將 Dataframe 欄位名稱轉換 ######
KBar_df.columns = [i[0].upper() + i[1:] for i in KBar_df.columns]

###### (6) 畫圖 ######
st.subheader("畫圖")
import plotly.graph_objects as go
from plotly.subplots import make_subplots

##### K線圖, 移動平均線 MA #####
with st.expander("K線圖, 移動平均線"):
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Candlestick(x=KBar_df['Time'],
                    open=KBar_df['Open'], high=KBar_df['High'],
                    low=KBar_df['Low'], close=KBar_df['Close'], name='K線'),
                   secondary_y=True)
    fig1.add_trace(go.Bar(x=KBar_df['Time'], y=KBar












