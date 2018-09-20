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
from huobi_http  import  HuobiHttp

   
class HuobiHttpThread(threading.Thread, HuobiHttp):
    '''
        ʵʱ��ȡ�˻�������Ȩ��䶯����(���� ���� ��longpollingģʽʵ��)
    '''
    def __init__(self, url, wss, channels, apikey, apisecret, queue=None, echname='HUOBI'):
        HuobiHttp.__init__(self, url, apikey, apisecret)
        threading.Thread.__init__(self)
        self.__channels = channels
        self.daemon  = True
        self.__echname = echname
        self.__orders = {} 
        self.__stop = False
        self.__account = None #��¼�˻���Ϣ
        self.__queue = queue
        if queue is None:
            self.__queue = Queue.deque()
        #ÿ3sһ����ѵ���ɽ� Ȩ��
        self.__sleep = 3 
        #�����г��ĳɽ�id�ǵ�����
        self.__last_tradeid = 0
        self.__last_orderid = 0
        
        self.__bits_round = {}
        self.__get_symbol_bits()
       
        #ԭʼ��order
        self.__open_orders = {}
        trades = self.orders_matchresults(size=1)
        if(not trades or trades['status'] != 'ok') : 
            raise Exception('huobi trade query error:' + str(trades))
        if(len(trades['data']) > 0):
            self.__last_orderid = trades['data'][-1]['order-id']
            self.__last_tradeid = trades['data'][-1]['id']
    
        orders = self.getOpenOrders()
        for order in orders:
            self.__queue.append((DateType.ON_ACCOUNT_ORDER, self.__echname, order))
        balances = self.getAccountBalance()
        self.__queue.append((DateType.ON_ACCOUNT_BALANCE, self.__echname, balances))

    def __get_symbol_bits(self):
        symbols  = self.symbols()
        for data in symbols['data']:
            symbol = self.__echname + '--' + data['base-currency'].upper() + '--'  + data['quote-currency'].upper()
            if symbol in self.__channels:
                self.__bits_round[symbol] = data['amount-precision']

    def __round(self, symbol, quantity):
        bit = self.__bits_round.get(symbol)
        return round(quantity, bit)

    def hb2bb(self, c):
        ''' btcusdt----> HB--BTC--USDT'''
        #ĩβ�������� USDT BTC ETH  USDT�����ں���
        n = -3
        if(c.lower().find('usdt') > 0) : n = -4
        return (self.__echname+'--' + c[:n].upper() + '--' +  c[n:].upper())
    
    def bb2hb(self, c):
        '''HUOBI--BTC--USDT ----> btcusdt'''
        return c.replace(self.__echname+'--', '').replace('--','').lower()
    
    def getsymbols(self):
        return self.__channels
    
    #################################�̴߳�����#################################################
    def start(self):
        super(HuobiHttpThread, self).start()
        self.__stop = False

    def stop(self):
        self.__stop = True

    def run(self):
        '''
            ÿ��3s��ѯ���100���ĳɽ����� ����ǲ��ǳɽ���
            �ټ�һ����ѯʱ���
        '''
        while True:
            if(self.__stop) : break
            try:
                #��ѯtrade Ȼ����³ɽ�
                trades = self.getTrade()
                for trade in trades:
                    self.__queue.append((DateType.ON_ACCOUNT_TRADE, self.__echname, Trade(trade)))
                
                orderids = [int(trade['order_id'].replace(self.__echname+'--', '')) for trade in trades]
                orders = self.OpenOrders(orderids)
                for order in orders:
                    self.__queue.append((DateType.ON_ACCOUNT_ORDER, self.__echname, order))
                
                if(len(trades) > 0 or len(orders) > 0):
                    balance = self.getAccountBalance()
                    self.__queue.append((DateType.ON_ACCOUNT_BALANCE, self.__echname, balance))

            except Exception, e:
                logging.exception(e)
            time.sleep(self.__sleep)

    def getTrade(self):
        trades = self.orders_matchresults(_from=self.__last_tradeid, direct='prev')
        if(not trades) : 
            raise Exception('query trade fail.')
        if(trades['status'] != 'ok') : 
            raise Exception('huobi trade query error:' + str(trades))
        if(len(trades['data']) == 0) : return []
        
        trades['data'].reverse()
        data = []
        for trade in trades['data']:
            if(trade['id'] <= self.__last_tradeid) : continue
            new_trade = {}
            new_trade['id']         = self.__echname+'--' + str(trade['id'])
            new_trade['order_id']   = self.__echname+'--' + str(trade['order-id'])
            new_trade['volume']     = trade['filled-amount']
            new_trade['price']      = trade['price']
            new_trade['symbol']     = self.hb2bb(trade['symbol'])
            new_trade['fee']        = trade['filled-fees']
            new_trade['order_type'] = self.__hb2local_order_type(trade['type']) 
            new_trade['price_type'] = self.__hb2local_price_type(trade['type']) 
            new_trade['datetime']   = datetime.datetime.utcfromtimestamp(trade['created-at']/1000)
            data.append(new_trade)
        self.__last_tradeid = trades['data'][-1]['id']
        return data
   
    def OpenOrders(self, orderids):
        '''ʵʱ����order��Ϣ'''
        #��ȡ��Сorderid ÿ�β�ѯ������Сid��ѯ��
        if(len(self.__open_orders) > 0):
            self.__last_orderid = min(self.__open_orders.keys())
        
        jsonResponse = self.orders(_from = self.__last_orderid, direct='prev')
        if not jsonResponse : 
            raise Exception('query orders fail.')
        if jsonResponse['status'] != 'ok':
            raise Exception('query orders fail: %s' %(jsonResponse))
        if(len(jsonResponse['data']) == 0): return []
       
        #���˵�����δ�ɽ��ҵ�֮���û�б仯��order
        orders = []
        for order in jsonResponse['data']:
            #logging.info(order)
            if(self.__open_orders.get(order['id'])):
                if(order['state'] != self.__open_orders[order['id']]['state']):
                    orders.append(order)
                    self.__open_orders[order['id']] = order
                if(order['state'] in ['canceled', 'filled', 'partial-canceled']):
                    try:
                        self.__open_orders.pop(order['id'])
                    except:
                        pass
            elif(order['state'] in ['pre-submitted', 'submitted', 'partial-filled']):
                self.__open_orders[order['id']] = order
                orders.append(order)
            elif order['id'] in orderids:
                orders.append(order)
            else:
                pass
        return [self.func(order) for order in orders]

    #################################�̴߳�����#################################################
    def __local2hb_order_type(self, order_type):
        '''local ---> huobi'''
        if order_type == OrderType.Buy:
            return 'buy'
        elif order_type == OrderType.Sell:
            return 'sell'
        else:
            raise Exception('local order_type ' + order_type + ' not support.')
    
    def __hb2local_order_type(self, order_type):
        #��ҵĶ���״̬ת������
        if order_type == 'buy-limit':
            return OrderType.Buy
        elif order_type == 'sell-limit':
            return OrderType.Sell
        elif order_type == 'buy-market':
            return OrderType.Buy
        elif order_type == 'sell-market':
            return OrderType.Sell
        else:
            raise Exception('hb order_type ' + order_type + ' not support.')
    
    def __local2hb_price_type(self, price_type):
        if price_type == PriceType.Limit:
            return '-limit'
        elif price_type == PriceType.Market:
            return '-market'
        else:
            raise Exception('local price_type ' + price_type + ' not support.')
    
    def __hb2local_price_type(self, price_type):
        if price_type == 'buy-limit':
            return PriceType.Limit
        elif price_type == 'sell-limit':
            return PriceType.Limit
        elif price_type == 'buy-market':
            return  PriceType.Market
        elif price_type == 'sell-market':
            return  PriceType.Market
        else:
            raise Exception('huobi price_type ' + price_type + ' not support.')

    def __order_status(self, order_status):
        if order_status == 'canceled':
            return OrderStatus.CANCELD
        elif order_status == 'submitted':
            return OrderStatus.SUBMITED 
        elif order_status == 'partial-filled':
            return OrderStatus.TRADEDPART
        elif order_status == 'filled':
            return OrderStatus.TRADED
        elif order_status == 'pre-submitted':
            return OrderStatus.SUBMITED
        elif order_status == 'partial-canceled':
            return OrderStatus.TRADED
        else:
            raise Exception('huobi order_status ' + order_status + ' not support.') 
    
    def func(self, order) :
        obj = {}
        obj['datetime']   = datetime.datetime.utcfromtimestamp(int(order['finished-at'])/1000) 
        obj['order_id'] = self.__echname+'--' + str(order['id'])
        obj['status']  = self.__order_status(order['state'])
        obj['symbol']  = self.hb2bb(order['symbol'])
        obj['price'] =  order['price'] 
        obj['amount'] = order['amount']
        obj['deal_amount'] = order['field-amount']
        obj['order_type'] = self.__hb2local_order_type(order['type']) 
        obj['price_type'] = self.__hb2local_price_type(order['type']) 
        obj['fee'] =  order['field-fees']
        return Order(obj)
       

    ############################��Ӧlivebroker�ӿ�##############################################
    def getOpenOrders(self):
        '''
            :����������ʱ���ȡ���еĴ򿪵Ķ���
        '''
        #��ѯ���д򿪵�order ���ݶ����б� TODO
        jsonResponse = self.orders(states='pre-submitted,submitted,partial-filled')
        if not jsonResponse : 
            raise Exception('query orders fail.')
        if jsonResponse['status'] != 'ok':
            raise Exception('query orders fail: %s' %(jsonResponse))
       
        for order in jsonResponse['data']:
            self.__open_orders[order['id']] = order
        
        return [self.func(order) for order in jsonResponse['data']]

    def getAccountBalance(self):
        '''
            ����������ʱ���ȡȨ��
            �����ȡ����spot �ұ��˻���Ȩ����Ϣ��  �ܸ��˻�ÿһ�����Ƕ����˻�������
        '''
        jsonResponse =  self.accounts()
        if not jsonResponse : return None
        if jsonResponse['status']!='ok' : return None
        
        #logging.info(jsonResponse)
        self.__account = [a for a in jsonResponse['data'] if a['type']=='spot'][0]
        if(len(self.__account) < 1) : 
            raise Exception('query account none.')

        jsonResponse = self.balance(self.__account['id'])
        if not jsonResponse : return None
        if jsonResponse['status'] != 'ok': return None

        balance = {}
        for item in jsonResponse['data']['list']:
            if(float(item['balance']) < 0.00000001) : continue
           
            item['currency'] = item['currency'].upper()

            key = self.__echname+'--' + item['currency']
            if(not balance.get(key)) :  balance[key] = {'currency': item['currency'], 'free': 0.0, 'freezed':0.0}

            if(item['type'] == 'trade') :  balance[key]['free'] = item['balance']
            if(item['type'] == 'frozen') : balance[key]['freezed'] = item['balance']
       
        push = {}
        for key in balance.keys():  push[key] = AccountBalance(balance[key])
        return push

    def submitOrder(self, symbol, order_type, price_type, limit_price, order_quantity):
        '''
            submitOrder(order.getInstrument(), ordertype,  PriceType.Limit, order.getLimitPrice(), order.getLimitPrice(),  order.getQuantity())
            {"result":true,"order_id":123456}

        '''
        _order_type = self.__local2hb_order_type(order_type) + self. __local2hb_price_type(price_type)
        order_quantity = self.__round(symbol, order_quantity)
        jsonResponse = self.place_order(self.__account['id'], self.bb2hb(symbol), str(limit_price), str(order_quantity),  _order_type)
        
        #place_order(self, accountid, symbol, amount, price, source,  type):
        
        if(not jsonResponse): return None
        
        if(not jsonResponse.get('status') or jsonResponse['status']!='ok'):
            logging.info('addorder fail:%r  %r', symbol, str(jsonResponse))
            return None

        jsonResponse['order_id'] = self.__echname+'--' + str(jsonResponse['data'])
        jsonResponse['order_type']     = order_type 
        jsonResponse['price_type']     = price_type 
        jsonResponse['price']    = limit_price
        jsonResponse['amount']   = order_quantity
        jsonResponse['datetime'] = datetime.datetime.utcnow() 
        jsonResponse['symbol']   = symbol
        jsonResponse['deal_amount']= 0
        jsonResponse['status']= OrderStatus.SUBMITED
               
        #self.__open_orders[jsonResponse['data']] = {'state': 'pre-submitted' , 'id': jsonResponse['data']}
       
        return Order(jsonResponse)
   

    def cancelOrder(self, symbol, orderid): 
        '''
            ͳһ�ӿ���һ�ζ�ֻȡ��һ������
            orderid: ����ID(�������ID�м���","�ָ�,һ�����������3������)
            return : {"success":"123456,123457","error":"123458,123459"}
        '''
        #logging.info('cancle symbol:%r, orderid:%r', symbol, orderid)

        jsonResponse = self.cancel_order(str(orderid))
        if(jsonResponse): 
            return True
        return False
        
    
    ############################��Ӧlivebroker�ӿ�##############################################

  

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')

    apikey = "3af5ee91-4bc1407b-d68cd6a5-7291b"
    apisecret    = "319c3ea1-88eeb820-a80d5ae8-3f93b"
    url = "https://api.huobi.pro"
    
    channels = ['HUOBI--LTC--USDT', 'HUOBI--ETH--USDT', 'HUOBI--BTC--ETH']
    
    th = HuobiHttpThread(url, url, channels, apikey, apisecret)
    th.start()
    while True:
        logging.info('main thread run.')
        time.sleep(3)
    
    


