# -*- coding: utf-8 -*-
# @Date    : 2018-03-06 15:40:03
# @Author  : DreamyZhang
# @QQ      : 775745576

import base64
import datetime
import hashlib
import hmac
import json
import urllib
import requests
import urlparse
import logging
import time

from vic.exchange.common.http import HttpClient
import logging

class BitmexHttp(HttpClient):
    def __init__(self, url, apikey, apisecret):
        super(BitmexHttp, self).__init__(url, apikey, apisecret)
        self.header  = {
                "Content-type": "application/x-www-form-urlencoded",
                "Accept": "application/json", 
                'api-key'   : apikey,
                'api-expires': '0',
                'api-signature':''
            } 
  
    def __sign(self, method, path, data=''):
        #get data=''   path = paht+query
        #and the data, if present, must be JSON without whitespace between keys.
        nonce = str(int(round(time.time()) + 10))
        message = (method + path + str(nonce) + data).encode('utf-8')
        logging.info(bytes(message).encode('utf-8'))
        signature = hmac.new(self.getApiSecret().encode('utf-8'), bytes(message).encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
        self.header.update({'api-signature': signature, 'api-expires':nonce})
        return signature 
      
    def http_get_request_sign(self, method, query=None, **args):
        params = {}
        params.update(**args)
        if query is not None: params.update(query)
        if params : method = '{method}?{params}'.format(method=method, params=urllib.urlencode(params))
        self.__sign('GET', method)
        self.header.update({'X-Requested-With' : 'XMLHttpRequest'})
        return self.http_request(self.getUrl()+method, 'GET', None, self.header)
    
    def http_get_request(self, method, query=None, **args):
        params = {}
        params.update(**args)
        if query is not None: params.update(query)
        header = {
                "Accept": "application/json"} 
        if params : method = '{method}?{params}'.format(method=method, params=urllib.urlencode(params))
        return self.http_request(self.getUrl()+method, 'GET',  None, header)
    
    def http_post_request(self, method, query=None, **args):
        params = {}
        params.update(**args)
        if query is not None: params.update(query)
        if params : method = '{method}?{params}'.format(method=method, params=urllib.urlencode(params))
        self.__sign('POST', method)
        self.header.update({'X-Requested-With' : 'XMLHttpRequest'})
        return self.http_request(self.getUrl()+method, 'POST', None, self.header)

    def http_put_request(self, method, query=None, **args):
        params = {}
        params.update(**args)
        if query is not None: params.update(query)
        if params : method = '{method}?{params}'.format(method=method, params=urllib.urlencode(params))
        self.__sign('PUT', method)
        self.header.update({'X-Requested-With' : 'XMLHttpRequest'})
        return self.http_request(self.getUrl()+method, 'PUT', None, self.header)

    def http_delete_request(self, method, query=None, **args):
        params = {}
        params.update(**args)
        if query is not None: params.update(query)
        if params : method = '{method}?{params}'.format(method=method, params=urllib.urlencode(params))
        self.__sign('DELETE', method)
        self.header.update({'X-Requested-With' : 'XMLHttpRequest'})
        return self.http_request(self.getUrl()+method, 'DELETE', None, self.header)

    ####################market data api start################################
    def announcement(self):
        ''' GET '''
        return self.http_get_request('/api/v1/announcement')          
    
    def announcement_urgent(self):
        ''' GET '''
        return self.http_get_request('/api/v1/announcement/urgent')          
       
    def funding(self, symbol='', count=0, filter=''):
        ''' GET '''
        params = {}
        if symbol: params['symbol'] = symbol
        if count!=0: params['count'] = count
        if filter: params['filter'] = filter
        return self.http_get_request('/api/v1/funding')          

    def instrument(self, symbol='', count=0, filter=''):
        ''' GET '''
        params = {}
        if symbol: params['symbol'] = symbol
        if count!=0: params['count'] = count
        if filter: params['filter'] = filter
        return self.http_get_request('/api/v1/instrument')          
 
    def instrument_active(self) :
        ''' GET '''
        return self.http_get_request('/api/v1/instrument/active')
    
    def instrument_activeAndIndices(self):
        ''' GET '''
        return self.http_get_request('/api/v1/instrument/activeAndIndices')
   
    def instrument_activeIntervals(self):
        '''GET'''
        return self.http_get_request('/api/v1/instrument/activeIntervals')

    def instrument_compositeIndex(self, symbol, count=0, filter=''):
        ''' GET '''
        params = {}
        params['symbol'] = symbol
        if count!=0: params['count'] = count
        if filter: params['filter'] = filter
        return self.http_get_request('/api/v1/instrument/compositeIndex', params)
    
    def instrument_indices(self):
        ''' GET '''
        return self.http_get_request('/api/v1/instrument/indices')
   
    def insurance(self, symbol='', count=0, filter=''):
        ''' GET '''
        return self.http_get_request('/api/v1/insurance')

    def leaderboard(self, method='notional'):
        ''' GET 
            method : Ranking type. Options: "notional", "ROE"
        '''
        return self.http_get_request('/api/v1/leaderboard', {'method': method})
    
    def liquidation(self, symbol='', count=0, filter=''):
        ''' GET '''
        params = {}
        params['symbol'] = symbol
        if count!=0: params['count'] = count
        if filter: params['filter'] = filter
        return self.http_get_request('/api/v1/liquidation')
    
    def orderBook(self, symbol, depth='20'):
        ''' GET '''
        return self.http_get_request('/api/v1/orderBook/L2', symbol=symbol, depth=depth)

    def quote(self, symbol='', filter='', count=''):
        ''' GET
        '''
        params = {}
        if symbol: params['symbol'] = symbol
        if count>0: params['count'] = count
        if filter: params['filter'] = filter
        return self.http_get_request('/api/v1/quote', params)          

    def schema(self, filter=''):
        ''' GET '''
        params = {}
        if filter: params['filter'] = filter
        return self.http_get_request('/api/v1/schema', params)

    def settlement(self, symbol='', count=0, filter=''):
        ''' GET '''
        params = {}
        params['symbol'] = symbol
        if count>0: params['count'] = count
        if filter: params['filter'] = filter
        return self.http_get_request('/api/v1/settlement')
    
    def stats(self):
        ''' GET '''
        return self.http_get_request('/api/v1/stats')

    def stats_history(self):
        return self.http_get_request('/api/v1/stats/history')

    def stats_historyUSD(self):
        return self.http_get_request('/api/v1/stats/historyUSD')

    def trade(self, symbol='', filter='', count=0):
        params = {}
        if symbol: params['symbol'] = symbol
        if count>0: params['count'] = count
        if filter: params['filter'] = filter
        return self.http_get_request('/api/v1/trade', params)
    
    def trade_bucketed(self, type, symbol='', count=0):
        ''' GET 
            type :  [1m,5m,1h,1d].
        '''
        params = {}
        params['binSize'] = type
        if symbol: params['symbol'] = symbol
        if count > 0 : params['count'] = count
        return self.http_get_request('/api/v1/trade/bucketed', params)

    ####################market data api end################################

    ####################trade  api start################################
    def leaderboard_name(self):
        ''' GET sign '''
        return self.http_get_request_sign('/api/v1/leaderboard/name')

    def execution(self, symbol='', count=0, filter=''):
        ''' GET Sign
            symbol : XBU:monthly|XBU  .daily, weekly, monthly, quarterly, and biquarterly.

        '''
        params = {}
        if symbol: params['symbol'] = symbol
        if count!=0: params['count'] = count
        if filter: params['filter'] = filter
        return self.http_get_request_sign('/api/v1/execution', params)          

    def execution_tradeHistory(self, symbol='', count=0, filter=''):
        ''' GET sign '''
        params = {}
        if symbol: params['symbol'] = symbol
        if count!=0: params['count'] = count
        if filter: params['filter'] = filter
        return self.http_get_request_sign('/api/v1/execution/tradeHistory', params)          

    def notification(self):
        ''' GET '''
        return self.http_get_request_sign('/api/v1/notification');
   
    def order(self, symbol='', count=0, filter=''):
        ''' GET '''
        params = {}
        if symbol: params['symbol'] = symbol
        if count!=0: params['count'] = count
        if filter: params['filter'] = filter
        return self.http_get_request_sign('/api/v1/order', params)

    def place_order(self, symbol, side, price, orderQty, ordType):
        ''' POST sign
            side :  Buy, Sell
            ordType :  Market, Limit, Stop, StopLimit, MarketIfTouched, LimitIfTouched, 
            Double orderQty : 
            Double price:

        '''
        params = {}
        params['symbol'] = symbol
        params['side'] = side
        params['orderQty'] = orderQty
        params['price'] = price
        params['ordType'] = ordType
        return self.http_post_request('/api/v1/order', params)
    
    def cancel_order(self, order_ids) :
        ''' DELETE  cancel orders of orderid'''
        return self.http_delete_request('/api/v1/order', orderID=order_ids)


    def cancel_all(self, symbol='', filter=''):
        ''' DELETE cancel all orders of match condition
            filter : e.g. {"side": "Buy"}.
        '''
        params = {}
        if symbol: params['symbol'] = symbol
        if filter: params['filter'] = filter
        return self.http_delete_request('/api/v1/order/all', params)
   
    def update_order(self, orderid, orderQty=0, price=0):
        ''' PUT '''
        params = {}
        params['orderid'] = orderid
        if orderQty > 0 : params['orderQty'] = orderQty
        if price>0 : params['price'] = price
        return self.http_put_request('/api/v1/order', params)
   
    def order_bulk(self, orders):
        ''' POST 批量下单
            orders : 订单列表 
        '''
        return self.http_post_request('/api/v1/order/bulk', orders=orders)
   
    def update_order_bulk(self, orders):
        ''' PUT 批量修改订单
        '''
        return self.http_put_request('/api/v1/order/bulk', orders=orders)
    
    def order_cancelAllAfter(self, timeout=15):
        ''' POST 订单超时取消时间
        
        '''
        return self.http_post_request('/api/v1/order/cancelAllAfter', timeout=timeout)

    def position(self, filter='', count=0):
        ''' GET sign 获取账户持仓
        '''
        params = {}
        if filter: params['filter'] = filter
        if count > 0 : params['count'] = count
        return self.http_get_request_sign('/api/v1/position', params)
   
    def position_isolate(self, symbol, enabled):
        ''' POST sign 设置保证金吧
            enabled ： True for isolated margin, false for cross margin.
        '''
        return self.http_post_request('/api/v1/position/isolate', symbol=symbol, enabled=enabled)
   
    def position_leverage(self, symbol, leverage):
        ''' POST sign 设置杠杆
            leverage : between 0.01 and 100 to enable isolated margin with a fixed leverage. Send 0 to enable cross margin.
        '''
        return self.http_post_request('/api/v1/position/leverage', symbol=symbol, leverage=leverage)
    
    def position_riskLimit(self, symbol, riskLimit):
        ''' POST sign 
            double riskLimi 
        '''
        return self.http_post_request('/api/v1/position/riskLimit', symbol=symbol, riskLimit=riskLimit)

    def position_transferMargin(self, symbol, amount):
        ''' POST sign
            double amount
        '''
        return self.http_post_request('/api/v1/position/transferMargin', symbol=symbol, amount=amount)
    
    def user(self):
        return self.http_get_request_sign('/api/v1/user')

    def user_commission(self):
        return self.http_get_request_sign('/api/v1/user/commission')

    def user_margin(self, symbol):
        return self.http_get_request_sign('/api/v1/user/margin', symbol=symbol)

    ####################trade  api end################################
    

import logging, sys

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')

    apikey    = 'xShYIkq6c964NqKMH7cP1f3j'
    apisecret = 'ehWvEyF80IkmkwTJbB5-DiLSlJP8k6WWJiEXyhIdmYaskrBR'
    url       = "https://www.bitmex.com"
        
    #generate_signature(None, 'ehWvEyF80IkmkwTJbB5-DiLSlJP8k6WWJiEXyhIdmYaskrBR', 'POST', '/api/v1/order', '1524203893', '{"ordType":"Limit","orderQty":1,"price":2000,"side":"Buy","symbol":"XBTUSD"}')

    http= BitmexHttp(url, apikey, apisecret)
   
    #print(http.execution())
    #print(http.execution_tradeHistory('XBTUSD'))
    #print(http.leaderboard_name())
    #print(http.notification())
    #print(http.order()) 


    #print(http.position())
    #print(http.user()) 
    #print(http.user_commission())
    #print(http.user_margin('XBTUSD'))
    print(http.place_order('XBTUSD', 'Buy', 1, 9000, 'Limit'))
    #必须双引号转义
    #order = http.order('', 0, '{"ordStatus":"New"}')
    #print(order)
    #print(http.cancel_order(order[0]['orderID']))
    #print(http.cancel_all())

    #print(http.announcement())
    #print(http.announcement_urgent())
    #print(http.funding()) 
    #print(http.instrument())
    #print(http.instrument_active())
    #print(http.instrument_activeAndIndices())
    #print(http.instrument_activeIntervals())
    #print(http.instrument_compositeIndex('XBTUSD'))
    #print(http.instrument_indices())
    #print(http.insurance())
    #print(http.leaderboard())
    #print(http.liquidation())
    #print(http.quote())
    #print(http.settlement())
    #print(http.stats())
    #print(http.stats_history())
    #print(http.stats_historyUSD())
    #print(http.schema())
    #print(http.orderBook('XBTUSD'))   
    #print(http.trade())    
    #print(http.trade_bucketed('1m'))    
   



