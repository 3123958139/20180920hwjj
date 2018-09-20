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

from bs4 import BeautifulSoup

from vic.core.struct  import *

from okex_ws_thread import  OkexWsThread
from okex_http import  OkexHttp

   
class OkexHttpThread(OkexWsThread, OkexHttp):
    '''
        实时获取账户订单和权益变动数据(推送 或者 用longpolling模式实现)
    '''
    def __init__(self, url, wss, channels, apikey, apisecret, queue=None, echname='OKEX'):
        OkexHttp.__init__(self, url, apikey, apisecret)
        OkexWsThread.__init__(self, wss, channels, apikey, apisecret, queue, echname)
    
        self.__channels = channels
        self.__echname = echname
        self.__orders = {}
        self.__bits_round = self.__get_symbol_bits()
       
        orders = self.getOpenOrders()
        for order in orders:
            self.getQueue().append((DateType.ON_ACCOUNT_ORDER, self.__echname, order))
        balances = self.getAccountBalance()
        self.getQueue().append((DateType.ON_ACCOUNT_BALANCE, self.__echname, balances))

    def getsymbols(self):
        return self.__channels
    
    def __get_symbol_bits(self):
        url = 'https://github.com/okcoin-okex/API-docs-OKEx.com/blob/master/%E5%B8%81%E5%AF%B9%E7%B2%BE%E5%BA%A6(pairs_increment).csv'
        response = requests.get(url, headers={}, timeout=15)
        if response.status_code != 200: 
            #logging.info('%r %r',  response.status_code)
            raise Exception('okex http error.')
        symbols = {}
        doc = BeautifulSoup(response.text, "html.parser")
        trs = doc.select('table > tbody > tr')
        for tr in trs:
            td = tr.select('td')
            symbol = self.ok2bb(td[2].text)
            mini = float(td[3].text)
            if symbol in self.__channels:
                symbols[symbol] = mini
        return symbols
    
    def __round(self, symbol, quantity):
        ''' 可操作的符号必然在这里 '''
        bit = self.__bits_round.get(symbol)
        return int(quantity / bit) * bit


    ############################线程覆盖函数#############################################
    def on_account_order(self, key, data):
        '''
            {u'orderId': 34148006, u'status': 0, u'tradeType': u'buy', u'tradeUnitPrice': u'0.20000000', u'symbol': u'ltc_eth', u'tradePrice': u'0.00000000', u'createdDate': u'1522399315443', u'averagePrice': u'0', u'tradeAmount': u'0.100000', u'completedTradeAmount': u'0.000000'}
            status(int):-1已撤销,0等待成交,1部分成交,2完全成交,4撤单处理中
        
        '''
        #兼容多交易所 
        data['orderId'] = self.__echname + '--' + str(data['orderId'])
        data['status']  = self.__order_status(data['status'])
        data['order_type'] = self.__ok2local_order_type(data['tradeType'])
        data['price_type'] = self.__ok2local_price_type(data['tradeType'])

        instrument  = self.ok2bb(key.replace('_order', '').replace('ok_sub_spot_', ''))
        #logging.info('instrument: %r,  order: %r', key, data)
       
        #撤单怎么更新到本地
        #等待成交 和  部分成交  完全成交  撤单处理

        # 只需要处理外平台挂单回报 在livebroker里面会过滤
        order = {}
        order['order_id']   = data['orderId']
        order['status']     = data['status']
        order['symbol']     = instrument
        order['order_type'] = data['order_type']
        order['price_type'] = data['price_type']
        order['price']      = data['tradeUnitPrice']
        order['amount']     = data['tradeAmount']
        order['deal_amount']= data['completedTradeAmount']
        order['avg_price']  = data['averagePrice']
        order['datetime']   = datetime.datetime.utcfromtimestamp(int(data['createdDate'])/1000)
        #根据order生成成交信息 一笔order可能多次成交
        self.getQueue().append((DateType.ON_ACCOUNT_ORDER, self.__echname,  Order(order)))

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

    def on_account_balance(self, key, data):
        '''
            {u'binary': 0, u'data': {u'info': {u'freezed': {u'eth': 0.02}, u'free': {u'eth': 0.08}}}, u'channel': u'ok_sub_spot_ltc_eth_balance'}
        '''
        instrument  = self.ok2bb(key.replace('_balance', '').replace('ok_sub_spot_', ''))
        #logging.info('instrument: %r,  order: %r', key, data)
        
        obj = {}
        obj['currency'] = data['info']['free'].keys()[0]
        obj['freezed']  = data['info']['freezed'][obj['currency']]
        obj['free']     = data['info']['free'][obj['currency']]
        obj['currency'] = obj['currency'].upper()

        self.getQueue().append((DateType.ON_ACCOUNT_BALANCE, self.__echname, {self.__echname + '--' + obj['currency'] : AccountBalance(obj)}))

    def subcribe(self, socket):
        for channel in self.getchannels():
            channel = 'ok_sub_spot_' + channel
            #订阅账户order
            socket.subcribe(channel+'_order')
            socket.onchannel(channel+'_order', self.on_account_order)
            #订阅账户权益变动
            socket.subcribe(channel+'_balance')
            socket.onchannel(channel+'_balance', self.on_account_balance)
    ############################线程覆盖函数#############################################
    
    def __local2ok_order_type(self, order_type):
        '''local ---> okex'''
        if order_type == OrderType.Buy:
            return 'buy'
        elif order_type == OrderType.Sell:
            return 'sell'
        else:
            raise Exception('local order_type ' + order_type + ' not support.') 

    def __ok2local_order_type(self, order_type):
        '''local ---> okex'''
        if order_type == 'buy':
            return OrderType.Buy
        elif order_type == 'sell':
            return OrderType.Sell
        elif order_type == 'buy_market':
            return OrderType.Buy
        elif order_type == 'sell_market':
            return OrderType.Sell
        else:
            raise Exception('ok order_type ' + order_type + ' not support.') 
 
    def __local2ok_price_type(self, price_type):
        '''local ---> okex'''
        if price_type == PriceType.Limit:
            return ''
        elif price_type == PriceType.Market:
            return '_market'
        else:
            raise Exception('local price_type ' + price_type + ' not support.') 

    def __ok2local_price_type(self, price_type):
        '''local ---> okex'''
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
        ''' okex ----> local
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
            raise Exception('okex order_status ' + order_status + ' not support.')
    ############################对应livebroker接口##############################################
    def getOpenOrders(self):
        '''
            :程序启动的时候获取所有的打开的订单
        '''
        #查询所有打开的order 根据订阅列表 TODO
        orders = []
        for symbol in self.getchannels():
            jsonResponse = self.orderinfo(symbol)
            if not jsonResponse : 
                raise Exception('query orders fail.')
            if 'result' not in jsonResponse.keys():
                if 'error_code' in jsonResponse and jsonResponse['error_code']==1007: continue #没有这个市场的订单
                raise Exception('query orders false symbol: %s, resp:%s' %(symbol, json.dumps(jsonResponse)))
            if jsonResponse['result'] == False:
                if jsonResponse['error_code'] == 1007: continue #没有这个市场的订单
                raise Exception('query orders false symbol: %s, resp:%s' %(symbol, json.dumps(jsonResponse)))

            def func(order) :
                obj = {}
                obj['datetime']   = datetime.datetime.utcfromtimestamp(int(order['create_date'])/1000) 
                obj['order_id']   = self.__echname + '--' + str(order['order_id'])
                obj['status']     = self.__order_status(order['status'])
                obj['symbol']     = self.ok2bb(order['symbol'])
                obj['order_type'] = self.__ok2local_order_type(order['type'])
                obj['price_type'] = self.__ok2local_price_type(order['type'])
                obj['price']      = order['price'] 
                obj['amount']     = order['amount'] 
                obj['deal_amount']= order['deal_amount'] 
                obj['avg_price']  = order['avg_price']
                return Order(obj)
            orders += [func(order) for order in jsonResponse['orders']]
            for o in jsonResponse['orders'] : self.__orders[o['order_id']] = o
        return orders    

    def getAccountBalance(self, symbol=None):
        '''
            程序启动的时候获取权益
        '''
        jsonResponse =  self.userinfo()
        if not jsonResponse : return None
        if not jsonResponse['result'] : return None
        #logging.info(jsonResponse)

        balance = {}
        free  = jsonResponse['info']['funds']['free'] 
        freezed = jsonResponse['info']['funds']['freezed'] 
        keys = set(free.keys() + freezed.keys())
        for key in keys:
            if( free.get(key) == None ) : free[key] = 0.0
            if( freezed.get(key) == None ) : freezed[key] = 0.0
            if(float(free[key]) < 0.000001 and float(freezed[key]) < 0.000001) : continue
            #logging.info('currency : %r,  free : %r,  freezed : %r', key, free[key], freezed[key])
            balance[self.__echname + '--' + key.upper()] = AccountBalance({'currency': key.upper(), 'free': float(free[key]), 'freezed': float(freezed[key])})
        
        return balance

    def submitOrder(self, symbol, order_type, price_type, limit_price, order_quantity):
        '''
            submitOrder(order.getInstrument(), ordertype,  PriceType.Limit, order.getLimitPrice(), order.getLimitPrice(),  order.getQuantity())
            {"result":true,"order_id":123456}

        '''
        _order_type  = self.__local2ok_order_type(order_type) + self.__local2ok_price_type(price_type)
        order_quantity = self.__round(symbol, order_quantity)

        jsonResponse = self.addorder(self.bb2ok(symbol), _order_type, limit_price, order_quantity)
        
        if(not jsonResponse): return None
        
        if(not jsonResponse.get('result')):
            logging.info('addorder fail:%r  %r', symbol, jsonResponse)
            return None

        jsonResponse['order_id'] = self.__echname + '--' + str(jsonResponse['order_id'])
        jsonResponse['order_type']     = order_type 
        jsonResponse['price_type']     = price_type 
        jsonResponse['price']    = limit_price
        jsonResponse['amount']   = order_quantity
        jsonResponse['datetime'] = datetime.datetime.utcnow() 
        jsonResponse['symbol']   = symbol
        jsonResponse['deal_amount']= 0
        jsonResponse['status']= OrderStatus.SUBMITED
               
        return Order(jsonResponse)
   

    def cancelOrder(self, symbol, orderid): 
        '''
            统一接口则一次都只取消一个订单
            orderid: 订单ID(多个订单ID中间以","分隔,一次最多允许撤消3个订单)
            return : {"success":"123456,123457","error":"123458,123459"}
        '''
        #logging.info('cancle symbol:%r, orderid:%r', symbol, orderid)

        jsonResponse = self.cancelorder(self.bb2ok(symbol), str(orderid))
        if(not jsonResponse): 
            return False
        return True
    
    ############################对应livebroker接口##############################################

  

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')

    apikey    = 'db98cb7e-71c4-442d-bf45-8c6ab05a4c1c'
    apisecret = '4A5F6437B9DE1A2B16E80FC0018C8515'
    url       = "https://www.okex.com/api/v1"

    #http = OkexHttp(url, apikey, apisecret)

    #print (' 现货行情 ')
    #print (http.klines('1min', 'ltc_btc', 10))
    #print (http.orderinfo('bch_eth'))
   
    wss = "wss://real.okex.com:10441/websocket"
    #channels = ['OKEX--LTC--ETH']
    channels = ['OKEX--BTC--USDT', 'OKEX--ETH--USDT', 'OKEX--ETC--USDT', 'OKEX--BCH--USDT', 'OKEX--LTC--USDT', 'OKEX--NEO--USDT', 'OKEX--XUC--USDT', 'OKEX--EOS--USDT', 'OKEX--XRP--USDT', 'OKEX--BTG--USDT', 'OKEX--OMG--USDT', 'OKEX--ZEC--USDT', 'OKEX--BTM--USDT', 'OKEX--TRX--USDT', 'OKEX--DASH--USDT', 'OKEX--QTUM--USDT']
    th = OkexHttpThread(url, wss, channels, apikey, apisecret)
    th.start()
    while True:
        logging.info('main thread run.')
        time.sleep(3)
    
    #print (u' 现货历史交易信息 ')
    #print (http.trades())

    print (' 用户现货账户信息 ')
    print (http.userinfo())

    #print (u' 现货下单 ')
    #print (http.trade('ltc_usd','buy','0.1','0.2'))

    #print (u' 现货批量下单 ')
    #print (http.batchTrade('ltc_usd','buy','[{price:0.1,amount:0.2},{price:0.1,amount:0.2}]'))

    #print (u' 现货取消订单 ')
    #print (http.cancelOrder('ltc_usd','18243073'))

    #print (u' 现货订单信息查询 ')
    print (http.orderinfo('bch_eth'))

    #print (u' 现货批量订单信息查询 ')
    print (http.ordersinfo('ltc_eth','6426168,34144382','0'))

    #print (u' 现货历史订单信息查询 ')
    #print (http.orderHistory('ltc_usd','0','1','2'))

    #print (u' 期货行情信息')
    #print (okcoinFuture.future_ticker('ltc_usd','this_week'))

    #print (u' 期货市场深度信息')
    #print (okcoinFuture.future_depth('btc_usd','this_week','6'))

    #print (u'期货交易记录信息') 
    #print (okcoinFuture.future_trades('ltc_usd','this_week'))

    #print (u'期货指数信息')
    #print (okcoinFuture.future_index('ltc_usd'))

    #print (u'美元人民币汇率')
    #print (okcoinFuture.exchange_rate())

    #print (u'获取预估交割价') 
    #print (okcoinFuture.future_estimated_price('ltc_usd'))

    #print (u'获取全仓账户信息')
    #print (okcoinFuture.future_userinfo())

    #print (u'获取全仓持仓信息')
    #print (okcoinFuture.future_position('ltc_usd','this_week'))

    #print (u'期货下单')
    #print (okcoinFuture.future_trade('ltc_usd','this_week','0.1','1','1','0','20'))

    #print (u'期货批量下单')
    #print (okcoinFuture.future_batchTrade('ltc_usd','this_week','[{price:0.1,amount:1,type:1,match_price:0},{price:0.1,amount:3,type:1,match_price:0}]','20'))

    #print (u'期货取消订单')
    #print (okcoinFuture.future_cancel('ltc_usd','this_week','47231499'))

    #print (u'期货获取订单信息')
    #print (okcoinFuture.future_orderinfo('ltc_usd','this_week','47231812','0','1','2'))

    #print (u'期货逐仓账户信息')
    #print (okcoinFuture.future_userinfo_4fix())

    #print (u'期货逐仓持仓信息')
    #print (okcoinFuture.future_position_4fix('ltc_usd','this_week',1))




