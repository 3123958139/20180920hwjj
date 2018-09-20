# -*- coding: utf-8 -*-

from threading import Timer

MINNUM = 0.00000001

class DateType:
    '''only 0-49֮��'''
    #for market trade 
    ON_TIMESTAMP = 0

    #for market data
    ON_MKT_TRADE     = 11
    ON_MKT_SNAP      = 12
    ON_MKT_KLINE     = 13
    ON_MKT_ORDER_BOOK= 14
    
    #for account balance
    ON_ACCOUNT_BALANCE  = 21
    ON_ACCOUNT_TRADE    = 22
    ON_ACCOUNT_ORDER    = 23
    ON_ACCOUNT_POSITION = 24

class OrderType:
    Buy  = 'buy'
    Sell = 'sell'

class Offset:
    Open  = 'open'
    Close = 'close'
    #ǿƽ
    Force = 'force'
    #ǿ��
    ForceOff = 'forceoff'
    #����
    Settlement = 'settlement'

class Direction:
    '''�ֲַ���'''
    Long = 'long'
    Short= 'short'

class PriceType:
    Limit = 'limit'
    Market = 'market'
    Stop  = 'stop'
    MarginLimit = 'marginlimit'

class OrderStatus:
    SUBMITED = 'submited'
    CANCELD  = 'canceld'   
    TRADEDPART = 'tradedpart'
    TRADED = 'traded'

############################mkt data#############################################
class Bar(object):
    def __init__(self, _dict):
        self.__dict = _dict

    def get(self):
        return self.__dict

    def timestamp(self):
        return self.get()['timestamp']

    def symbol(self):
        return self.get()['symbol']
    
    def period(self):
        return self.get()['period']

    def high(self):
        return float(self.get()['high'])
       
    def open(self):
        return float(self.get()['open'])

    def low(self):
        return float(self.get()['low'])
  
    def close(self):
        return float(self.get()['close'])
    
    def volume(self):
        return float(self.get()['volume']) 

    def amount(self):
        return float(self.get()['amount'])

    def openinterest(self):
        ''' �ֱֲ仯'''
        return float(self.get()['openinterest'])

class Ticker:
    def __init__(self, _dict):
        self.__dict = _dict

    def get(self):
        return self.__dict

    def timestamp(self):
        return self.get()['timestamp']

    def symbol(self):
        return self.get()['symbol']

    def id(self):
        return self.get()['id']

    def price(self):
        return float(self.get()['price'])
    
    def volume(self):
        return float(self.get()['volume']) 

    def amount(self):
        return self.price() * self.volume()

    def isbuy(self):
        return self.get()['direction'] == 'buy'

    def issell(self):
        return self.get()['direction'] == 'sell'

    def side(self):
        return 1 if self.isbuy() else 2

    def openinterest(self):
        ''' �ֱֲ仯'''
        return float(self.get()['openinterest'])



class OrderBook:
    def __init__(self, instrument,  _dict):
        self.__dateTime = _dict['timestamp']
        self.__instrument = instrument
        self.__ask = _dict['asks']
        self.__bid = _dict['bids'] 

    def symbol(self):
        return self.__instrument

    def timestamp(self):
        return self.__dateTime

    def bid_prices(self):
        return [float(bid[0]) for bid in self.__bid]

    def bid_volumes(self):
        return [float(bid[1]) for bid in self.__bid]

    def ask_prices(self):
        return [float(ask[0]) for ask in self.__ask]

    def ask_volumes(self):
        return [float(ask[1]) for ask in self.__ask]


############################mkt data#############################################


#########################for trade data start###########################################
class AccountBalance(object):
    '''
        {currency: '', free:'', freezed:''}}
    '''
    def __init__(self, _dict):
        self.__dict = _dict

    def get(self):
        return self.__dict
    
    def balance(self):
        return self.available() + self.freezed()

    def available(self):
        return float(self.get()['free'])

    def freezed(self):
        return float(self.get()['freezed'])
    
    def currency(self):
        return self.get()['currency']
    
    def fee(self):
        return float(self.get()['fee'])

    def margin(self):
        return float(self.get()['margin'])


    def close_profit(self):
        return float(self.get()['closeprofit'])
    
    def position_profit(self):
        return float(self.get()['positionprofit'])
    
    def timestamp(self):
        return (self.get()["timestamp"])
    
    def risk_rate(self):
        return (self.get()["risk_rate"])


