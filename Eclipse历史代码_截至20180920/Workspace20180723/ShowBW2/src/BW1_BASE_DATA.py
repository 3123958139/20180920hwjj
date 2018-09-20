#!/usr/bin/env python
# coding=utf-8

import json
from viclib.common.conf import VConf
from viclib.exchange.vic_binance.binance_http import BinaHttp
from viclib.exchange.vic_huobi.huobi_http import HuobiHttp
from viclib.exchange.vic_okex.okex_http import OkexHttp
from viclib.exchange.vic_okex.okexft_http import OkexftHttp
import pandas as pd
import datetime as dt
from sqlalchemy import create_engine


def getNowDateTime():
    '''获取本地时间
    '''
    now = dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    return now


ts = getNowDateTime()

def getBtcUsdt():
    '''获取btc的usdt报价
    '''
    conf = VConf()
    account = '13651401725'
    url = conf.get_http('okex')
    apikey = conf.get_apikey('okex', account)
    apisecret = conf.get_secret('okex', account)    
    okexhttp = OkexHttp(url, apikey, apisecret)
    return float(okexhttp.ticker('btc_usdt')['ticker']['last'])


class ExchangeOkex(OkexHttp, OkexftHttp):
    '''获取OKEX账户的持仓和价格
    bb0: 币币权益部分
    ft1: 合约权益部分
    ft2: 合约持仓部分
    '''

    def __init__(self, account='13651401725'):
        '''只接受单账户的传入，多账户下需外部进行遍历
        '''
        self.conf = VConf()
        url = self.conf.get_http('okex')
        apikey = self.conf.get_apikey('okex', account)
        apisecret = self.conf.get_secret('okex', account)
        super(ExchangeOkex, self).__init__(url, apikey, apisecret)
        self.exch_account = account
        self.contract_types = ['this_week', 'next_week', 'quarter']
        self.stat_okex = {}

    def bb0(self):
        '''获取OKEX的币币权益
        没有币种不做
        持仓量低不做
        权益数低不做
        '''
        userinfo = self.userinfo()['info']['funds']
        if not userinfo:
            return
        free = userinfo['free']
        freezed = userinfo['freezed']
        currency = set(free.keys() + freezed.keys())
        balances = {}
        for cur in currency:
            holding = 0.0
            price = 0.0
            try:
                if(free.get(cur) == None):
                    free[cur] = 0.0
                if(freezed.get(cur) == None):
                    freezed[cur] = 0.0
                if(float(free[cur]) < 0.000001 and float(freezed[cur]) < 0.000001):
                    continue
                holding = float(free[cur]) + float(freezed[cur])
                if cur == 'usdt':
                    price = 1.0
                elif self.ticker(cur.lower() + '_usdt'):
                    price = float(self.ticker(cur.lower() + '_usdt')['ticker']['last'])
                if holding * price < 1:
                    continue
                balances[cur.upper()] = {
                    'ts': ts,
                    'holding': holding,
                    'price': price,
                    'account': self.exch_account,
                }
            except:
                continue
        self.stat_okex['bb0'] = balances
        return balances

    def ft1(self):
        '''获取OKEX的合约权益
        '''
        userinfo = self.future_userinfo()['info']
        if not userinfo:
            return
        currency = userinfo.keys()
        balances = {}
        for cur in currency:
            holding = 0.0
            price = 0.0
            if userinfo[cur]['account_rights'] > 0.0001:
                try:
                    holding = userinfo[cur]['account_rights']
                    if cur == 'usdt':
                        price = 1.0
                    elif self.ticker(cur.lower() + '_usdt'):
                        price = float(self.ticker(cur.lower() + '_usdt')['ticker']['last'])
                    if holding * price < 1:
                        continue
                    balances[cur.upper()] = {
                        'ts': ts,
                        'holding': holding,
                        'price': price,
                        'account': self.exch_account,
                    }
                except:
                    continue
        self.stat_okex['ft1'] = balances
        return balances

    def ft2(self):
        '''获取OKEX的合约持仓
        '''
        userinfo = self.future_userinfo()['info']
        if not userinfo:
            return
        currency = userinfo.keys()
        balances = {}
        for cur in currency:
            cur = cur.lower() + '_usd'
            for con in self.contract_types:
                holding = 0.0
                price = 0.0
                try:
                    if len(self.future_position(cur, con)['holding']) > 0:
                        holding = float(self.future_position(cur, con)['holding'][0]['buy_amount']) - float(self.future_position(cur, con)['holding'][0]['sell_amount'])
                        if self.future_ticker(cur, con):
                            price = float(self.future_ticker(cur, con)['ticker']['last'])
                        if cur == 'btc_usd':
                            holding = holding * 100 / price
                        else:
                            holding = holding * 10 / price
                        if abs(holding * price) < 1:
                            continue
                        balances[cur[:-3].upper()+con] = {
                            'ts': ts,
                            'holding': holding,
                            'price': price,
                            'account': self.exch_account,
                        }
                except:
                    continue
        self.stat_okex['ft2'] = balances
        return balances


