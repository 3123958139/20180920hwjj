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

from vic.exchange.common.http import HttpClient

class HuobiHttp(HttpClient):
    def __init__(self, url, apikey, apisecret):
        super(HuobiHttp, self).__init__(url, apikey, apisecret)
        self.getheader  = {
                "Content-type": "application/x-www-form-urlencoded",
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'
            }
        self.postheader = {
                "Accept": "application/json",
                'Content-Type': 'application/json'
            }

    def __sign(self, method, param, host, path):
        data = sorted(param.items(), key=lambda d: d[0], reverse=False)
        data = urllib.urlencode(data)
        payload = [method, host, path, data]
        payload = '\n'.join(payload)
        payload = payload.encode(encoding='UTF8')
        digest = hmac.new(self.getApiSecret(), payload, digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(digest).decode()
        return sign

    def http_post_request(self, method, query=None, **args):
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params = {'AccessKeyId'     : self.getApiKey(),
                  'SignatureMethod' : 'HmacSHA256',
                  'SignatureVersion': '2',
                  'Timestamp'       : timestamp} #'2018-05-08T14:47:46'}
        host = urlparse.urlparse(self.getUrl()).hostname
        params['Signature'] = self.__sign('POST', params, host, method)
        url = '{url}{method}?{params}'.format(url=self.getUrl(), method=method, params=urllib.urlencode(params))
        params = {}
        params.update(**args)
        if query is not None: params.update(query)
        data = json.dumps(params)
        return self.http_request(url, 'POST', data, self.postheader)


    def http_get_request(self, method, query=None, **args):
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params = {}
        params.update(**args)
        if query is not None: params.update(query)
        url = '{url}{method}?{params}'.format(url=self.getUrl(), method=method, params=urllib.urlencode(params))
        return self.http_request(url, 'GET', None, self.getheader)


    def http_get_request_sign(self, method, query=None, **args):
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params = {}
        params.update(**args)
        if query is not None: params.update(query)
        params.update({'AccessKeyId': self.getApiKey(),
                       'SignatureMethod': 'HmacSHA256',
                       'SignatureVersion': '2',
                        'Timestamp'       : timestamp})
        host = urlparse.urlparse(self.getUrl()).hostname
        params['Signature'] = self.__sign('GET', params, host, method)
        url = '{url}{method}?{params}'.format(url=self.getUrl(), method=method, params=urllib.urlencode(params))
        return self.http_request(url, 'GET', None, self.getheader)



    ######################################public api################################################
    def symbols(self):
        ''' 查询Pro站支持的所有交易对及精度
            return : {
                status : 'ok'
                data : [
                    {
                        "base-currency": "eth",
                        "quote-currency": "usdt",
                        "symbol": "ethusdt"
                    },
                    ......
                ]
            }
        '''
        return self.http_get_request('/v1/common/symbols')

    def currencys(self):
        ''' 查询Pro站支持的所有币种
            return : {
                "status": "ok",
                data : [ "usdt", "eth",  "etc"]
            }
        '''
        return self.http_get_request('/v1/common/currencys')

    def timestamp(self):
        ''' 查询系统当前时间
            return : {
                "status": "ok",
                "data": 1494900087029
            }
        '''
        return self.http_get_request('/v1/common/timestamp')

    ######################################public api################################################


    ################################### market data ###############################################################
    def kline(self, symbol, period, size=150):
        '''
            period: 可选值：{1min, 5min, 15min, 30min, 60min, 1day, 1mon, 1week, 1year }
            size: 可选值： [1,2000]
        '''
        if(size > 20000 or size < 1) :
            raise Exception('size must in [1, 2000]')
        return self.http_get_request('/market/history/kline', symbol=symbol, period=period, size=size)

    def detail_merged(self, symbol):
        '''获取聚合行情(Ticker)'''
        return self.http_get_request('/market/detail/merged', symbol=symbol)


    def depth(self, symbol, type):
        ''' 获取 Market Depth 数据
            type : step0, step1, step2, step3, step4, step5（合并深度0-5）；step0时，不合并深度
        '''
        return self.http_get_request('/market/depth', symbol=symbol, type=type)

    def trade(self, symbol):
        '''获取 Trade Detail 数据'''
        return self.http_get_request('/market/trade', symbol=symbol)

    def history_trade(self, symbol, size=2000):
        ''' 批量获取最近的交易记录
            integer size : [1, 2000]
        '''
        return self.http_get_request('/market/trade', symbol=symbol, size=size)

    def detail(self, symbol):
        ''' 获取 Market Detail 24小时成交量数据
        '''
        return self.http_get_request('/market/detail', symbol=symbol)

    ################################### market data ###############################################################


    ################################### trade api  ###############################################################
    def accounts(self):
        ''' 查询当前用户的所有账户(即account-id)
            return : {
                "status": "ok",
                "data": [
                    "id": 100009,
                    "type": "spot",
                    "state": "working",
                    "user-id": 1000
                ]
            }
        '''
        return self.http_get_request_sign('/v1/account/accounts')

    def balance(self, account_id):
        '''查询Pro站指定账户的余额
            return {
                "status": "ok",
                data: {
                    "id": 100009,               #账户id
                    "type": "spot",             #spot：现货账户
                    "state": "working",         #working：正常 lock：账户被锁定
                    list: [
                        {
                            "currency": "usdt",
                             "type": "trade",       ##trade: 交易余额，frozen: 冻结余额
                             "balance": "500009195917.4362872650"
                        },
                        ......
                    ]
                }
            }
        '''
        return self.http_get_request_sign("/v1/account/accounts/{0}/balance".format(account_id), {"account-id": account_id})


    def place_order(self, accountid, symbol, price, amount, type, source='api'):
        ''' Pro站下单
            source :  api，如果使用借贷资产交易，请填写‘margin-api’
            type : buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖
            return : {
                "status": "ok",
                "data": "59378"
            }
        '''
        params = {"account-id"  : accountid,
                  "amount"      : amount,
                  "symbol"      : symbol,
                  "type"        : type,
                  "source"      : source,
                  'price'       : price}
        url = '/v1/order/orders/place'
        return self.http_post_request(url, params)

    def cancel_order(self, order_id):
        ''' 申请撤销一个订单请求
            return : {
                "status": "ok",//注意，返回OK表示撤单请求成功。订单是否撤销成功请调用订单查询接口查询该订单状态
                "data": "59378"
            }
        '''
        url = "/v1/order/orders/{0}/submitcancel".format(order_id)
        return self.http_post_request(url)

    def cancel_orders(self, order_ids):
        '''
            order_ids : {"order-ids": ['1', '2', ...]}单次不超过50个订单id 撤销订单ID列表
            return : {
                "status": "ok".
                data: {
                    "success": ['1', '2'],
                    "failed": [{"err-msg": "记录无效","order-id": "2","err-code": "base-record-invalid"}]
                }
            }
        '''
        return self.http_post_request('/v1/order/orders/batchcancel', order_ids)


    def order(self, order_id):
        '''GET  查询某个订单详情
            return : {
                "status": "ok",
                data : {
                    "id": 59378,
                    "symbol": "ethusdt",
                    "account-id": 100009,
                    "amount": "10.1000000000",
                    "price": "100.1000000000",
                    "created-at": 1494901162595,
                    "type": "buy-limit",            #buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖
                    "field-amount": "10.1000000000",
                    "field-cash-amount": "1011.0100000000",
                    "field-fees": "0.0202000000",
                    "finished-at": 1494901400468,
                    "user-id": 1000,
                    "source": "api",
                    "state": "filled",      #pre-submitted 准备提交, submitting , submitted 已提交, partial-filled 部分成交, partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销
                    "canceled-at": 0,
                    "exchange": "huobi",
                    "batch": ""
                }
            }
        '''
        url = "/v1/order/orders/{0}".format(order_id)
        return self.http_get_request_sign(url)

    def order_matchresults(self, order_id):
        ''' GET 查询某个订单的成交明细
            return : {
                "status": "ok",
                data : {
                    "id": 29553,
                    "order-id": 59378,
                    "match-id": 59335,
                    "symbol": "ethusdt",
                    "type": "buy-limit",
                    "source": "api",
                    "price": "100.1000000000",
                    "filled-amount": "9.1155000000",
                    "filled-fees": "0.0182310000",
                    "created-at": 1494901400435
                }
            }
        '''
        url = "/v1/order/orders/{0}/matchresults".format(order_id)
        return self.http_get_request_sign(url)


    def orders(self, symbol=None, states='pre-submitted,submitted,partial-filled,partial-canceled,filled,canceled', start_date=None, end_date=None, _from=None, direct=None, size=100000):
        ''' GET 查询当前委托、历史委托
            states : 使用','分割 pre-submitted 准备提交, submitted 已提交, partial-filled 部分成交, partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销
            return : {
                "status": "ok",
                data: {
                    "id": 59378,
                    "symbol": "ethusdt",
                    "account-id": 100009,
                    "amount": "10.1000000000",
                    "price": "100.1000000000",
                    "created-at": 1494901162595,
                    "type": "buy-limit",
                    "field-amount": "10.1000000000",
                    "field-cash-amount": "1011.0100000000",
                    "field-fees": "0.0202000000",
                    "finished-at": 1494901400468,
                    "user-id": 1000,
                    "source": "api",
                    "state": "filled",
                    "canceled-at": 0,
                    "exchange": "huobi",
                    "batch": ""
                }
            }
        '''
        params = {}
        if symbol   : params['symbol'] = symbol
        if states    : params['states'] = states
        if start_date : params['start-date'] = start_date
        if end_date : params['end-date'] = end_date
        if _from : params['from'] = _from
        if direct : params['direct'] = direct
        if size : params['size'] = size
        url = '/v1/order/orders'
        return self.http_get_request_sign(url, params)

    def orders_matchresults(self, symbol=None, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
        ''' GET 查询当前成交、历史成交
            types : buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖
            return : {
                "status": "ok",
                data: {
                    "id": 29555,
                    "order-id": 59378,
                    "match-id": 59335,
                    "symbol": "ethusdt",
                    "type": "buy-limit",
                    "source": "api",
                    "price": "100.1000000000",
                    "filled-amount": "0.9845000000",
                    "filled-fees": "0.0019690000",
                    "created-at": 1494901400487
                }
            }
        '''
        params = {}
        if symbol   : params['symbol'] = symbol
        if types    : params['types'] = types
        if start_date : params['start-date'] = start_date
        if end_date : params['end-date'] = end_date
        if _from : params['from'] = _from
        if direct : params['direct'] = direct
        if size : params['size'] = size
        url = '/v1/order/matchresults'
        return self.http_get_request_sign(url, params)

    def orders_matchresults_test(self, size=10):
        ''' 查询当前成交、历史成交 '''
        url = '/v1/order/matchresults'
        return self.http_get_request_sign(url)



    ################################### trade api  ###############################################################

    ################################### account api  ###############################################################
    def withdraw(self, address, amount, currency, fee=0):
        ''' POST 申请提现虚拟币
            address : 提现地址
            currency : 资产类型
            fee : 转账手续费
            return : {
                "status": "ok",
                "data": 700     #提现ID
            }
        '''
        url = '/v1/dw/withdraw/api/create'
        return self.http_post_request(url, address=address, amount=amount, currency=currency, fee=fee)

    # 申请取消提现虚拟币
    def cancel_withdraw(self, withdraw_id):
        ''' POST 申请取消提现虚拟币
            return : {
                "status": "ok",
                "data": 700     #提现ID
            }
        '''
        url = '/v1/dw/withdraw-virtual/{0}/cancel'.format(withdraw_id)
        return self.http_post_request(url)

    def query_withdraw(self, currency, type, size=10000000):
        ''' GET  查询虚拟币充提记录 默认查询所有的
            type : 'deposit' or 'withdraw'
            return : {
                "status": "ok",
                data : [
                    {
                        "id": 1171,
                        "type": "deposit",  #deposit' 'withdraw'
                        "currency": "xrp",
                        "tx-hash": "ed03094b84eafbe4bc16e7ef766ee959885ee5bcb265872baaa9c64e1cf86c2b",
                        "amount": 7.457467,
                        "address": "rae93V8d2mdoUQHwBDBdM4NHCMehRJAsbm",
                        "address-tag": "100040",
                        "fee": 0,
                        "created-at": 1510912472199,
                        "updated-at": 1511145876575
                        "state": "safe",
                    },
                    ......
                ]
            }
            state :
            提现状态 : submitted, reexamine, canceled, pass,reject,pre-transfer,wallet-transfer,wallet-reject,confirmed,confirm-error,repealed
            充值状态 : unknown, confirming, confirmed, safe, orphan
        '''
        return self.http_get_request_sign('/v1/query/deposit-withdraw', {'from':0}, currency=currency, type=type, size=size)
    ################################### account api  ###############################################################

    ###################################  借贷 trade api  ###############################################################

    def exchange_to_margin(self, symbol, currency, amount):
        ''' POST 现货账户划入至借贷账户
            return : {
                "status": "ok",
                "data": 1000        # 划转ID
            }
        '''
        url = "/v1/dw/transfer-in/margin"
        return self.http_post_request(url, symbol=symbol, currency=currency, amount=amount)

    def margin_to_exchange(self, symbol, currency, amount):
        ''' POST 借贷账户划出至现货账户
            return : {
               "status": "ok",
               "data": 1000        # 划转ID
            }
        '''
        url = "/v1/dw/transfer-out/margin"
        return self.http_post_request(url, symbol=symbol, currency=currency, amount=amount)

    def loan_margin(self, symbol, currency, amount):
        ''' POST 申请借贷
            return : {
                "status": "ok",
                "data": 59378       #订单号
            }
        '''
        url = "/v1/margin/orders"
        return self.http_post_request(url, symbol=symbol, currency=currency, amount=amount)

    def repay_margin(self, order_id, amount):
        ''' POST 归还借贷
            order_id : 借贷订单 ID，写在path中
            return : {
                status": "ok",
                "data": 59378   #订单号
            }
        '''
        url = "/v1/margin/orders/{0}/repay".format(order_id)
        return self.http_post_request(url, {'order-id': order_id}, amount=amount)

    def margin_orders(self, symbol, states='',  size='100000'):
        ''' GET 查询借贷订单
            states : 状态 created 未放款，accrual 已放款，cleared 已还清，invalid 异常
            return : {
                "status": "ok",
                data : {
                    "loan-balance": "0.100000000000000000",     #未还本金
                    "interest-balance": "0.000200000000000000", #未还利息
                    "interest-rate": "0.002000000000000000",    #利率
                    "loan-amount": "0.100000000000000000",      #借贷本金总额
                    "accrued-at": 1511169724531,                #最近一次计息时间
                    "interest-amount": "0.000200000000000000",  #利息总额
                    "symbol": "ethbtc",         #交易对
                    "currency": "btc",          #币种
                    "id": 394,                  #订单号
                    "state": "accrual",         #created 未放款，accrual 已放款，cleared 已还清，invalid 异常
                    "account-id": 17747,        #账户ID
                    "user-id": 119913,          #用户ID
                    "created-at": 1511169724531 #借贷发起时间
                }
            }
        '''
        url = "/v1/margin/loan-orders"
        return self.http_get_request(url, symbol=symbol, states=states, size=size)

    def margin_balance(self):
        ''' GET 借贷账户详情
           return : {
                "status": "ok",
                data: [
                    {
                        "id": 18264,
                        "type": "margin",
                        "state": "working",
                        "symbol": "btcusdt",
                        "fl-price": "0",
                        "fl-type": "safe",
                        "risk-rate": "475.952571086994250554",
                        "list": [
                            {
                                "currency": "btc",
                                "type": "trade",
                                "balance": "1168.533000000000000000"
                            },
                            ......
                        ]
                    }
                ]
           }
        '''
        url = "/v1/margin/accounts/balance"
        return self.http_get_request_sign(url)
    ###################################  借贷 trade api  ###############################################################

if __name__ == "__main__":
    url = "https://api.huobipro.com"
    #dreamy
    #apiKey = "3af5ee91-4bc1407b-d68cd6a5-7291b"
    #apiSecret    = "319c3ea1-88eeb820-a80d5ae8-3f93b"

    #simons
    apiKey = '4163ada2-fee5a229-97e5600a-60259'
    apiSecret = 'b1e638f0-a17d88a8-048d26a3-7f4ea'

    http = HuobiHttp(url, apiKey, apiSecret)
    print(http.symbols())
    #print(http.currencys())
    #print(http.timestamp())
    #print(http.detail_merged('btcusdt'))
    #print(http.depth('btcusdt', 'step0'))
    #print(http.trade('btcusdt'))
    #print(http.history_trade('btcusdt', size=200))
    #print(http.detail('btcusdt'))

    #aid = http.accounts()
    #print(aid)
    #for it in aid['data']:
    #    print(http.balance(it['id']))

    #h = http.orders_matchresults(_from='1283306331', direct='prev');
    #print(h)

    #rsp = http.place_order(581289, 'ethusdt', '0.02', '750', 'sell-limit')
    #print(rsp)
    
    #n = [{'id': s['id'], 'symbol':s['symbol'], 'oid': s['order-id']} for s in h['data']]
    #print(n)
    #print(http.orders())
    #print(http.orders(_from='3334070460', direct='prev'))
    #print(http.order_matchresults('btcusdt', 10))
    #print(http.query_withdraw('btc', 'withdraw', size=10))

    #print(http.margin_balance())







