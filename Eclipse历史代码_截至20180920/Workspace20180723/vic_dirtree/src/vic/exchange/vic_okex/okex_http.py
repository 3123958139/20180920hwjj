# -*- coding: utf-8 -*-
# @Date    : 2018-03-06 15:40:03
# @Author  : DreamyZhang
# @QQ      : 775745576

from vic.exchange.common.http import HttpClient
import logging

class OkexHttp(HttpClient):
    def __init__(self, url, apikey, apisecret):
        super(OkexHttp, self).__init__(url, apikey, apisecret)
   
   ####################market data api start################################
    def ticker(self, symbol):
        return self.http_get_request('ticker.do', symbol=symbol)          
    
    def depth(self, symbol, size=20):
        # 最大200 默认20
        return self.http_get_request('depth.do', symbol=symbol, size=size)          
    
    def trades(self, symbol):
        #默认600条
        return self.http_get_request('trades.do', symbol=symbol)          
    
    def klines(self, type, symbol, size=2000):
        # type : 1min/3min/5min/15min/30min/1day/3day/1week/1hour/2hour/4hour/6hour/12hour
        # size : 最多2000条 默认返回所有
        return self.http_get_request('kline.do', type=type, symbol=symbol, size=size)          

    ####################market data api end################################
    
    ####################trade  api start################################
    def userinfo(self):
        '''
            访问频率 6次/2秒
            {
                "info": {
                    "funds": {
                        free": {"btc": "0","usd": "0",},
                        freezed": {"btc": "0", "usd": "0",}
                    }
                },
                "result": true
            }
        '''  
        return self.http_post_request('userinfo.do', api_key=self.getApiKey())           
    
    def addorder(self, symbol, tradetype, price, amount):
        ''' 频率 20次/2秒
            return  : {"result":true,"order_id":123456}
            tradetype: 限价单(buy/sell) 市价单(buy_market/sell_market)
            price :  Double
            amount : Double
        '''
        return self.http_post_request('trade.do', api_key=self.getApiKey(), symbol=symbol, type=tradetype, price=price, amount=amount)           
    
    def batch_trade(self, symbol, tradetype, orders_data):
        '''
            tradetype: 限价单(buy/sell)
            orders_data: string([{price:3,amount:5,type:'sell'},{price:3,amount:3,type:'buy'}])) 最大下单量为5
            return :
                    {"order_info":[
                        {"order_id":41724206},
                        {"error_code":10011,"order_id":-1},
                        {"error_code":10014,"order_id":-1}
                    ],
                    "result":true}
        '''
        return self.http_post_request('trade.do', api_key=self.getApiKey(), symbol=symbol, type=tradetype, orders_data=orders_data)           

    def cancelorder(self, symbol, orderid): 
        '''
            orderid: 订单ID(多个订单ID中间以","分隔,一次最多允许撤消3个订单)
            return : {"success":"123456,123457","error":"123458,123459"}
        '''
        return self.http_post_request('cancel_order.do', api_key=self.getApiKey(), symbol=symbol, order_id=orderid)           
    
    def orderinfo(self, symbol, orderid=-1):
        ''''
            status： -1：已撤销  0：未成交 1：部分成交 2：完全成交 4:撤单处理中
            orderid : Long 默认订单ID -1:未完成订单
            return : {
                "result": true,
                "orders": [
                    {
                        "amount": 0.1,
                        "avg_price": 0,
                        "create_date": 1418008467000,
                        "deal_amount": 0,
                        "order_id": 10000591,
                        "orders_id": 10000591,
                        "price": 500,
                        "status": 0,
                        "symbol": "btc_usd",
                        "type": "sell"
                    }
                ]
            }
        '''
        return self.http_post_request('order_info.do', api_key=self.getApiKey(), symbol=symbol, order_id=orderid)           

    def ordersinfo(self, symbol, orderid, tradetype): 
        '''
            orderid:  Integer  0:未完成的订单 1:已经完成的订单
            orderid: 订单ID(多个订单ID中间以","分隔,一次最多允许查询50个订单)
        '''
        return self.http_post_request('orders_info.do', api_key=self.getApiKey(), symbol=symbol, order_id=orderid, type=tradetype)           

    def order_history(self, symbol, status=0, current_page=1, page_length=200):
        '''
        '''
        return self.http_post_request('order_history.do', api_key=self.getApiKey(), symbol=symbol, status=status, current_page=current_page, page_length=page_length)
    
    ####################trade  api end################################
    def withdraw(self, symbol,chargefee,trade_pwd,withdraw_address,withdraw_amount,target):
        '''
            return : { "withdraw_id":301, "result":true}
            chargefee : Double 网络手续费 >=0 BTC范围 [0.002，0.005] LTC范围 [0.001，0.2] ETH范围 [0.01] ETC范围 [0.0001，0.2] BCH范围 [0.0005，0.002] 手续费越高，网络确认越快，向OKCoin提币设置为0
            trade_pwd : 交易密码
            withdraw_address : 认证的地址、邮箱或手机号码
            withdraw_amount : Double 提币数量 BTC>=0.01 LTC>=0.1 ETH>=0.1 ETC>=0.1 BCH>=0.1
            target : 地址类型 okcn：国内站 okcom：国际站 okex：OKEX address：外部地址
        '''
        return self.http_post_request('withdraw.do', api_key=self.getApiKey(), symbol=symbol, chargefee=chargefee, trade_pwd=trade_pwd, withdraw_address=withdraw_address, withdraw_amount=withdraw_amount, target=target)           

    def cancel_withdraw(self, symbol, withdraw_id):
        '''
            return : { "result":true, "withdraw_id":301}
            withdraw_id : 提币申请Id
        '''
        return self.http_post_request('cancel_withdraw.do', api_key=self.getApiKey(), symbol=symbol, withdraw_address=withdraw_address)           

    def withdraw_info(self, symbol, withdraw_id):
        '''
            查询提币BTC/LTC/ETH/ETC/BCH信息
            return : {
                        "result": true,
                        "withdraw": [
                            {
                                "address": "15KGp……",
                                "amount": 2.5,
                                "created_date": 1447312756190,
                                "chargefee": 0.1,
                                "status": 0,
                                "withdraw_id": 45001
                            }
                        ]
                    }
        '''
        return self.http_post_request('withdraw_info.do', api_key=self.getApiKey(), symbol=symbol, withdraw_address=withdraw_address)           
    
    def account_records(self, symbol, type, current_page, page_length):
        '''
            return : {
                        "records": [
                            {
                                "addr": "1CWKbfwxSkEWP8W45D76j3BX8vPieoSCyL",
                                "account": "12312",
                                "amount": 0,
                                "bank": "中国银行",
                                "benificiary_addr": "350541545",
                                "transaction_value": 111,
                                "fee": 0,
                                "date": 1418008467000,
                                "status": 1
                            }
                        ],
                        "symbol": "btc"
                     }
        '''
        return self.http_post_request('account_records', api_key=self.getApiKey(), symbol=symbol, type=type, current_page=current_page, page_length=page_length)
    
    #################### withdraw ###########################################
    

