# -*- coding: utf-8 -*-
# @Date    : 2018-03-06 15:40:03
# @Author  : DreamyZhang
# @QQ      : 775745576

from vic.exchange.common.http import HttpClient
import logging
import sys

class OkexftHttp(HttpClient):
    def __init__(self, url, apikey, apisecret):
        super(OkexftHttp, self).__init__(url, apikey, apisecret)
   
   ####################market data api start################################
    def future_ticker(self, symbol, contract_type):
        ''' GET  获取OKEx合约行情
            symbol :btc_usd ltc_usd eth_usd etc_usd bch_usd
            contract_type : this_week/next_week/quarter
            return : {
                date: '1411627632',
                ticker: {...}
            }
        '''
        return self.http_get_request('future_ticker.do', symbol=symbol, contract_type=contract_type)          
    
    def future_depth(self, symbol, contract_type, size=200, merge=0):
        ''' GET  获取OKEx合约深度信息
            Integer size: 1 -- 200
            Integer merge : 否(默认0)   value：1(合并深度)
            return:{'asks':[[12,32], ], 'bids':[[123, 1], ]}
        '''
        # 最大200 默认20
        return self.http_get_request('future_depth.do', symbol=symbol, contract_type=contract_type, size=size, merge=merge)          
    
    def future_trades(self, symbol, contract_type):
        ''' GET 获取OKEx合约交易记录信息
            return : [{
                    "amount":11,
                    "date_ms":140807646000,
                    "date":140807646,
                    "price":7.076,
                    "tid":37,
                    "type":"buy"
                }, {}]
        '''
        return self.http_get_request('future_trades.do', symbol=symbol, contract_type=contract_type)          
    
    def future_index(self, symbol):
        ''' GET 获取OKEx合约指数信息
            symbol: btc_usd ltc_usd eth_usd etc_usd bch_usd
            return : {"future_index":471.0817}
        '''
        return self.http_get_request('future_index.do', symbol=symbol)

    def exchange_rate(self):
        ''' GET 获取美元人民币汇率
            return : { "rate":6.1329 }
        '''
        return self.http_get_request('exchange_rate.do')

    def future_estimated_price(self, symbol):
        ''' GET 获取交割预估价
            return {"forecast_price":5.4}
        '''
        return self.http_get_request('future_estimated_price.do', symbol=symbol)

    def future_kline(self, symbol, type,  contract_type, size=20, since=0):
        ''' GET 获取OKEx合约深度信息
            type : 1min/3min/5min/15min/30min/1day/3day/1week/1hour/2hour/4hour/6hour/12hour
            Integer size :  默认0
            return : [[
                1440308760000,  时间戳
                233.38,     开
                233.38,     高
                233.27,     低
                233.37,     收
                186,        交易量
                79.70234956     交易量转化BTC或LTC数量
                ], [], ]
        '''
        return self.http_get_request('future_kline.do', type=type, symbol=symbol,contract_type=contract_type, size=size)          

    def future_hold_amount(self, symbol, contract_type):
        ''' GET 获取当前可用合约总持仓量
            return : [["amount": 106856, "contract_name": "BTC0213"]]
        '''
        return self.http_get_request('future_hold_amount.do', symbol=symbol, contract_type=contract_type);
    
    def future_price_limit(self, symbol, contract_type):
        ''' GET  获取合约最高限价和最低限价
        '''
        return self.http_get_request('future_price_limit.do', symbol=symbol, contract_type=contract_type)
    ####################market data api end################################
   
    
    ####################trade  api start################################
    def future_userinfo(self):
        ''' POST  获取OKEx合约账户信息(全仓)
            return : {
                "info": {
                    'btc':{
                        'ount_rights": 1,
                        "keep_deposit": 0,
                        "profit_real": 3.33,
                        "profit_unreal": 0,
                        "risk_rate": 10000
                    },
                    ....
                },
                "result": true
            }
        '''  
        return self.http_post_request('future_userinfo.do', api_key=self.getApiKey())           
    
    def future_position(self, symbol, contract_type):
        ''' POST 获取用户持仓获取OKEX合约账户信息 （全仓）
            return : {
                "force_liqu_price": "0.07",             #预估爆仓价格
                "holding": [
                    "buy_amount": 1,
                    "buy_available": 0,
                    "buy_price_avg": 422.78,
                    "buy_price_cost": 422.78,
                    "buy_profit_real": -0.00007096,
                    "contract_id": 20141219012,
                    "contract_type": "this_week",
                    "create_date": 1418113356000,
                    "lever_rate": 10,
                    "sell_amount": 0,
                    "sell_available": 0,
                    "sell_price_avg": 0,
                    "sell_price_cost": 0,
                    "sell_profit_real": 0,
                    "symbol": "btc_usd"
                ]
                "result": true
            }
        '''
        return self.http_post_request('future_position.do', symbol=symbol, contract_type=contract_type, api_key=self.getApiKey())

    def future_trade(self, symbol, contract_type, tradetype, price, amount, match_price=0):
        ''' POST 合约下单 访问频率5次/秒
            return  : {"result":true,"order_id":123456}
            tradetype: 1:开多 2:开空 3:平多 4:平空
            match_price: 是否为对手价 0:不是 1:是 ,当取值为1时,price无效(0 现价单 1市价单)
        '''
        return self.http_post_request('future_trade.do', api_key=self.getApiKey(), symbol=symbol, contract_type=contract_type, type=tradetype, price=price, amount=amount, match_price=match_price)           
    
    
    def future_trades_history(self, symbol, date, since):
        ''' POST 获取OKEX合约交易历史（非个人）
            date : 合约交割时间，格式yyyy-MM-dd
            Long since : 交易Id起始位置
            return : [
                    {
                      "amount": 11,
                      "date": 140807646000,
                      "price": 7.076,
                      "tid": 37,
                      "type": "buy"     
                    },
                    ...
                ]
        ''' 
        return self.http_post_request('future_trades_history.do', api_key=self.getApiKey(), symbol=symbol, date=date, since=since)
    
    def future_batch_trade(self, symbol, contract_type, orders_data):
        ''' POST 批量下单 访问频率5次/秒
            type: 限价单(buy/sell)
            orders_data: string([{price:3,amount:5,type:1,match_price:1}, ...])) 最大下单量为5
            return :
                    {"order_info":[
                        {"order_id":41724206},
                        {"error_code":10011,"order_id":-1},
                        {"error_code":10014,"order_id":-1}
                    ],
                    "result":true}
        '''
        return self.http_post_request('future_batch_trade.do', api_key=self.getApiKey(), symbol=symbol, contract_type=contract_type, orders_data=orders_data)           

    def future_cancel(self, symbol, contract_type, orderid): 
        ''' POST 取消合约订单 访问频率10次/秒
            orderid: 订单ID(多个订单ID中间以","分隔,一次最多允许撤消3个订单)
            return : 
                批量撤销 ： {"success":"123456,123457","error":"123458,123459"}
                单个撤销： {"order_id":"161277", "result":true}
        '''
        return self.http_post_request('future_cancel.do', api_key=self.getApiKey(), symbol=symbol, contract_type=contract_type, order_id=orderid)           
   
    def future_order_info(self, symbol, contract_type, order_id, status='1', current_page=0, page_length=50):
        ''' POST 获取合约订单信息
            status : 查询状态 1:未完成的订单 2:已经完成的订单
            orders : 订单ID -1:查询指定状态的订单，否则查询相应订单号的订单
            current_page : 当前页数
            page_length : 每页获取条数，最多不超过50
            return : {
                    "result":true
                    orders:[
                        {
                            "amount":111,
                            "contract_name":"LTC0815",
                            "create_date":1408076414000,
                            "deal_amount":1,
                            "fee":0,
                            "order_id":106837,
                            "price":1111,
                            "price_avg":0,
                            "status":"0",
                            "symbol":"ltc_usd",
                            "type":"1",
                            "unit_amount":100,
                            "lever_rate":10
                        },
                        ...
                    ]
                }
        '''
        params = {}
        params['api_key'] = self.getApiKey()
        params['symbol'] = symbol
        params['contract_type'] = contract_type
        if order_id == '-1':
            params['order_id'] = '-1' 
            params['status'] = status
            params['current_page'] = current_page
            params['page_length'] = page_length
        else:
            params['order_id'] = order_id  
        return self.http_post_request('future_order_info.do', params)

    def future_order_info_page(self, symbol, contract_type, status='1', current_page=0, page_length=50):
        '''分页查询'''
        return self.future_order_info(symbol, contract_type, '-1', status, current_page, page_length)

    def future_orders_info(self, symbol, contract_type, order_id): 
        ''' POST  批量获取合约订单信息
            orderid:  订单ID -1:查询指定状态的订单，否则查询相应订单号的订单
            return :{
                    "result": true
                    orders [
                        {
                            "amount": 1,
                            "contract_name": "BTC0213",
                            "create_date": 1424932853000,
                            "deal_amount": 0,
                            "fee": 0,
                            "lever_rate": 20,
                            "order_id": 200144,
                            "price": 1,
                            "price_avg": 0,
                            "status": 0,
                            "symbol": "btc_usd",
                            "type": 1,
                            "unit_amount": 100
                        },
                        ...
                    ]
                }
        '''
        return self.http_post_request('future_orders_info.do', api_key=self.getApiKey(), symbol=symbol, order_id=order_id, contract_type=contract_type)           

    
    def future_userinfo_4fix(self):
        ''' POST 获取逐仓合约账户信息
            return : {
                "result": true
                info:{
                    btc:{
                        "balance": 99.95468925,         #账户余额
                        "rights": 99.95468925           #账户权益
                        "contracts": [{
                            "available": 99.95468925,   #合约可用
                            "balance": 0.03779061,      #账户(合约)余额
                            "bond": 0,                  #固定保证金
                            "contract_id": 20140815012, #合约ID
                            "contratct_type": "this_week",
                            "freeze": 0,                #冻结
                            "profit": -0.03779061,      #已实现盈亏
                            "unprofit": 0               #未实现盈亏
                        }],
                    },
                    ......
                }
            }
        '''
        return self.http_post_request('future_userinfo_4fix.do', api_key=self.getApiKey())
   
    def future_position_4fix (self, symbol, contract_type, type='1'):
        ''' POST 逐仓用户持仓查询
            type : 默认返回10倍杠杆持仓 type=1 返回全部持仓数据
            return :{
                "result": true
                "holding": [{
                    "buy_amount": 10,
                    "buy_available": 2,
                    "buy_bond": 1.27832803,
                    "buy_flatprice": "338.97",
                    "buy_price_avg": 555.67966869,
                    "buy_price_cost": 555.67966869,
                    "buy_profit_lossratio": "13.52",
                    "buy_profit_real": 0,
                    "contract_id": 20140815012,
                    "contract_type": "this_week",
                    "create_date": 1408594176000,
                    "sell_amount": 8,
                    "sell_available": 2,
                    "sell_bond": 0.24315591,
                    "sell_flatprice": "671.15",
                    "sell_price_avg": 567.04644056,
                    "sell_price_cost": 567.04644056,
                    "sell_profit_lossratio": "-45.04",
                    "sell_profit_real": 0,
                    "symbol": "btc_usd",
                    "lever_rate": 10
                
                }]
            }
        '''
        return self.http_post_request('future_position_4fix.do', api_key=self.getApiKey(), symbol=symbol, contract_type=contract_type, type=type)
    
    def future_explosive (self, symbol, contract_type, status):
        ''' des : 获取合约爆仓单
            return :[
                {
                    "data": [
                        {
                            mount": "42",
                            "create_date": "2015-02-27 11:48:07",
                            "loss": "-0.54275722",
                            "price": "249.02",
                            "type": 4 #交易类型 1：买入开多 2：卖出开空 3：卖出平多 4：买入平空
                        },
                        ...
                    ]
                }
            ]
        '''
        return self.http_post_request('future_explosive.do', api_key=self.getApiKey(), symbol=symbol, contract_type=contract_type, status=status)
    
    
    ####################trade  api end################################
    def future_devolve(self, symbol, type, amount):
        ''' POST 个人账户资金划转
            type : 划转类型。1：币币转合约 2：合约转币币
        '''
        return self.http_post_request('future_devolve.do', api_key=self.getApiKey(), symbol=symbol, type=type, amount=amount)
    ####################trade  api end################################

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')

    apikey    = 'db98cb7e-71c4-442d-bf45-8c6ab05a4c1c'
    apisecret = '4A5F6437B9DE1A2B16E80FC0018C8515'
    url       = "https://www.okex.com/api/v1"
    
    http= OkexftHttp(url, apikey, apisecret)
    
    #print(http.future_ticker('btc_usd', 'this_week'))
    #print(http.future_depth('btc_usd', 'this_week'))
    #print(http.future_trades('btc_usd', 'this_week'))
    #print(http.future_index('btc_usd'))
    #print(http.exchange_rate())
    #print(http.future_estimated_price('btc_usd'))
    #print(http.future_kline('btc_usd', '1min', 'this_week'))
    #print(http.future_hold_amount('btc_usd', 'this_week'))
    #print(http.future_price_limit('btc_usd', 'this_week'))

    #全仓
    #print(http.future_userinfo())
    print(http.future_position('eth_usd', 'next_week'))
    #print(http.future_position_4fix('btc_usd', 'this_week'))
    #print(http.future_trade('eth_usd', 'this_week', '1', '400', '1'))
    
    #参数错误 不通过
    #print(http.future_trades_history('btc_usd', '2018-04-01', 1232454544543434))
    
    #签名错误不通过
    #print(http.future_batch_trade('btc_usd', 'this_week', "[{price:3,amount:1,type:1,match_price:1}]"))
    #print(http.future_batchTrade('ltc_usd','this_week','[{price:0.1,amount:1,type:1,match_price:0},{price:0.1,amount:3,type:1,match_price:0}]','20'))

    #print(http.future_cancel('btc_usd', 'this_week', '1111'))
  
    #傻逼接口 没测试出来不同
    #print(http.future_order_info('eth_usd', 'quarter', '-1'))
    #print(http.future_order_info_page('btc_usd', 'this_week', '1', '0', '50'))
    #print(http.future_orders_info('btc_usd', 'this_week', '-1'))
    
    #print(http.future_explosive ('btc_usd', 'this_week', '1'))    
    
    
    #未通过
    print(http.future_devolve('eos_usd', '1', '1'))
    
    



