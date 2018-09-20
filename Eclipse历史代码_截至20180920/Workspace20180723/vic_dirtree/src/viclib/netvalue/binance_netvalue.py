#!/usr/bin/env python
#coding=utf-8

import re
import os
import time
import logging

from viclib.exchange.vic_binance.binance_http import BinaHttp


from viclib.common.conf import VConf

# 提供给净值计算使用  风控使用
# 提供给交易使用

class BinanService(BinaHttp):
    '''BinanService'''
    def __init__(self, account='Kevin.wang@126.com'):
        conf = VConf()
        url = conf.get_http('binance') 
        apikey = conf.get_apikey('binance', account)
        apisecret = conf.get_secret('binance', account)
        super(BinanService, self).__init__(url, apikey, apisecret)

    def c1toc2(self, c1, c2):
        ''' 兑换btc价格 '''
        c1 = c1.upper()
        c2 = c2.upper()
        if c1 == c2: return 1
        ticker = self.ticker(c1+c2)
        if ticker.get('lastPrice'):
            return  float(ticker['lastPrice'])
        return None

    def tousdt(self, currency):
        ''' 转换usdt '''
        usdt = self.c1toc2(currency, 'usdt')
        if usdt : return usdt
        btc  = self.c1toc2(currency, 'btc') 
        usdt = self.c1toc2('BTC', 'usdt')
        if btc and usdt:
            return btc*usdt
        return 0

    def balances_list(self):
        ''' 持仓列表 '''
        acc =  self.account()
        infos = acc.get('balances')
        if not infos : 
            raise Exception(acc)
        balances = {}
        for b in infos:
            if(float(b['free'])+float(b['locked']) < 0.000001):
                continue
            balances[b['asset'].upper()] = {
                    'currency' : b['asset'].upper(),
                    'free'     : float(b['free']),
                    'freezed'  : float(b['locked'])
                }
        return balances

    def sum_usdt(self):
        ''' 估值币安所有持仓币种转usdt的总数 '''
        balances = self.balances_list()
        _sum = 0.0
        for currency in balances:
            balance = balances[currency]
            bvol = float(balance['freezed']) + float(balance['free'])  
            currency  = balance['currency']
            _sum +=  bvol * self.tousdt(currency)
        return _sum
    
    ################################加减仓相关######################################################
    #self.place_order(symbol, quantity, price, 'MARKET', 'SELL')
    
    def cancel_open_orders(self, symbol=''):
        ''' 撤销所有的挂单
            symbol : 'LTCBTC'  空表示撤销所有 
            return ['LTCBTC',...]  返回失败的symbol
        '''
        orders = self.openorders()
        if symbol : orders = [order for order in orders if order['symbol']==symbol]
       
        def cancel():
            for order in orders:
                self.cancel_order(order['symbol'], order['orderId'])
            self.cancel_open_orders(symbol)

        if len(orders) > 0:
            cancel()

    def balance_btc(self, currency, quantity, side='SELL'):
        ''' 其他货币<--->btc 
            side : SELL 卖出其他货币  用BTCBUY买入其他货币
        '''
        if currency == 'BTC':  return
        symbol = currency.upper() + 'BTC'
        self.place_order(symbol, quantity, 'MARKET', side)

    def balance_usdt(self, currency, quantity, side='SELL'):
        ''' 其他货币转换为btc'''
        if currency == 'USDT':  return
        symbol = currency.upper() + 'USDT'
        self.place_order(symbol, quantity, 'MARKET', side)


    def balance_all_tousdt(self, currency=''):
        ''' 持仓转化为usdt 如果有挂单需要先全部撤单
            如果不能直接转化为usdt通过中间btc做转换
            currency : 'BTC'  需要转换为usdt的货币 如果为空表示所有持仓
            return : ['BTC', ...] 失败的合约
        '''
        #self.cancel_open_orders()

        tickers = self.http.ticker()
        symbols = [t['symbol'] for t in tickers]
        def tousdt():
            balances_list = self.balances_list()
            for b in balances_list:
                currency  = b['asset'].upper()
                if (currency and currency!=currency) or currency=='USDT':
                    continue
                free = float(b['free'])
                if free < 0.0001 : continue
               
                if currency+'USDT' not in symbols:
                    self.balance_btc(currency, free)
                else: 
                    self.balance_usdt(currency, free)
        tousdt() 
        tousdt() 