import logging, sys

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')

    apikey    = 'db98cb7e-71c4-442d-bf45-8c6ab05a4c1c'
    apisecret = '4A5F6437B9DE1A2B16E80FC0018C8515'
    url       = "https://www.okex.com/api/v1"
    
    http= OkexHttp(url, apikey, apisecret)
    
    #print (' 现货行情 ')
    #print (http.klines('1min', 'ltc_btc', 10))
    
    #print(http.http_post_request('order_info.do', api_key=http.getApiKey()))
    #print(http.http_post_request('order_info.do', api_key=http.getApiKey(), order_id=-1))

    #print(http.http_post_request('orders_info.do', api_key=http.getApiKey(),  type=0))
    #print(http.http_post_request('orders_info.do', api_key=http.getApiKey(),  type=1))
 
    print (u' 现货订单信息查询 ')
    print (http.orderinfo('btc_usdt'))

    #print (u' 现货批量订单信息查询 ')
    #print (http.ordersinfo('ltc_eth','6426168,34144382','0'))

   
    sys.exit(-1)
    print (' 用户现货账户信息 ')
    print (http.userinfo())

    #print (u' 现货下单 ')
    #print (http.trade('ltc_usd','buy','0.1','0.2'))

    #print (u' 现货批量下单 ')
    #print (http.batchTrade('ltc_usd','buy','[{price:0.1,amount:0.2},{price:0.1,amount:0.2}]'))

    #print (u' 现货取消订单 ')
    #print (http.cancelOrder('ltc_usd','18243073'))



