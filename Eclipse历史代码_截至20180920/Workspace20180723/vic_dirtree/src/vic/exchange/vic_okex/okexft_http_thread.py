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

from okexft_ws_thread import  OkexftWsThread
from okexft_http import  OkexftHttp


class OkexftHttpThread(OkexftWsThread, OkexftHttp):
    def __init__(self, url, wss, channels, apikey, apisecret, queue=None, echname='OKEXFT'):
        OkexftHttp.__init__(self, url, apikey, apisecret)
        OkexftWsThread.__init__(self, wss, channels, apikey, apisecret, queue, echname)
        self.__echname = echname
        self.__orders = {}
        #{OKEXTF-BTC-TW: {'contract_name' : '', '' : ''}}
        self.__channel_instrument = {}

        orders = self.getOpenOrders()
        for order in orders:
            self.getQueue().append((DateType.ON_ACCOUNT_ORDER, self.__echname, order))
        
        balances = self.getAccountBalance()
        self.getQueue().append((DateType.ON_ACCOUNT_BALANCE, self.__echname, balances))
        
        positions = self.get_positions()
        self.getQueue().append((DateType.ON_ACCOUNT_POSITION, self.__echname, positions))


    ############################线程覆盖函数#############################################
   
    def ok2ft(self, symbol, contract_type):
        '''ETH0204/eth_usd -----> ETH'''
        symbol = ''.join([i for i in symbol if i>'9' or i<'0'])
        symbol = symbol.replace('_usd', '').upper()
        return  self.__echname + '--' + symbol + '--' + self.get_ontract_type()[contract_type]

    def on_account_order(self, key, data):
        '''
            type(int): 订单类型 1：开多 2：开空 3：平多 4：平空
            system_type(int):订单类型 0:普通 1:交割 2:强平 4:全平 5:系统反单
            status(int): 订单状态(0等待成交 1部分成交 2全部成交 -1撤单 4撤单处理中)
        '''
        symbol = self.ok2ft(data['contract_name'], data['contract_type'])
        self.__channel_instrument[symbol] = data['contract_id']
        self.__channel_instrument[data['contract_id']] = symbol
        
        #logging.info('key: %r,  symbol:%r,  order: %r', symbol, key, data)
        data['orderid'] = self.__echname + '--' + str(data['orderid'])
        data['status']  = self.__order_status(data['status'])
        data['order_type'] = self.__okft2local_order_type(data['type'])
        data['offset']     = self.__local2okft_offset(data['type'], data['system_type'])
        #data['price_type'] = self.__ok2local_price_type(data['type'])

        order = {}
        order['order_id']   = data['orderid']
        order['status']     = data['status']
        order['symbol']     = symbol
        order['order_type'] = data['order_type']
        order['price_type'] = PriceType.Limit
        order['price']      = data['price']
        order['amount']     = data['amount']
        order['deal_amount']= data['deal_amount']
        order['avg_price']  = data['price_avg']
        order['fee']        = data['fee']
        order['datetime']   = datetime.datetime.utcfromtimestamp(int(data['create_date'])/1000)
        
        order['contract']   = data['contract_name']
        order['lever_rate'] = data['lever_rate']     
        order['offset']     = data['offset']     
        self.getQueue().append((DateType.ON_ACCOUNT_ORDER, self.__echname, Order(order)))

        if(order['order_id'] in self.__orders.keys()):
            diff = float(order['deal_amount']) - float(self.__orders[order['order_id']]['deal_amount'])
            if(diff > 0.00000001) :
                trade = {}
                trade['order_id']   = order['order_id']
                trade['order_type'] = order['order_type']
                trade['price_type'] = PriceType.Limit
                trade['offset']     = order['offset']
                trade['volume']     = diff
                trade['price']      = order['price']
                trade['symbol']     = symbol
                trade['id']         = order['order_id'] + str(time.time())
                trade['fee']        = order['fee'] - float(self.__orders[order['order_id']]['fee'])
                trade['datetime']   = datetime.datetime.utcnow()
                self.getQueue().append((DateType.ON_ACCOUNT_TRADE, self.__echname, Trade(trade)))
                self.__orders[order['order_id']]['deal_amount'] = order['deal_amount']
        else:
            self.__orders[order['order_id']] = order
         
        if(order['deal_amount'] == order['amount']):
            try:
                self.__orders.pop(order['order_id'])
            except Exception, e:
                pass
        
    def on_account_userinfo(self, key, data):
        #logging.info('instrument: %r,  balance: %r', key, data)
        #逐仓账户独立计算风险  总账户要向逐仓账户转钱。
        if 'contracts' in data.keys(): 
            raise Exception('not support the fix account model!')
        account = {}
        account['currency']      = data['symbol'].replace('_usd', '').upper()
        account['fee']           = 0
        account['freezed']       = 0    #挂单占用
        account['margin']        = data['keep_deposit']
        account['free']          = data['balance'] - data['keep_deposit'] - account['freezed']
        
        
        account['closeprofit']   = data['profit_real']
        account['positionprofit']= 0
        account['datetime']      = datetime.datetime.utcnow()
        
        self.getQueue().append((DateType.ON_ACCOUNT_BALANCE, self.__echname, {self.__echname + '--' + account['currency']: AccountBalance(account)}))

    def on_account_position(self, key, data):
        positions = {}
        #logging.info(data)
        for item in data['positions']:
            position = {}
            position['symbol']          = self.__channel_instrument[item['contract_id']]
            position['direction']       = self.__okft2local_direction(item['position'])
            position['position']        = item['hold_amount']
            position['margin']          = item['bondfreez'] #item['margin']
            position['avgprice']        = item['avgprice']
            
            position['closeprofit']     = item['realized'] #按日结算之后 会有这个
            position['positionprofit']  = 0
            position['fee']             = 0
            position['openvolume']      = item['eveningup'] # 可平仓量
            position['closevolume']     = 0
            position['openamount']      = 0
            position['closeamount']     = 0
            position['contract']        = item['contract_name']
            position['id'] = position['symbol'] + '--' +  position['direction']
            positions[position['id']] = Position(position)
            #logging.info('key: %r,  position: %r', key, item)
        #持仓也用key---value模式
        self.getQueue().append((DateType.ON_ACCOUNT_POSITION, self.__echname, positions))
    
    def subcribe(self, socket):
        pass
        #订阅账户order
        socket.subcribe('ok_sub_futureusd_trades')
        socket.onchannel('ok_sub_futureusd_trades', self.on_account_order)
        #订阅账户权益变动
        socket.subcribe('ok_sub_futureusd_userinfo')
        socket.onchannel('ok_sub_futureusd_userinfo', self.on_account_userinfo)
        #订阅合约持仓信息
        socket.subcribe('ok_sub_futureusd_positions')
        socket.onchannel('ok_sub_futureusd_positions', self.on_account_position)
    
    ############################线程覆盖函数#############################################
    def __local2okft_order_type(self, order_type, offset):
        '''local ---> okex TODO 下单用 1:开多 2:开空 3:平多 4:平空'''
        if order_type == OrderType.Buy:
            if offset == Offset.Open:
                return 1
            elif offset == Offset.Close:
                return 3
            else:
                raise Exception('local offset ' + offset + ' not support.') 
        elif order_type == OrderType.Sell:
            if offset == Offset.Open:
                return 2
            elif offset == Offset.Close:
                return 4
            else:
                raise Exception('local offset ' + offset + ' not support.') 
        else:
            raise Exception('local order_type ' + order_type + ' not support.') 

    def __okft2local_order_type(self, order_type):
        '''local ---> okex'''
        if order_type == 1 or order_type == 3:
            return OrderType.Buy
        elif order_type == 2 or order_type == 4:
            return OrderType.Sell
        else:
            raise Exception('ok order_type ' + order_type + ' not support.') 
    
    def __local2okft_offset(self, offset, system_type=0):
        if offset == 1 or offset == 2:
            return Offset.Open
        elif offset == 3 or offset == 4:
            if system_type == 2:
                return Offset.Force
            elif system_type == 1:
                return Offset.Settlement
            else:
                return Offset.Close
        else:
            raise Exception('okft offset ' + offset + ' not support.') 

    def __okft2local_direction(self, direction):
        if direction == 1:
            return Direction.Long
        elif direction == 2:
            return Direction.Short
        else:
            raise Exception('okft direction ' + direction + ' not support.') 

    def __order_status(self, order_status):
        ''' okex ----> local
            0等待成交 1部分成交 2全部成交 -1撤单 4撤单处理中
        '''
        if order_status == -1:
            return OrderStatus.CANCELD
        elif order_status == 0:
            return OrderStatus.SUBMITED 
        elif order_status == 1:
            return OrderStatus.TRADEDPART
        elif order_status == 2:
            return OrderStatus.TRADED
        elif order_status == 4:
            return OrderStatus.SUBMITED
        else:
            raise Exception('okexft order_status ' + order_status + ' not support.')
    
    ############################对应livebroker接口##############################################
    def getOpenOrders(self):
        '''
            :程序启动的时候获取所有的打开的订单
        '''
        #查询所有打开的order 根据订阅列表 TODO
        orders = []
        for item in self.getchannels():
            if item[1] == 'index': continue
            symbol = item[0]+'_usd'
            contract_type = item[1]
            jsonResponse = self.future_order_info(symbol, contract_type, '-1')
            if not jsonResponse : 
                raise Exception('query orders fail.')
            if 'result' not in jsonResponse.keys() or jsonResponse['result']!=True:
                if jsonResponse['error_code'] == 1007: continue #没有这个市场的订单
                raise Exception('query orders false symbol: %s %s, resp:%s' %(symbol, contract_type,  json.dumps(jsonResponse)))
           
            def func(data) :
                order = {}
                order['order_id']   = self.__echname + '--' + str(data['order_id'])
                order['status']     = self.__order_status(data['status'])
                order['symbol']     = self.ok2ft(symbol, contract_type)
                order['order_type'] = self.__okft2local_order_type(data['type'])
                order['offset']     = self.__local2okft_offset(data['type'])
                order['price_type'] = PriceType.Limit
                order['price']      = data['price']
                order['amount']     = data['amount']
                order['deal_amount']= data['deal_amount']
                order['avg_price']  = data['price_avg']
                order['fee']        = data['fee']
                order['datetime']   = datetime.datetime.utcfromtimestamp(int(data['create_date'])/1000)
                order['contract']   = data['contract_name']
                order['lever_rate'] = data['lever_rate']
                return Order(order)
            orders += [func(order) for order in jsonResponse['orders']]
            for o in jsonResponse['orders'] : self.__orders[o['order_id']] = o
        return orders    

    def getAccountBalance(self, symbol=None):
        '''
            程序启动的时候获取权益
        '''
        jsonResponse =  self.future_userinfo()
        if not jsonResponse : return None
        if not jsonResponse['result'] or not jsonResponse['result'] : return None
        #logging.info(jsonResponse)

        info = jsonResponse['info'] 
        balance = {}
        for key in info.keys():
            if(info[key]['account_rights'] < 0.00000001) : continue 
            b = {}
            b['currency']   = key.upper()
            b['free']       = info[key]['account_rights'] - info[key]['keep_deposit']
            b['margin']     = info[key]['keep_deposit']
            b['freezed']    = 0
            b['fee']        = 0
            
            
            b['closeprofit']    = info[key]['profit_real'] 
            b['positionprofit'] = info[key]['profit_unreal']
            b['risk_rate'] = info[key]['risk_rate']
            b['datetime']      = datetime.datetime.utcnow()
            logging.info('currency : %r,  free : %r,  freezed : %r', key, b['free'], b['margin'])
            balance[self.__echname + '--' + key.upper()] = AccountBalance(b)
        return balance

    def get_positions(self):
        positions = {}
        for item in self.getchannels():
            if item[1] == 'index': continue
            symbol = item[0]+'_usd'
            contract_type = item[1]
            jsonResponse = self.future_position(symbol, contract_type)
            
            logging.info(jsonResponse)
            
            if not jsonResponse : 
                raise Exception('query positions fail.')
            if 'result' not in jsonResponse.keys() or jsonResponse['result']!=True:
                if jsonResponse['error_code'] == 1007: continue #没有这个市场的订单
                raise Exception('query positions false symbol: %s %s, resp:%s' %(symbol, contract_type,  json.dumps(jsonResponse)))

            for p in jsonResponse['holding']:
                symbol = self.ok2ft(p['symbol'], p['contract_type'])
                self.__channel_instrument[symbol] = p['contract_id']
                self.__channel_instrument[p['contract_id']] = symbol
                if(p['buy_amount'] > 0): #多仓
                    position = {}
                    position['symbol']          = symbol
                    position['direction']       = Direction.Long 
                    position['position']        = p['buy_amount']
                    position['margin']          = 0 
                    position['avgprice']        = p['buy_price_avg']
                    
                    position['closeprofit']     = p['buy_profit_real']
                    position['positionprofit']  = 0
                    position['fee']             = 0
                    position['openvolume']      = p['buy_available'] # 可平仓量
                    position['closevolume']     = 0
                    position['openamount']      = 0
                    position['closeamount']     = 0
                    position['datetime']        = datetime.datetime.utcfromtimestamp(int(p['create_date'])/1000)
                    position['lever_rate']      = p['lever_rate']
                    position['contract']        = p['contract_id']
                    position['id']              = position['symbol'] + '--' + position['direction']
                    positions[position['id']] = Position(position)
                if(p['sell_amount'] > 0): #空仓
                    position = {}
                    position['symbol']          = symbol
                    position['direction']       = Direction.Short 
                    position['position']        = p['sell_amount']
                    position['margin']          = 0 
                    position['avgprice']        = p['sell_price_avg']
                    
                    position['closeprofit']     = p['sell_profit_real']
                    position['positionprofit']  = 0
                    position['fee']             = 0
                    position['openvolume']      = p['sell_available'] # 可平仓量
                    position['closevolume']     = 0
                    position['openamount']      = 0
                    position['closeamount']     = 0
                    position['datetime']        = datetime.datetime.utcfromtimestamp(int(p['create_date'])/1000)
                    position['lever_rate']      = p['lever_rate']
                    position['contract']        = p['contract_id']
                    position['id']              = position['symbol'] + '--' + position['direction']
                    positions[position['id']] = Position(position)
            time.sleep(0.2)
        return positions    

    def submitOrder(self, symbol, order_type, price_type, limit_price, order_quantity):
        ''' TODO
            submitOrder(order.getInstrument(), ordertype,  PriceType.Limit, order.getLimitPrice(), order.getLimitPrice(),  order.getQuantity())
            {"result":true,"order_id":123456}

        '''
        symbol, contract_type = self.ft2ok(symbol)
        
        #下单量为负表示平仓
        offset = Offset.Close 
        if (order_quantity > 0): offset = Offset.Open

        match_price = 0
        if(price_type == PriceType.Market) : match_price = 1
        
        _type = self.__local2okft_order_type(order_type, offset)
        
        #symbol, contract_type, tradetype, price, amount, match_price=0):
        #1:开多 2:开空 3:平多 4:平空 tradetype    match_price 0 现价单 1市价单)
        jsonResponse = self.future_trade(symbol+'_usd', contract_type, _type, limit_price, order_quantity, match_price)
        
        if(not jsonResponse): return None
        if(not jsonResponse.get('result') or jsonResponse['result']!=True):
            logging.info('addorder fail:%r  %r', symbol, jsonResponse)
            return None

        jsonResponse['order_id'] = self.__echname + '--' + str(jsonResponse['order_id'])
        jsonResponse['order_type']     = order_type 
        jsonResponse['price']    = limit_price
        jsonResponse['amount']   = order_quantity
        jsonResponse['datetime'] = datetime.datetime.utcnow() 
        jsonResponse['symbol']   = symbol
        jsonResponse['deal_amount']= 0
        jsonResponse['status']  = OrderStatus.SUBMITED
        jsonResponse['offset']  = offset
        jsonResponse['price_type'] = price_type

        return Order(jsonResponse)
   

    def cancelOrder(self, symbol, orderid): 
        '''
            统一接口则一次都只取消一个订单
            orderid: 订单ID(多个订单ID中间以","分隔,一次最多允许撤消3个订单)
            return : {"success":"123456,123457","error":"123458,123459"}
        '''
        symbol, contract_type = self.ft2ok(symbol)
        logging.info('cancle symbol:%r, orderid:%r', symbol, orderid)

        jsonResponse = self.future_cancel(symbol+'_usd', contract_type, str(orderid))
        if(not jsonResponse): 
            return False
        #下单失败返回处理
        return True
    
    ############################对应livebroker接口##############################################
  

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')
    url      = "https://www.okex.com/api/v1"
    wss      = 'wss://real.okex.com:10440/websocket/okexapi'
    apikey    = 'db98cb7e-71c4-442d-bf45-8c6ab05a4c1c'
    apisecret = '4A5F6437B9DE1A2B16E80FC0018C8515'

    channels = ['OKEXFT--BTC--TW', 'OKEXFT--BTC--NW', 'OKEXFT--BTC--TQ', 'OKEXFT--BTC--ZS']
    #channels = ['OKEXFT--BTC--TW']
    ws = OkexftHttpThread(url, wss, channels, apikey, apisecret);
    ws.start()
    while True:
        logging.info('main thread run.')
        time.sleep(3)
    

