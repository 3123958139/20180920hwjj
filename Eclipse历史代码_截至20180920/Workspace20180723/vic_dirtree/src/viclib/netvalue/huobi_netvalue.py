#!/usr/bin/env python
#coding=utf-8

import re
import os
import time
import logging

from viclib.exchange.vic_huobi.huobi_http import HuobiHttp

from viclib.common.conf import VConf

class HuobiService(HuobiHttp):
    ''' HuobiService
        1. oct账户
        2. margin账户
        3. spot账户 币币
        不支持oct  margin账户
    '''
    def __init__(self, account='Kevin.wang@126.com'):
        conf = VConf()
        url = conf.get_http('huobi') 
        apikey = conf.get_apikey('huobi', account)
        apisecret = conf.get_secret('huobi', account)
        self.__uid = ''
        super(HuobiService, self).__init__(url, apikey, apisecret)

    def balances_list(self):
        ''' 权益 '''
        account = filter(lambda x:x['type']=='spot', self.accounts()['data'])[0]
        balances = self.balance(account['id'])
        if not balances or balances.get('status')!='ok':
            raise Exception(balances)

        balance = {}
        for item in balances['data']['list']:
            if(float(item['balance']) < 0.00000001) : continue
            item['currency'] = item['currency'].upper()
            key = item['currency']
            if(not balance.get(key)) :  
                balance[key] = {'currency': item['currency'], 'free': 0.0, 'freezed':0.0}
            if(item['type'] == 'trade') :  balance[key]['free'] = float(item['balance'])
            if(item['type'] == 'frozen') : balance[key]['freezed'] = float(item['balance'])
        return balance

    def c1toc2(self, c1, c2):
        c1 = c1.lower()
        c2 = c2.lower()
        if c1 == c2: return 1
        ticker = self.detail_merged(c1+c2)
        if ticker.get('tick'):
            return float(ticker['tick']['close'])
        return None

    def tousdt(self, currency):
        usdt = self.c1toc2(currency, 'usdt')
        if usdt : return usdt        
        btc  = self.c1toc2(currency, 'btc') 
        usdt = self.c1toc2('btc', 'usdt')   
        if btc and usdt:
            return btc*usdt              
        return 0

    def sum_usdt(self):
        ''' 火币所有币种转usdt的总数 '''
        _sum  = 0.0
        balances = self.balances_list()
        for currency in balances:
            balance = balances[currency]
            bvol  = float(balance['free']) + float(balance['freezed'])
            _sum +=  bvol * self.tousdt(currency)
        return _sum


    ################################加减仓相关######################################################
    def cancel_open_orders(self, symbol=''):
        ''' 火币撤单 如果订单数量大于50需要在调试 '''
        orders = self.orders(states='pre-submitted,submitted,partial-filled')['data']
        if symbol : orders = [order for order in orders if order['symbol']==symbol] 

        def cancel():
            order_id_list = [order['id'] for order in orders]
            order_ids   = {'order-id': order_id_list}
            self.cancel_order(order_ids)
            self.cancel_open_orders(symbol)
        
        if len(orders) > 0:
            cancel()    
    
    def balance_btc(self, currency, quantity, side='sell-market', price=0):
        if currency == 'BTC':  return                        
        symbol = currency.upper() + 'BTC'                    
        self.place_order(self.__uid, symbol, price, quantity,  side)   
    
    def balance_usdt(self, currency, quantity, side='sell-market', price=0):
        if currency == 'USDT':  return                        
        symbol = currency.upper() + 'USDT'                    
        self.place_order(self.__uid, symbol, price, quantity,  side)   

    def balance_all_tousdt(self, currency=''):
        ''' 持仓转化为usdt 如果有挂单需要先全部撤单
            如果不能直接转化为usdt通过中间btc做转换
            currency : 'BTC'  需要转换为usdt的货币 如果为空表示所有持仓
            return : ['BTC', ...] 失败的合约
        '''
        #self.cancel_open_orders()

        self.__uid = filter(lambda x:x['type']=='spot', self.accounts()['data'])[0]['id']
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



if __name__ == "__main__":

    url        = "https://api.huobipro.com"
    apiKey     = "8d22783f-7cb9e4c6-40ccd735-fa087"
    apiSecret  = "76b99517-fa66c3f7-eb9282d8-01c48"

    hs = HuobiService(url, apiKey, apiSecret)

    sum_usdt = hs.sum_usdt()
