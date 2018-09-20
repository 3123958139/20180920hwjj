# -*- coding: utf-8 -*-
# @Date    : 2018-03-06 15:40:03
# @Author  : DreamyZhang
# @QQ      : 775745576
import sys
import requests
import urllib
import json
import logging
import time
import datetime
import hmac
import hashlib
import requests
import threading
import Queue

from vic.core.struct  import *

from bitmex_ws_thread import  BitmexWsThread
from bitmex_http import  BitmexHttp

   
class BitmexHttpThread(BitmexWsThread, BitmexHttp):
    '''
        实时获取账户订单和权益变动数据(推送 或者 用longpolling模式实现)
    '''
    def __init__(self, url, wss, channels, apikey, apisecret, queue=None, echname='BITM'):
        BitmexHttp.__init__(self, url, apikey, apisecret)
        BitmexWsThread.__init__(self, wss, channels, apikey, apisecret, queue, echname)
        self.__echname = echname 

    ############################线程覆盖函数#############################################
    def onorder(self, key, data):
        logging.info('%r  %r', key, data)
        for item in data:
            if 'side' not in item.keys(): continue
            instrument = self.bm2ft(item['symbol'])
            if(instrument is None): continue

            order = {}
            order['symbol']     = instrument
            order['order_id']   = self.__echname+'--' + str(item['orderID'])
            order['order_type'] = self.__bm2local_order_type(item['side'])
            order['price_type'] = self.__bm2local_price_type(item['ordType'])
            order['price']      = item['price']
            order['amount']     = item['orderQty']
            order['deal_amount']= item['orderQty'] - item['leavesQty']
            order['status']     = self.__order_status(item['ordStatus'])
            order['fee']        = 0
            order['datetime']   = item['timestamp']
            #self.getQueue().append((DateType.ON_ACCOUNT_BALANCE, self.__echname, {self.__echname+'--' + obj['currency'] : AccountBalance(obj)}))
    
    def ontrade(self, key, data):
        #logging.info('%r  %r', key, data)
        for item in data:
            instrument = self.bm2ft(item['symbol'])
            if(instrument is None): continue
            
            trade = {}
            trade['symbol']     = instrument
            trade['order_id']   = self.__echname+'--' + str(item['orderID'])
            trade['price']      = item['price']
            trade['volume']     = item['orderQty'] - item['leavesQty']
            trade['id']         = item['execID']
            trade['fee']        = 0
            order['order_type'] = self.__bm2local_order_type(item['side'])
            order['price_type'] = self.__bm2local_price_type(item['ordType'])
            trade['datetime']   = item['timestamp']
        
    def onposition(self, key, data):
        positions = {}
        #logging.info('key: %r,  position: %r', key, data)
        for item in data:
            if 'maintMargin' not in item.keys() or 'avgEntryPrice' not in item.keys():
                continue
            instrument = self.bm2ft(item['symbol'])
            if(instrument is None): continue
            
            position = {}
            position['symbol']          = instrument
            position['position']        = item['currentQty']
            if(position['position'] > 0):
                position['direction']       = Direction.Long
            elif(position['position'] < 0):
                position['direction']       = Direction.Short 
            else:
                continue
            position['margin']          = item['maintMargin'] #item['margin']
            position['avgprice']        = item['avgEntryPrice']
            
            position['closeprofit']     = 0
            position['positionprofit']  = 0
            position['fee']             = 0
            position['openvolume']      = 9
            position['closevolume']     = 0
            position['openamount']      = 0
            position['closeamount']     = 0
            position['contract']        = item['symbol']
            key = position['symbol'] + '--' +  position['direction']
            positions[key] = Position(position)
            #logging.info('key: %r,  position: %r', key, item)
        self.getQueue().append((DateType.ON_ACCOUNT_POSITION, self.__echname, positions))

    def onmargin(self, key, data):
        logging.info('%r %r', key, data)
        for item in data:
            account = {}
            account['currency']      = item['currency'].upper()
            account['fee']           = 0
            account['margin']        = item['maintMargin']
            account['freezed']       = 0
            account['free']          = item['marginBalance'] - item['maintMargin']
            
            account['positionprofit']= 0
            account['closeprofit']   = 0
            account['datetime']      = datetime.datetime.utcnow()
        self.getQueue().append((DateType.ON_ACCOUNT_BALANCE, self.__echname, {self.__echname+'--'+account['currency']: AccountBalance(account)}))

    def onwallet(self, key, data):
        logging.info('%r  %r', key, data)
    
    def ontransact(self, key, data):
        logging.info('%r  %r', key, data)

    def subcribe(self, socket):
        socket.subcribe('instrument')
        socket.subcribe('execution')
        socket.subcribe('order')
        socket.subcribe('position')
        #账户余额和保证金更新
        socket.subcribe('margin')
        #资金提存更新
        #socket.subcribe('transact')
        #比特币余额更新及总提款存款
        #socket.subcribe('wallet')
        socket.onchannel('instrument', self.oninstrument)
        socket.onchannel('execution', self.ontrade)
        socket.onchannel('order', self.onorder)
        socket.onchannel('position', self.onposition)
        socket.onchannel('margin', self.onmargin)
        #socket.onchannel('transact', self.ontransact)
        #socket.onchannel('wallet', self.onwallet)
    
    ############################线程覆盖函数#############################################
    def __local2bm_order_type(self, order_type):
        '''local ---> bitmex'''
        if order_type == OrderType.Buy:
            return 'buy'
        elif order_type == OrderType.Sell:
            return 'sell'
        else:
            raise Exception('local order_type ' + order_type + ' not support.') 

    def __bm2local_order_type(self, order_type):
        '''local ---> bitmex'''
        if order_type == 'buy':
            return OrderType.Buy
        elif order_type == 'sell':
            return OrderType.Sell
        elif order_type == 'buy_market':
            return OrderType.Buy
        elif order_type == 'sell_market':
            return OrderType.Sell
        else:
            raise Exception('bm order_type ' + order_type + ' not support.') 
 
    def __local2bm_price_type(self, price_type):
        '''local ---> bitmex'''
        if price_type == PriceType.Limit:
            return ''
        elif price_type == PriceType.Market:
            return '_market'
        else:
            raise Exception('local price_type ' + price_type + ' not support.') 

    def __bm2local_price_type(self, price_type):
        '''local ---> bitmex'''
        if price_type == 'buy':
            return PriceType.Limit
        elif price_type == 'sell':
            return PriceType.Limit
        elif price_type == 'buy_market':
            return PriceType.Market
        elif price_type == 'sell_market':
            return PriceType.Market
        else:
            raise Exception('local price_type ' + price_type + ' not support.') 

    def __order_status(self, order_status):
        ''' bitmex ----> local
            -1：已撤销  0：未成交 1：部分成交 2：完全成交 4:撤单处理中
        '''
        if order_status == -1:
            return OrderStatus.CANCELD
        elif order_status == 0:
            return OrderStatus.SUBMITED 
        elif order_status == 1:
            return OrderStatus.TRADEDPART
        elif order_status == 2:
            return OrderStatus.TRADED
        elif order_status == 3:
            return OrderStatus.SUBMITED
        else:
            raise Exception('bitmex order_status ' + order_status + ' not support.')
    ############################对应livebroker接口##############################################
    def getOpenOrders(self):
        '''通过push获取'''
        return []

    def getAccountBalance(self, symbol=None):
        '''通过push获取'''
        return {}

    def submitOrder(self, symbol, order_type, price_type, limit_price, order_quantity):
        '''
            submitOrder(order.getInstrument(), ordertype,  PriceType.Limit, order.getLimitPrice(), order.getLimitPrice(),  order.getQuantity())
            {"result":true,"order_id":123456}

        '''
        _order_type  = self.__local2bm_order_type(order_type)
        _price_type = self.__local2bm_price_type(price_type)
        
        jsonResponse = self.place_order(self.ft2bm(symbol), _order_type, limit_price, order_quantity,  _price_type)
        
        if(not jsonResponse): return None

        #如果有反向单子表示平仓
        jsonResponse['order_id'] = self.__echname+'--' + str(jsonResponse['order_id'])
        jsonResponse['order_type']     = order_type 
        jsonResponse['price_type']     = price_type 
        jsonResponse['price']    = limit_price
        jsonResponse['amount']   = order_quantity
        jsonResponse['datetime'] = datetime.datetime.utcnow() 
        jsonResponse['symbol']   = symbol
        jsonResponse['deal_amount']= 0
        jsonResponse['status']= OrderStatus.SUBMITED
               
        return Order(jsonResponse)
   

    def cancelOrder(self, orderid=0): 
        '''
        '''
        logging.info('cancel orderid:%r', orderid)
        jsonResponse = None
        if orderid == 0:
            jsonResponse = self.cancel_order(orderid)
        else:
            jsonResponse = self.cancel_all()

        if(not jsonResponse): 
            return False

        return True
    
    ############################对应livebroker接口##############################################

  

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')

    apikey    = 'xShYIkq6c964NqKMH7cP1f3j'
    apisecret = 'ehWvEyF80IkmkwTJbB5-DiLSlJP8k6WWJiEXyhIdmYaskrBR'
    url       = "https://www.bitmex.com"
    wss = "wss://www.bitmex.com/realtime"

    channels = ['BITM--LTC--ETH', 'BITM--ETC--ETH', 'BITM--BTC--ETH']
    
    th = BitmexHttpThread(url, wss, channels, apikey, apisecret)
    th.start()
    while True:
        logging.info('main thread run.')
        time.sleep(3)
    