class ExchangeBina(BinaHttp):
    def __init__(self, account='kevinwang126@163.com'):
        self.conf = VConf()
        url = self.conf.get_http('binance')
        apikey = self.conf.get_apikey('binance', account)
        apisecret = self.conf.get_secret('binance', account)
        super(ExchangeBina, self).__init__(url, apikey, apisecret)
        self.exch_account = account
        self.stat_bina = {}

    def bb0(self):
        acc = self.account()
        infos = acc.get('balances')
        if not infos:
            return
        currency = infos
        balances = {}
        for cur in currency:
            holding = 0.0
            price = 0.0
            if(float(cur['free']) + float(cur['locked']) < 0.000001):
                continue
            holding = float(cur['free']) + float(cur['locked'])
            try:
                if cur['asset'].upper() == 'USDT':
                    price = 1.0
                else:
                    price = float(self.ticker(cur['asset'].upper() + 'USDT')['lastPrice'])
                balances[cur['asset'].upper()] = {
                    'ts': ts,
                    'holding': holding,
                    'price': price,
                    'account': self.exch_account,
                }
            except:
                continue
        self.stat_bina['bb0'] = balances
        return balances


class ExchangeHuobi(HuobiHttp):
    def __init__(self, account='kevinwang126@163.com'):
        self.conf = VConf()
        url = self.conf.get_http('huobi')
        apikey = self.conf.get_apikey('huobi', account)
        apisecret = self.conf.get_secret('huobi', account)
        self.__uid = ''
        super(ExchangeHuobi, self).__init__(url, apikey, apisecret)
        self.exch_account = account
        self.stat_huobi = {}

    def bb0(self):
        account = filter(lambda x: x['type'] == 'spot', self.accounts()['data'])[0]
        balances = self.balance(account['id'])
        if not balances or balances.get('status') != 'ok':
            return
        balance = {}
        for item in balances['data']['list']:
            holding = 0.0
            price = 0.0
            try:
                if(float(item['balance']) < 0.00000001):
                    continue
                item['currency'] = item['currency'].upper()
                key = item['currency']
                if(not balance.get(key)):
                    balance[key.upper()] = {
                        'ts': ts,
                        'holding': 0.0,
                        'price': 0.0,
                        'account': self.exch_account,
                    }
                if(item['type'] == 'trade'):
                    holding = float(item['balance'])
                if(item['type'] == 'frozen'):
                    holding = float(item['balance'])
                if key.lower() == 'usdt':
                    price = 1.0
                else:
                    price = self.detail_merged(key.lower() + 'usdt')['tick']['open']
                if holding * price < 1:
                    continue
                balance[key.upper()] = {
                    'ts': ts,
                    'holding': holding,
                    'price': price,
                    'account': self.exch_account,
                }
            except:
                continue
        self.stat_huobi['bb0'] = balance
        return balance


def main():
    '''整合以上三个类的数据
    '''
    # 合并三个交易所
    exch_account = {
        'okex': ['13651401725', 'BW1Hedge'],
        'bina': ['kevinwang126@163.com'],
        'huobi': ['kevinwang126@163.com'],
    }
    all3exchanges = {}
    for exch in exch_account:
        if exch == 'okex':
            for i, acc in enumerate(exch_account[exch]):
                exch_okex = ExchangeOkex(acc)
                exch_okex.bb0()
                exch_okex.ft1()
                exch_okex.ft2()
                if i == 0:
                    all3exchanges['OKEX'] = exch_okex.stat_okex
                if i > 0:
                    all3exchanges['OKEX' + str(i)] = exch_okex.stat_okex
                print('OKEX\n', '*' * 80, '\n', exch_okex.stat_okex, '\n', '*' * 80, '\n')
        if exch == 'bina':
            exch_bina = ExchangeBina()
            exch_bina.bb0()
            all3exchanges['bina'] = exch_bina.stat_bina
            print('BINA\n', '*' * 80, '\n', exch_bina.stat_bina, '\n', '*' * 80, '\n')
        if exch == 'huobi':
            exch_huobi = ExchangeHuobi()
            exch_huobi.bb0()
            all3exchanges['huobi'] = exch_huobi.stat_huobi
            print('HUOBI\n', '*' * 80, '\n', exch_huobi.stat_huobi, '\n', '*' * 80, '\n')

    # 保存为csv
    js = all3exchanges
    with open('BW1.csv', 'w') as g:
        columns = 'ts,exchange,label,currency,holding,price,account\n'
        g.write(columns)
        for exchange in js.keys():
            for label in js[exchange].keys():
                for currency in js[exchange][label].keys():
                    try:
                        ts = js[exchange][label][currency]['ts']
                        holding = js[exchange][label][currency]['holding']
                        price = js[exchange][label][currency]['price']
                        account = js[exchange][label][currency]['account']
                        line = [ts, exchange.upper(),  label.upper(), currency.upper(),
                                holding,  price, account.upper()]
                        line = str(line).replace('[', '').replace(']', '').replace('u', '').replace(' ','')
                        line = line.replace("'", '') + '\n'
                        g.write(line)
                    except:
                        continue
    df = pd.read_csv('BW1.csv')
    df['usdt'] = df['holding']*df['price']
    btc_usdt = getBtcUsdt()
    df['btc'] = df['usdt']/btc_usdt
    return df

def writeBW1DataToMysql():
    engine = create_engine('mysql://ops:ops!@#9988@47.74.249.179:3308/david')
    with engine.connect() as con:
        df = main()
        df.to_sql('BW1_BASE_DATA', con, schema='david', index=False, if_exists='append', chunksize=500)
        return 'finished'

if __name__ == '__main__':    
    print(writeBW1DataToMysql())
