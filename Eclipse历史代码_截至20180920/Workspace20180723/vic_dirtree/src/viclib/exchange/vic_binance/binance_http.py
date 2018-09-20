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

class BinaHttp(HttpClient):
    def __init__(self, url, apikey, apisecret):
        super(BinaHttp, self).__init__(url, apikey, apisecret)
        #WEBSITE_URL = 'https://www.binance.com'            

        self.getheader  = {
                "Content-type": "application/x-www-form-urlencoded",
                'X-MBX-APIKEY' : apikey,
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'    
            } 
        self.postheader = {
                "Accept": "application/json",
                'Content-Type': 'application/json',
                'X-MBX-APIKEY' : apikey,
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'
            }
  
    def __sign(self, data):
        #data = sorted(data.items(), key=lambda d: d[0], reverse=True)
        data = urllib.urlencode(data)
        sign = hmac.new(self.getApiSecret().encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()
        return sign
    
    def http_get_request(self, method, query=None, **args):
        params = {}
        params.update(**args)
        if query is not None: params.update(query)
        
        if(params.get('sign')):
            del params['sign']
            params['signature'] = self.__sign(params)
        
        url = '{url}{method}?{params}'.format(url=self.getUrl(), method=method, params=urllib.urlencode(params))
        return self.http_request(url, 'GET', None, self.getheader)
    
    def http_post_request(self, method, query=None, **args):
        params = {}
        params.update(**args)
        if query is not None: params.update(query)
        #params['signature'] = self.__sign(params)
        
        if(params.get('sign')):
            del params['sign']
            params['signature'] = self.__sign(params)

        url = '{url}{method}'.format(url=self.getUrl(), method=method)
        return self.http_request(url, 'POST', params, self.postheader)
    

    def http_put_request(self, method, query=None, **args):
        params = {}
        params.update(**args)
        if query is not None: params.update(query)
        url = '{url}{method}?{params}'.format(url=self.getUrl(), method=method, params=urllib.urlencode(params))
        return self.http_request(url, 'PUT', None, self.postheader)
    
    def http_delete_request(self, method, query=None, **args):
        params = {}
        params.update(**args)
        if query is not None: params.update(query)
        
        if(params.get('sign')):
            del params['sign']
            params['signature'] = self.__sign(params)
        
        logging.info(params)

        url = '{url}{method}?{params}'.format(url=self.getUrl(), method=method, params=urllib.urlencode(params))
        return self.http_request(url, 'DELETE', None, self.postheader)
    

    ######################################public api################################################
    def exchangeInfo(self):
        ''' GET (....) Return rate limits and list of symbols
            return : {
                "timezone": "UTC",
                "serverTime": 1508631584636,
                "rateLimits": [
                    {
                        "rateLimitType": "REQUESTS",
                        "interval": "MINUTE",
                        "limit": 1200
                    },
                    {
                        "rateLimitType": "ORDERS",
                        "interval": "SECOND",
                        "limit": 10
                    },
                    {
                        "rateLimitType": "ORDERS",
                        "interval": "DAY",
                        "limit": 100000
                    }
                ],
                "exchangeFilters": [],
                "symbols": [
                    {
                        "symbol": "ETHBTC",
                        "status": "TRADING",
                        "baseAsset": "ETH",
                        "baseAssetPrecision": 8,
                        "quoteAsset": "BTC",
                        "quotePrecision": 8,
                        "orderTypes": ["LIMIT", "MARKET"],
                        "icebergAllowed": false,
                        "filters": [
                            {
                                "filterType": "PRICE_FILTER",
                                "minPrice": "0.00000100",
                                "maxPrice": "100000.00000000",
                                "tickSize": "0.00000100"
                            }, {
                                "filterType": "LOT_SIZE",
                                "minQty": "0.00100000",
                                "maxQty": "100000.00000000",
                                "stepSize": "0.00100000"
                            }, {
                                "filterType": "MIN_NOTIONAL",
                                "minNotional": "0.00100000"
                            }
                        ]
                    }
                ]
            }

   
        '''
        return self.http_get_request('/api/v1/exchangeInfo')
    
    def symbol(self, symbol):
        ''' see function exchangeInfo'''
        info = self.exchangeInfo()
        for item in info['symbols']:
            if item['symbols'] == symbol.upper():
                return item
        return None

    def timestamp(self):
        ''' get the current server time. 
            return : {
                "serverTime": 1499827319559 
            }
        '''
        return self.http_get_request('/api/v1/time')
    ######################################public api################################################
    
   
    ################################### market data ###############################################################  
    def ticker_allprice(self):
        ''' Latest price for all symbols
            return : [
                {
                    "symbol": "LTCBTC", 
                    "price": "4.00000200" 
                },
                ......
            ]
        '''
        return self.http_get_request('/api/v1/ticker/allPrices')
    
    def orderbook(self):
        ''' bid1 and ask1 on the order book for all symbols
            return : [
                {
                    "symbol": "LTCBTC",       
                    "bidPrice": "4.00000000", 
                    "bidQty": "431.00000000", 
                    "askPrice": "4.00000200", 
                    "askQty": "9.00000000"    
                },
                {
                    "symbol": "ETHBTC",           
                    "bidPrice": "0.07946700",     
                    "bidQty": "9.00000000",       
                    "askPrice": "100000.00000000",
                    "askQty": "1000.00000000"     
                }
            ]
        '''
        return self.http_get_request('/api/v1/ticker/allBookTickers')
   
    def depth(self, symbol, limit):
        ''' the Order Book for the market 
            int limit :   Default 100; max 1000. Valid limits:[5, 10, 20, 50, 100, 500, 1000]
        '''
        return self.http_get_request('/api/v1/depth', symbol=symbol, limit=limit)

    def trades(self, symbol, limit):
        ''' recent trades (up to last 500).
            limit : Default 500; max 500.
            return : [
                {
                    "id": 28457,           
                    "price": "4.00000100", 
                    "qty": "12.00000000",  
                    "time": 1499865549590, 
                    "isbuyerMaker": true,  
                    "isBestMatch": true    
                },
                ......
            ] 
        '''
        return self.http_get_request('/api/v1/trades', symbol=symbol, limit=limit)

    def historicalTrades(self, symbol, limit=10, fromId=None):
        ''' Get older trades.
            int limit : Default 500; max 500
            long fromId : TradeId to fetch from. Default gets most recent trades.
            return : [
                "id": 28457,             
                "price": "4.00000100",   
                "qty": "12.00000000",    
                "time": 1499865549590,   
                "isbuyerMaker": true,    
                "isBestMatch": true      
            ]
        '''
        params = {}
        if(fromId) :  params['fromId'] = fromId
        return self.http_get_request('/api/v1/historicalTrades', params, symbol=symbol, limit=limit)

    def klines(self, symbol, interval, limit=500, startTime=None, endTime=None):
        ''' Kline/candlestick bars for a symbol. Klines are uniquely identified by their open time
            interval : 1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 1w 1M
            int limit : Default 500; max 500.  
            long startTime : 
            long endTime : 
            return : [
                [
                    1499040000000,      # Open time                     
                    "0.01634790",       # Open                          
                    "0.80000000",       # High                          
                    "0.01575800",       # Low                           
                    "0.01577100",       # Close                         
                    "148976.11427815",  # Volume                        
                    1499644799999,      # Close time                    
                    "2434.19055334",    # Quote asset volume            
                    308,                # Number of trades              
                    "1756.87402397",    # Taker buy base asset volume   
                    "28.46694368",      # Taker buy quote asset volume  
                    "17928899.62484339" # Can be ignored                
                ]
                ......
            ]
        '''
        params = {}
        if(startTime) : params['startTime'] = startTime
        if(endTime)   : params['endTime']   = endTime
        return self.http_get_request('/api/v1/klines', params, symbol=symbol, interval=interval, limit=limit)

    def ticker(self, symbol=None):
        ''' 
            symbol : None  will return all ticker of symbols  
            return : {} or [{}, {}.....]
        '''
        params = {}
        if(symbol) : params['symbol'] = symbol
        return self.http_get_request('/api/v1/ticker/24hr', params)

    
    ################################### market data ###############################################################  

    
    ################################### trade api  ###############################################################  
   
    def account(self):
        ''' GET (HMAC SHA256) Get current account information.
            return : {
            } 
        '''
        return self.http_get_request('/api/v3/account', sign=True, timestamp=int(time.time() * 1000))

    def tradelist(self, symbol):
        ''' GET (HMAC SHA256) Get trades for a specific account and symbol.
            return : [{}]
        '''
        return self.http_get_request('/api/v3/myTrades', sign=True, symbol=symbol, timestamp=int(time.time() * 1000))
    
    def place_order(self, symbol, price, quantity,  type, side):
        ''' POST  (HMAC SHA256)  Send in a new order. 
            type : LIMIT / MARKET 
            side : BUY / SELL
            return : {
                "symbol": "BTCUSDT",
                "orderId": 28,
                "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
                "transactTime": 1507725176595
            }
        '''
        params = {"timeInForce" : 'GTC',
                  "timestamp"   : int(time.time() * 1000),
                  "quantity"    : quantity,
                  "symbol"      : symbol,
                  "type"        : type,
                  "side"        : side,
                  'newOrderRespType' : 'ACK',  #ACK, RESULT, or FULL; default: RESULT.
                  'price'       : price}
        return self.http_post_request('/api/v3/order', params, sign=True)
    
    def place_order_test(self, symbol, quantity, price,  type, side):
        '''for test. Creates and validates a new order but does not send it into the matching engine.
        
        '''
        params = {"timeInForce" : 'GTC',
                  "timestamp"   : int(time.time() * 1000),
                  "quantity"    : quantity,
                  "symbol"      : symbol,
                  "type"        : type,
                  "side"        : side,
                  'newOrderRespType' : 'ACK',  #ACK, RESULT, or FULL; default: RESULT.
                  'price'       : price}
        return self.http_post_request('/api/v3/order/test', params, sign=True)
    
    def order(self, symbol, orderId=None):
        ''' Check an order's status.
        '''
        params = {"timestamp"   : int(time.time() * 1000),
                  "symbol"      : symbol}
        if orderId : params['orderId'] = orderId
        return self.http_post_request('/api/v3/order', params, sign=True)

    def cancel_order(self, symbol, orderId):
        ''' DELETE (HMAC SHA256) 申请撤销某个符号的订单 或者订单id的
            return : {
                "symbol": "LTCBTC",
                "origClientOrderId": "myOrder1",
                "orderId": 1,
                "clientOrderId": "cancelMyOrder1"
            }
        '''
        params = {"timestamp"   : int(time.time() * 1000),
                  "symbol"      : symbol,
                  'orderId'     : orderId}
        return self.http_delete_request('/api/v3/order', params, sign=True)
    
    def openorders(self):
        ''' Get all open orders
            return : [
                {
                    "symbol": "LTCBTC",
                    "orderId": 1,
                    "clientOrderId": "myOrder1",
                    "price": "0.1",
                    "origQty": "1.0",
                    "executedQty": "0.0",
                    "status": "NEW",
                    "timeInForce": "GTC",
                    "type": "LIMIT",
                    "side": "BUY",
                    "stopPrice": "0.0",
                    "icebergQty": "0.0",
                    "time": 1499827319559,
                    "isWorking": trueO
                }
                ......
            ]
        '''
        return self.http_get_request('/api/v3/openOrders', sign=True, timestamp=int(time.time() * 1000))
    
    def allorders(self, symbol):
        '''GET  (HMAC SHA256) Get all account orders; active, canceled, or filled.
        '''
        return self.http_get_request('/api/v3/allOrders', sign=True, symbol=symbol, timestamp=int(time.time() * 1000))
   
    
    
    ################################### trade api  ###############################################################  

    ###################################User data stream##############################################################
    def stream_get_listen_key(self):
        '''POST  Specifics on how user data streams work is in another document.
            return : {
                "listenKey": "pqia91ma19a5s61cv6a81va65sdf19v8a65a1a5s61cv6a81va65sdf19v8a65a1"
            }
        
        '''
        return self.http_post_request('/api/v1/userDataStream')

    def stream_keepalive(self, listenKey):
        '''PUT  Keepalive a user data stream  It's recommended to send a ping about every 30 minutes.
            listenKey : 
        '''
        return self.http_put_request('/api/v1/userDataStream', listenKey=listenKey)

    def stream_close(self, listenKey):
        ''' DELETE  Keepalive a user data stream  It's recommended to send a ping about every 30 minutes.
            listenKey : 
        '''
        return self.http_delete_request('/api/v1/userDataStream', listenKey=listenKey)

    
    ###################################User data stream##############################################################
    
    ################################### account api  ###############################################################  
    #def withdraw(self, address, amount, currency, fee=0):
    #    ''' POST 申请提现虚拟币
    #        address : 提现地址
    #        currency : 资产类型 
    #        fee : 转账手续费
    #        return : {
    #            "status": "ok",
    #            "data": 700     #提现ID
    #        }
    #    '''
    #    url = '/v1/dw/withdraw/api/create'
    #    return self.http_post_request(url, address=address, amount=amount, currency=currency, fee=fee)
    #
    ## 申请取消提现虚拟币
    #def cancel_withdraw(self, withdraw_id):
    #    ''' POST 申请取消提现虚拟币
    #        return : {
    #            "status": "ok",
    #            "data": 700     #提现ID
    #        }
    #    '''
    #    url = '/v1/dw/withdraw-virtual/{0}/cancel'.format(withdraw_id)
    #    return self.http_post_request(url)
   
    #def query_withdraw(self, currency, type, size=10000000):
    #    ''' GET  查询虚拟币充提记录 默认查询所有的
    #        type : 'deposit' or 'withdraw'
    #        return : {
    #            "status": "ok",
    #            data : [
    #                {
    #                    "id": 1171,
    #                    "type": "deposit",  #deposit' 'withdraw'
    #                    "currency": "xrp",
    #                    "tx-hash": "ed03094b84eafbe4bc16e7ef766ee959885ee5bcb265872baaa9c64e1cf86c2b",
    #                    "amount": 7.457467,
    #                    "address": "rae93V8d2mdoUQHwBDBdM4NHCMehRJAsbm",
    #                    "address-tag": "100040",
    #                    "fee": 0,
    #                    "created-at": 1510912472199,
    #                    "updated-at": 1511145876575
    #                    "state": "safe",
    #                },
    #                ......
    #            ]
    #        }
    #        state : 
    #        提现状态 : submitted, reexamine, canceled, pass,reject,pre-transfer,wallet-transfer,wallet-reject,confirmed,confirm-error,repealed
    #        充值状态 : unknown, confirming, confirmed, safe, orphan
    #    '''
    #    return self.http_get_request_sign('/v1/query/deposit-withdraw', {'from':0}, currency=currency, type=type, size=size)
    ################################### account api  ###############################################################  

if __name__ == "__main__":
    url = "https://api.binance.com"
    apiKey   = "i5gVlrajCWSpQulsTbYZUC1Prp2TvxPxF16jjYnHSdo13LfFAi0fUEAjd0Vu7DME"
    apiSecret= "OYzRJA6B2gxAkETIg1eDGJWZsf1unz5Rrl1aVewelkB3iNLUsArYWedOtonBNeTe"

    apiKey = 'zF2whVxfO3C0kclQIdqf2RkHrf22s8FLeqYUPQzU0913XNvThtKqMNnHecqkPFZh'
    apiSecret='U3SZHilMLyWUufCtxwxn2C9hUWOViWGoavTTYV2OWkrPTb5ww8MHP5PFmVYQlqdx'
    #key:  zF2whVxfO3C0kclQIdqf2RkHrf22s8FLeqYUPQzU0913XNvThtKqMNnHecqkPFZh
    #secret: U3SZHilMLyWUufCtxwxn2C9hUWOViWGoavTTYV2OWkrPTb5ww8MHP5PFmVYQlqdx

    http = BinaHttp(url, apiKey, apiSecret)
    #rtn = http.place_order("LTCUSDT", 200, 0.1,  "LIMIT", "SELL")
    #print(rtn)
    #print(http.exchangeInfo())
    #print(http.ticker_allprice())
    #print(http.orderbook())
    
    #print(http.trades('ETHBTC', 5))
    #print(http.depth('ETHBTC', 10))
    #print(http.klines('ETHBTC', '1m', 10))
    #print(http.ticker('ETHBTC'))
    #print(http.historicalTrades('ETHBTC'))
    
    
    print(http.account())
    print(http.tradelist('BTCUSDT'))
    #print(http.allorders('BTCUSDT'))
    
    #oo = http.openorders()
    #oa = http.account()
    #print(oo)
    #print(oa)
    #print(http.cancel_order('LTCUSDT', oo[0]['orderId']))
    
    #listenkey = http.stream_get_listen_key()
    #print(listenkey)
    #print(http.stream_keepalive(listenkey['listenKey']))
    #print(http.stream_close(listenkey['listenKey']))







