#!/usr/bin/env python
#coding=utf-8

import re
import os
import time
import logging

from viclib.exchange.vic_okex.okex_http import OkexHttp
from viclib.exchange.vic_okex.okexft_http import OkexftHttp

from viclib.common.conf import VConf

class OkexService(OkexHttp, OkexftHttp):
    ''' OkexService 
        1. 法币账户
        2. 币币账户
        3. 合约账户
        4. margin账户
        只支持币币账户和合约账户
    '''
    def __init__(self, account='Kevin.wang@126.com'):
        ''' okex okexft的http地址一致 '''
        self.conf = VConf()
        url = self.conf.get_http('okex') 
        apikey = self.conf.get_apikey('okex', account)
        apisecret = self.conf.get_secret('okex', account)
        self.contract_types = ['this_week', 'next_week', 'quarter']
        super(OkexService, self).__init__(url, apikey, apisecret)
    
    def ft_balances_list(self):
        ''' 期货权益 '''
        userinfo =  self.future_userinfo()['info']
        balances = {}
        for k in userinfo:
            if userinfo[k]['account_rights'] > 0.0001:
                balances[k.upper()] = userinfo[k]
        return balances

    def bb_balances_list(self):
        ''' 币币权益 '''
        userinfo = self.userinfo()['info']['funds']
        free    = userinfo['free']
        freezed = userinfo['freezed']
        keys = set(free.keys() + freezed.keys())
        balances = {}
        for key in keys:
            if( free.get(key) == None ) : free[key] = 0.0
            if( freezed.get(key) == None ) : freezed[key] = 0.0
            if(float(free[key]) < 0.000001 and float(freezed[key]) < 0.000001) : continue
            balances[key.upper()] = {'currency': key.upper(), 'free': float(free[key]), 'freezed': float(freezed[key])}
        return balances 
    
    def balances_list(self):
        balances = self.bb_balances_list()
        for b in balances : 
            balances[b]['future'] = 0
        ft = self.ft_balances_list()
        for c in ft:
            if not balances.get(c):  
                balances[c] = {}
                balances[c]['free'] = 0
                balances[c]['freezed'] = 0
            balances[c]['future'] = ft[c]['account_rights']
        return balances

    def c1toc2(self, c1, c2):
        c1 = c1.lower()
        c2 = c2.lower()
        if c1 == c2: return 1
        ticker = self.ticker(c1+'_'+c2)
        if ticker.get('ticker'):
            return float(ticker['ticker']['last'])
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
        _sum = 0.0
        balances = self.balances_list()
        for currency in balances:
            balance = balances[currency]
            bvol  = float(balance['free']) + float(balance['freezed']) + float(balance['future'])
            _sum +=  bvol * self.tousdt(currency)
        return _sum


    ################################加减仓相关######################################################
    def okex_cancel_order(self, symbols=''):
        ''' okex币币 撤掉挂单'''
        channels = self.conf.get_channels('OKEX')
        channels = [i.replace('OKEX--', '').reaplce('--', '_').lower() for i in channels]
        for cc in channels:
            if symbols  and symbols == cc:
                continue
            orders = self.orderinfo(cc)
            for order in orders:
                self.cancelorder(order['symbol'], order['order_id'])
            time.sleep(0.5)
        return True

   
    def okex_future_cancel(self, symbol='', contract_type=''):
        ''' okex合约 撤单 '''
        #查询持仓权益  根据持仓权益符号查询订单id 然后撤单
        channels = self.conf.get_channels('OKEXFT')
        channels = [i.replace('OKEXFT--', '').reaplce('--', '_').lower() for i in channels]
        #查询orderid
        for cc in channels:
            for contract_type in contract_types:
                orders = self.future_order_info(cc, contract_type, -1)
                for order in orders:
                    self.future_cancel(order['symbol'], contract_type, order['order_id'])
                    time.sleep(0.1)
        return True

    def okex_future_closeposition(self):
        ''' 期货平仓 '''
        channels = self.conf.get_channels('OKEXFT')
        channels = [i.replace('OKEXFT--', '').reaplce('--', '_').lower() for i in channels]
        for cc in channels:
            for contract_type in contract_types:
                positions = self.future_position(cc, contract_type)
                for position in positions:
                    if position['buy_available'] > 0:
                        self.future_trade(cc, contract_type, 3, 0, position['buy_available'], 1)
                    if position['sell_available'] > 0:
                        self.future_trade(cc, contract_type, 4, 0, position['buy_available'], 1)
                    time.sleep(0.2)
        return True


    def ft_account_2bb(self, currency='', amount=0):
        ''' currency转换到bb账户 或者 所有资金转换到币币账户'''
        if not amount:
            balances = self.ft_balances_list()
            balances = [(b, b['account_rights']) for b in balances]
            if currency:
                balances = filter(lambda x:x[0]==currency, balances)
        else:
            balances = [(currency, amount)]
        
        for b in balances:
            self.funds_transfer(b[0], b[1], 3, 1)

    def balance_btc(self, currency, quantity, side='sell-market', price=0):            
        ''' 货币转化为btc '''
        if currency == 'BTC':  return
        symbol = currency.upper() + 'BTC'
        self.addorder(symbol, side, price, quantity)

    def balance_usdt(self, currency, quantity, side='sell-market', price=0):            
        ''' 货币转化为usdt '''
        if currency == 'USDT':  return
        symbol = currency.upper() + 'USDT'
        self.addorder(symbol, side, price, quantity)


    def balance_all_tousdt(self):
        ''' 
            所有的货币不能转化为usdt的线转化为btc  转化为usdt
            1. 期货撤单
            2. 期货平仓
            3. 期货账户转到币币账户
            4. 币币取消订单
            5. 将比比所有的资金转化为usdt
        '''
        #self.okex_future_cancel()
        #
        #self.okex_future_closeposition()

        #self.ft_account_2bb()

        #self.okex_cancel_order()

        #self.okex_balance_usdt()
 
        channels = self.conf.get_channels('OKEX')
        channels = [i.replace('OKEX--', '').reaplce('--', '') for i in channels]
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









