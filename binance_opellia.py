from symtable import Symbol
import ccxt 
import time
import datetime
from numpy import short
import pandas as pd
api_key = '6zHOZK1HIAidFdxoGxHR5GB85VOqCZ7VbbKXdBz8Ne6XfFUG4feKcPfVw15o0Ew1'
secret = 'PevYip6CONYhgYKdNTVnGjIYGS03hptq09jqUgsCUlLFlJJXJ7KcTXUyGmJmEVcl'
binance = ccxt.binance(config={
    'apiKey': api_key, 
    'secret': secret,
    'enableRateLimit': False,
    'options': {
        'defaultType': 'future'
    }
})

def cal_target(self,coin,origin):
   try: 
    btc = binance.fetch_ohlcv(
        symbol=coin,
        timeframe='1d', 
        since=None, 
        limit=10)
    df = pd.DataFrame(data=btc, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    long_target = today['open'] + (yesterday['high'] - yesterday['low']) * 0.5
    short_target = today['open'] - (yesterday['high'] - yesterday['low']) * 0.5
    if origin == 'long':
     return long_target
    if origin == 'short':
     return short_target 
    if origin == False:
     return today['open']
   except Exception as e:
     print(e,"3")
def cal_amount(usdt_balance, cur_price):
   try: 
    amount = ((usdt_balance * 1000000)/cur_price) / 1000000
    return amount 
   except Exception as e:
     print(e,"2")  

def enter_position(exchange, coin, cur_price,long_target,short_target, coin_amount, position,bought_coin):
    origin = False
    open = cal_target(binance,'BTCUSDT',origin)
    bitcoin = binance.fetch_ticker("BTC/USDT")
    coin2 = coin.replace("/","")
    if open <= bitcoin['last']:
        btc = True
    else:
        btc = False
    if (long_target * 1.01 >=cur_price >= long_target) and btc:    
        binance.fapiPrivate_post_leverage({  
            'symbol': coin2,  
            'leverage': position['leverege'],  
        })
        exchange.create_market_buy_order(
            symbol= coin, 
            amount= coin_amount * position['leverege'],             
            params={'type': 'future'})
        position['buy_coin'] = coin
        position['buy_price'] = cur_price
        position['amount'] = coin_amount * position['leverege']
        position['type'] = 'long'
        bought_coin.append(coin)  
        print("지구 롱")
    if (long_target * 1.01>= cur_price >= long_target) and btc == False:      
        binance.fapiPrivate_post_leverage({  
            'symbol': coin2,  
            'leverage': position['leverege'], 
        })
        exchange.create_market_sell_order(
            symbol= coin, 
            amount= coin_amount * position['leverege'],             
            params={'type': 'future'}) 
        position['buy_coin'] = coin
        position['buy_price'] = cur_price
        position['amount'] = coin_amount * position['leverege']
        position['type'] = 'short'
        bought_coin.append(coin)
        print("지구 숏")
    if short_target*0.99 <= cur_price <= short_target:
        binance.fapiPrivate_post_leverage({  
            'symbol': coin2,  
            'leverage': position['leverege'], 
        })
        exchange.create_market_sell_order(
            symbol= coin, 
            amount= coin_amount * position['leverege'],             
            params={'type': 'future'}) 
        position['buy_coin'] = coin
        position['buy_price'] = cur_price
        position['amount'] = coin_amount * position['leverege']
        position['type'] = 'short'
        bought_coin.append(coin)
        print("지구 숏") 
def exit_position(exchange, position):
    amount = position['amount']
    coin = position['buy_coin']
    if position['type'] == 'short':
        exchange.create_market_buy_order(symbol=coin, amount=amount)
        position['type'] = None 
        position['buy_coin'] = ""
    if position['type'] == 'long':
        exchange.create_market_sell_order(symbol=coin, amount=amount)
        position['type'] = None 
        position['buy_coin'] = ""
coin = ""
start = True
markets = binance.load_markets() 
long_target = [0 for i in markets.keys()]
short_target = [0 for i in markets.keys()]
position = {"type": None,"amount":0,"buy_coin":"","buy_price":0,"leverege":6} 
bought_coin = []
m =0
k = 0

while True: 
  try:
    now = datetime.datetime.now()                     
    if position["buy_coin"] == "":
     markets = binance.load_markets()  
    n = 0
    for i in markets.keys():
      if 'USDT' in i: 
          n = n + 1  
    Market= ["" for i in range(n)]
    n = 0
    for i in markets.keys():
       if 'USDT' in i: 
        Market[n] = i
        n = n + 1
    if m < len(Market):                                               
        coin = Market[m]                             
        if now.hour == 9 and now.minute == 00 and (0 <= now.second < 10): 
            if op_mode:                               
                exit_position(binance, position)
                op_mode = False
                bought_coin = []
                start = False
                long_target = [0 for i in markets.keys()]
                short_target = [0 for i in markets.keys()]
        if now.hour == 9 and now.minute == 00:               
            start = True
        if start:
         if long_target[m] == 0 and short_target[m]== 0:
          long = 'long'
          short = 'short'
          long_target[m] = cal_target(binance,coin,long)
          short_target[m] = cal_target(binance,coin,short)
         balance = binance.fetch_balance()        
         usdt = balance['total']['USDT']   
         op_mode = True
         ticker = binance.fetch_ticker(coin)
         cur_price = ticker['last']              
        if op_mode and position['type'] is None and len(bought_coin) < 20: 
            amount = cal_amount(usdt, cur_price)
            a = 16- len(coin)
            b = 11 - len(str(usdt))
            c = 11 - len(str(cur_price))
            d = 25 - len(str(long_target[m]))
            print(coin,a * "_",usdt,b * "_",cur_price,c * "_",long_target[m],d * "_",short_target[m])
            enter_position(binance, coin, cur_price,long_target[m],short_target[m], amount, position,bought_coin)
        if op_mode and position['type'] is not None:
            ticker = binance.fetch_ticker(position['buy_coin'])
            cur_price = ticker['last']
            if position['type'] == 'long':
                if cur_price <= (position['buy_price']) * 0.95:
                   exit_position(binance, position)
                   print("돔황차")
                   print(usdt)
                if cur_price >= (position['buy_price']) * 1.05:
                   exit_position(binance, position) 
                   print("익절")
                   print(usdt)
            if position['type'] == 'short':
                if cur_price >= (position['buy_price']) * 1.05:
                   exit_position(binance, position)
                   print("돔황차")
                   print(usdt)
                if cur_price <= (position['buy_price']) * 0.95:
                   exit_position(binance, position) 
                   print("익절")
                   print(usdt)
            time.sleep(3)
        time.sleep(0.1)
        m = m + 1
    else:
        m = 0
  except Exception as e:
      print(e,"1")
      m = m + 1
      time.sleep(5)   
     