class Order(object):
    '''
        {order_id: '', type:'', price:'', amount:'', deal_amount:'', timestamp:'', symbol:'' fee:'', status:''}
    '''
    def __init__(self, _dict):
        self.__dict = _dict

    def get(self):
        return self.__dict

    def id(self):
        return (self.get()["order_id"])

    def order_type(self): #һ�����ƽ  �ڻ�������
        return (self.get()["order_type"])

    def price_type(self):
        return (self.get()["price_type"])
    
    def isbuy(self):
        return self.get()["order_type"] == OrderType.Buy

    def issell(self):
        return self.get()["order_type"] == OrderType.Sell

    def price(self):
        return float(self.get()["price"])
    
    def volume(self):
        return float(self.get()["amount"])
    
    def deal_volume(self):
        return float(self.get()["deal_amount"])

    def symbol(self):
        return self.get()['symbol']
    
    def fee(self):
        return self.__dict.get('fee') if self.__dict.get('fee') else 0
    
    def status(self):
        return self.get()['status']

    def timestamp(self):
        return (self.get()["timestamp"])

    # for future
    def lever_rate(self): #�ܸ˱���
        return self.get()['lever_rate']
  
    def offset(self): #��ƽ��־
        return self.get()['offset']


class Trade(object):
    def __init__(self, _dict):
        self.__dict = _dict

    def get(self):
        return self.__dict

    def volume(self):
        return float(self.get()["volume"])

    def amount(self):       #Amount
        return self.volume() * self.price()

    def price(self):    #price
        return float(self.get()["price"])

    def fee(self):       #����
        return float(self.get()["fee"])

    def id(self):        #tradeid
        return (self.get()["id"])

    def orderid(self):   #orderid
        return self.get()["order_id"]

    def symbol(self):
        return self.get()['symbol']

    def timestamp(self):
        return (self.get()["timestamp"])

    def order_type(self):
        return (self.get()["order_type"])

    def price_type(self):
        return (self.get()["price_type"])


    # for future
    def offset(self): #��ƽ��־
        return self.get()['offset']


class Position(object):
    #preposition     ;    /*�����ֲܳ�       
    #preholdposition ;    /*�������         
    #todayholdposition;   /*�������         
    #premargin       ;    /*����ռ�õı�֤�� 
    #margin          ;    /*��ǰռ�õı�֤�� 
    def __init__(self, _dict):
        self.__dict = _dict

    def get(self):
        return self.__dict
    
    def id(self):
        return self.get()['id']

    def symbol(self):
        return self.get()['symbol']

    def direction(self):
        return self.get()['direction']

    def position(self):
        return self.get()['position']
    
    def avg_price(self):
        return self.get()['avgprice']
 
    def margin(self):
        return self.get()['margin']
    
    
    def close_profit(self):
        return self.get()['closeprofit']

    def position_profit(self):
        return self.get()['positionprofit']

    def fee(self):
        return self.get()['fee']
    
    def open_volume(self):
        return self.get()['openvolume']
    
    def close_volume(self):
        return self.get()['closevolume']

    def open_amount(self):
        return self.get()['openamount']

    def close_amount(self):
        return self.get()['closeamount']
      
    ############################����õ�#########################################
    def lever_rate(self): #�ܸ˱���
        return self.get()['lever_rate']
   
    def balance(self): 
        return self.get()['balance']
    
    def forced_price(self): #ǿƽ�۸�
        return self.get()['forcedprice']

    def timestamp(self):
        return (self.get()["timestamp"])
    
    def contract(self):
        return (self.get()["contract"])


#########################for market data start###########################################
#########################for market data end###########################################


def schedule(interval, func, args):
    def run(interval, func, args): 
        func(args)
        Timer(interval, run, (interval, func, args)).start()
    Timer(interval, run, (interval, func, args)).start()






