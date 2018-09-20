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
import os
from threading import Timer

from vic.core.struct  import *
from binance_ws_thread import  BinaWsThread
from binance_http  import  BinaHttp

   
class BinaHttpThread(BinaWsThread, BinaHttp):
    '''
        实时获取账户订单和权益变动数据(推送 或者 用longpolling模式实现)
    '''
    def __init__(self, url, wss, channels, apikey, apisecret, queue=None, echname='BINA'):
        BinaHttp.__init__(self, url, apikey, apisecret)
        BinaWsThread.__init__(self, wss, channels, apikey, apisecret, queue, echname)
        self.__channels = channels
        self.daemon  = True
        self.__echname = echname 
        self.__stop = False
        #通过order计算成交 记录order信息
        self.__orders = {}
        self.__listenkey = ''

        orders = self.getOpenOrders()
        for order in orders:
            self.getQueue().append((DateType.ON_ACCOUNT_ORDER, self.__echname, order))
        balances = self.getAccountBalance()
        self.getQueue().append((DateType.ON_ACCOUNT_BALANCE, self.__echname, balances))

    def getsymbols(self):
        return self.__channels

  ####################################线程覆盖函数########################################################## 
    def thread_stream_keepalive(self):
        while True:
            try:
                resp = self.stream_keepalive(self.__listenkey)
                if(resp != {}) : 
                    logging.exception('stream_keepalive error return: %r', resp)
            except Exception, e:
                logging.exception(e)
            time.sleep(10*60)


    def onwss(self):
        data = self.stream_get_listen_key()
        if(not data) :
            logging.exception('stream_get_listen_key error.')
            return ''
            #os.__exit('__listenkey error') 
        self.__listenkey = data['listenKey'] 
        wss = self.getwss() + '/ws/' + self.__listenkey 
        #logging.info('wss : %r', wss)
        
        Timer(3, self.thread_stream_keepalive).start()
        
        return wss

    def onchannels(self):
        self.socket.onchannel('outboundAccountInfo', self.onaccount)
        self.socket.onchannel('executionReport', self.onorder)
    
    def onaccount(self, key, data):
        #更新权益信息
        #logging.info('%r : %r', key, data)
        for item in data['B']:
            obj = {}
            obj['currency'] = item['a'].upper()
            obj['free']     = item['f']
            obj['freezed']  = item['l']
            if(float(obj['free']) + float(obj['freezed']) < 0.00000001) :
                continue
            self.getQueue().append((DateType.ON_ACCOUNT_BALANCE, self.__echname, {self.__echname+'--'+ obj['currency'] : AccountBalance(obj)}))

  
    def onorder(self, key, data):
        instrument  = self.hb2bb(data['s'].lower())
        #logging.info('instrument: %r,  order: %r', instrument, data)

        # 只需要处理外平台挂单回报 在livebroker里面会过滤
        order = {}
        order['order_id']   = self.__echname + '--' + str(data['i'])
        order['status']     = self.__order_status(data['X'])
        order['symbol']     = instrument
        order['order_type'] = self.__bi2local_order_type(data['S'])
        order['price_type'] = self.__bi2local_price_type(data['o'])
        order['price']      = data['p']
        order['amount']     = data['q']
        order['deal_amount']= data['z']
        order['avg_price']  = data['L'] #用了最后成交价格代替
        order['datetime']   = datetime.datetime.utcfromtimestamp(int(data['T'])/1000)
        #根据order生成成交信息 一笔order可能多次成交
        self.getQueue().append((DateType.ON_ACCOUNT_ORDER, self.__echname, Order(order)))
        
        #只支持现价单  模拟成交这里的成交价格  
        if(order['order_id'] in self.__orders.keys()):
            diff = float(order['deal_amount']) - float(self.__orders[order['order_id']]['deal_amount'])
            if(diff > 0.00000001) :
                trade = {}
                trade['order_id']   = order['order_id']
                trade['volume']     = diff
                trade['price']      = order['price']
                trade['symbol']     = instrument
                trade['id']         = order['order_id'] + str(time.time())
                trade['fee']        = 0
                trade['order_type'] = order['order_type']
                trade['price_type'] = order['price_type']
                trade['datetime']   = datetime.datetime.utcnow()
                self.getQueue().append((DateType.ON_ACCOUNT_TRADE, self.__echname, Trade(trade)))
                self.__orders[order['order_id']]['deal_amount'] = order['deal_amount']
        else:
            self.__orders[order['order_id']] = order
        
        if(order['deal_amount'] == order['amount']):
            try:
                self.__orders.pop(order['order_id'])
            except Exception, e:
                pass

   ####################################线程覆盖函数########################################################## 
    
    def __local2bi_order_type(self, order_type):
        if order_type == OrderType.Buy:
            return 'BUY'
        elif order_type == OrderType.Sell:
            return 'SELL'
        else:
            raise Exception('local order_type ' + order_type + ' not support.')

    def __bi2local_order_type(self, order_type):
        if order_type == 'BUY':
            return OrderType.Buy
        elif order_type == 'SELL':
            return OrderType.Sell
        else:
            raise Exception('bina order_type ' + order_type + ' not support.')

    def __local2bi_price_type(self, price_type):
        if price_type == PriceType.Limit:                                            
            return 'LIMIT'                                                          
        elif price_type == PriceType.Market:                                         
            return 'MARKET'                                                         
        else:                                                                        
            raise Exception('local price_type ' + price_type + ' not support.')      

    def __bi2local_price_type(self, price_type):
        if price_type == 'LIMIT':
            return PriceType.Limit
        elif price_type == 'MARKET':
            return PriceType.Market
        else:
            raise Exception('bina price_type ' + price_type + ' not support.') 

    def __order_status(self, order_status):
        if order_status == 'CANCELED':
            return OrderStatus.CANCELD
        elif order_status == 'NEW':
            return OrderStatus.SUBMITED 
        elif order_status == 'PARTIALLY_FILLED':
            return OrderStatus.TRADEDPART
        elif order_status == 'FILLED':
            return OrderStatus.TRADED
        elif order_status == 'PENDING_CANCEL':
            return OrderStatus.SUBMITED
        elif order_status == 'REJECTED':
            return OrderStatus.CANCELD
        elif order_status == 'EXPIRED':
            return OrderStatus.CANCELD
        else:
            raise Exception('binance order_status ' + order_status + ' not support.')

    ############################对应livebroker接口##############################################
    def getOpenOrders(self):
        '''
            :程序启动的时候获取所有的打开的订单
        '''
        #查询所有打开的order 根据订阅列表 TODO
        orders = []
        jsonResponse = self.openorders()
        if not jsonResponse and jsonResponse != []: 
            raise Exception('query orders fail.')
        
        def func(order) :
            order['datetime']   = datetime.datetime.utcfromtimestamp(int(order['time'])/1000) 
            order['order_id'] = self.__echname + '--' + str(order['orderId'])
            order['status']  = self.__order_status(order['status'])
            order['symbol']  = self.hb2bb(order['symbol'].lower())
            order['price'] =  order['price'] 
            order['amount'] = order['origQty']
            order['deal_amount'] = order['executedQty']
            order['order_type'] = self.__bi2local_order_type(order['side'])
            order['price_type'] = self.__bi2local_price_type(order['type'])
            order['fee'] =  0
            return Order(order)
 
        for order in jsonResponse:
            if(order['status']=='EXPIRED' or 
               order['status']=='REJECTED' or 
               order['status']=='FILLED' or
               order['status']=='CANCELED') :
                continue
            orders.append(func(order))
            self.__orders[order['order_id']] = order

        return orders    

    def getAccountBalance(self, symbol=None):
        '''
            程序启动的时候获取权益
            这里获取的是spot 币币账户的权益信息。  杠杆账户每一个都是独立账户！！！
        '''
        jsonResponse =  self.account()
        if not jsonResponse : return None
        #logging.info(jsonResponse)
        
        balance = {}
        for item in jsonResponse['balances']:
            if(float(item['free']) + float(item['locked']) < 0.00000001) : 
                continue
            key = self.__echname + '--' + item['asset']
            balance[key] = AccountBalance({'currency': item['asset'], 'free': item['free'], 'freezed': item['locked']})
        return balance

    def submitOrder(self, symbol, order_type, price_type, limit_price, order_quantity):
        '''
            submitOrder(order.getInstrument(), ordertype,  PriceType.Limit, order.getLimitPrice(), order.getLimitPrice(),  order.getQuantity())
            {"result":true,"order_id":123456}


        '''
        jsonResponse = self.place_order(str(self.bb2hb(symbol)).upper(), limit_price, order_quantity, self.__local2bi_price_type(price_type), self.__local2bi_order_type(order_type))
        #logging.info(jsonResponse)
        if(not jsonResponse or 'orderId' not in jsonResponse): return None
        
        jsonResponse['order_id'] = self.__echname + '--' + str(jsonResponse['orderId'])
        jsonResponse['price']    = limit_price
        jsonResponse['amount']   = order_quantity
        jsonResponse['datetime'] = datetime.datetime.utcnow() 
        jsonResponse['symbol']   = symbol
        jsonResponse['deal_amount']= 0
        jsonResponse['status']= OrderStatus.SUBMITED
        jsonResponse['order_type'] = order_type 
        jsonResponse['price_type'] = price_type
              
        return Order(jsonResponse)
   

    def cancelOrder(self, symbol, orderid): 
        '''
            统一接口则一次都只取消一个订单
            orderid: 订单ID(多个订单ID中间以","分隔,一次最多允许撤消3个订单)
            return : {"success":"123456,123457","error":"123458,123459"}
        '''
        #logging.info('cancle symbol:%r, orderid:%r', symbol, orderid)
        
        #orderid need to process

        jsonResponse = self.cancel_order(str(self.bb2hb(symbol)), str(orderid))
        if(not jsonResponse): 
            return False
        return True

    
    ############################对应livebroker接口##############################################

  

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')

    wss = "wss://stream.binance.com:9443"
    apiKey   = "i5gVlrajCWSpQulsTbYZUC1Prp2TvxPxF16jjYnHSdo13LfFAi0fUEAjd0Vu7DME"
    apiSecret= "OYzRJA6B2gxAkETIg1eDGJWZsf1unz5Rrl1aVewelkB3iNLUsArYWedOtonBNeTe"
    url = "https://api.binance.com"
    
    channels = ['BINA--LTC--ETH', 'BINA--ETC--ETH', 'BINA--BTC--ETH']
    
    th = BinaHttpThread(url, wss, channels, apiKey, apiSecret)
    th.start()
    while True:
        logging.info('main thread run.')
        time.sleep(3)
    
    


