import pandas as pd
import pandas_ta as ta1
from math import *
import time
from binance.client import Client
from datetime import datetime
import ta 
import discord
### API
binance_api_key = 'PzP'    #Enter your own API-key here
binance_api_secret = 'MR' #Enter your own API-secret here


### CONSTANTS
client = Client(api_key=binance_api_key, api_secret=binance_api_secret)

# Parameters
pairSymbol = 'ADAUSDT'
fiatSymbol = 'USDT'
cryptoSymbol = 'ADA'
myTruncate = 2

def truncate(n, decimals=0):
  r = floor(float(n)*10**decimals)/10**decimals
  return str(r)



def getHistorical(symbole):
  klinesT = client.get_historical_klines(symbole, Client.KLINE_INTERVAL_1HOUR, "10 day ago UTC")
  dataT = pd.DataFrame(klinesT, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
  dataT['close'] = pd.to_numeric(dataT['close'])
  dataT['high'] = pd.to_numeric(dataT['high'])
  dataT['low'] = pd.to_numeric(dataT['low'])
  dataT['open'] = pd.to_numeric(dataT['open'])
  dataT['volume'] = pd.to_numeric(dataT['volume'])
  dataT.drop(dataT.columns.difference(['open','high','low','close','volume']), 1, inplace=True)
  return dataT


df = getHistorical(pairSymbol)


#mom
df['Mom'] = ta1.mom(close=df["close"],length=10)
df['Mom10'] = df['Mom'].shift(1).rolling(window=10).min()
#CCI
df ['cci']= ta.trend.cci(high=df['high'], low=df['low'],close=df['close'], window=13, constant=0.015)
df['cci10h'] = df['cci'].shift(1).rolling(window=4).max()
df['cci10l'] = df['cci'].shift(1).rolling(window=10).min()


# Initialize Bollinger Bands Indicator
indicator_bb = ta.volatility.BollingerBands(close=df["close"], window=10, window_dev=2)

# Add Bollinger Bands features
df['bb_bbm'] = indicator_bb.bollinger_mavg()
df['bb_bbh'] = indicator_bb.bollinger_hband()
df['bb_bbl'] = indicator_bb.bollinger_lband()


df['bbp'] = indicator_bb.bollinger_pband()


df['bb10h'] = df['bbp'].shift(1).rolling(window=4).max()
df['bb10l'] = df['bbp'].shift(1).rolling(window=4).min()



#RSI
df['RSI'] = ta1.rsi(close=df["close"],length=44)

print(df)
actualPrice = df['close'].iloc[-1]
fiatAmount = client.get_asset_balance(asset=fiatSymbol)['free']
cryptoAmount = client.get_asset_balance(asset=cryptoSymbol)['free']
minToken = 1/actualPrice
prePrice =  df['close'].iloc[-3]
evoPrice= ((actualPrice-prePrice)/prePrice)*100
print (str(datetime.now()))
print ('prix avant:',prePrice)

print(pairSymbol,'price :',actualPrice)
print(fiatSymbol,'blance :',fiatAmount)
print(cryptoSymbol,'blance :',cryptoAmount)

if  ( df['Mom'].iloc[-2] < df['Mom10'].iloc[-2]
      ):
    if float(fiatAmount) > 1:
        quantityBuy = truncate(float(fiatAmount)/actualPrice, myTruncate)
        buyOrder = client.order_market_buy(
            symbol=pairSymbol,
            quantity=quantityBuy)
        print("BUY",buyOrder)
        messages= pairSymbol, "ordre d'achat déclanché"
    else:
        print("If you give me more",fiatSymbol,"I will use them to BUY")
        messages= "Tu as de l'" + cryptoSymbol +" pour " + str(int(cryptoAmount * actualPrice)) +"$ soit "+ str(round(evoPrice,2))+"% "+"en H1"

elif (df['Mom'].iloc[-2] <df['Mom10'].iloc[-2]) :
    if float(cryptoAmount) > minToken:
        sellOrder = client.order_market_sell(
            symbol=pairSymbol,
            quantity=truncate(cryptoAmount,myTruncate))
        print("SELL",sellOrder)
        messages= pairSymbol, "ordre de vente déclanché"
    else:
        print("If you give me more",cryptoSymbol,"I will SELL them")
        messages= "Ton compte " + pairSymbol +" est à  " + str(fiatAmount) + " " + fiatSymbol
else :
  if float(fiatAmount) > 1 and float(cryptoAmount) < minToken:
       messages= "Ton compte " + pairSymbol +" est à  " + str(fiatAmount) + " " + fiatSymbol
  elif float(cryptoAmount) > minToken:
      messages= "Tu as de l'" + cryptoSymbol +" pour " + str((int(cryptoAmount)) * (int(actualPrice))) +"$ soit "+ str(round(evoPrice,2))+"% "+"en H1"
  else:
       print("No opportunity to take")
