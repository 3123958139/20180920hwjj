# -*- coding: utf-8 -*-

from struct import *

class SymbolRound:
    def __init__(self, bit):
        if not bit : 
            bit = 8
        self.__bit = bit

    def round(self, quantity):
        return round(quantity, self.__bit)

#插件在这里管理
class Broker(object):
    '''order position account done管理'''
    def __init__(self, group):
        # 组名对应一组时序相同产品(交易所)
        self.__group_name = group
        # 打开的order 
        self.__orders = {}
        # 账户权益
        self.__balances = {}
        # 持仓
        self.__positions = {}
        #成交
        self.__trades = {}
        self.__symbol_round = {}
        
    def register(self, symbols, bits={}):
        for symbol in symbols:
            self.__symbol_round[symbol] = SymbolRound(bits.get(symbol))

    def round(symbol, equity):
        if self.__symbol_round.get(symbol) :
            return self.__symbol_round[symbol].round(equity)
        return equity

    def open_orders(self):
        return [self.__orders[oid] for oid in self.__orders if self.__orders[oid].status()!=OrderStatus.TRADED] 

    def orders(self):
        return self.__orders

    def positions(self):
        return self.__positions

    def trades(self):
        self.__trades

    def balances(self):
        return self.__balances

    def onorder(self, data, callback):
        self.__orders[data.id()] = data
        callback(self, self.__group_name, self.__orders[data.id()])
        if (data.status() == OrderStatus.CANCELD or
            data.status() == OrderStatus.TRADED):
            self.__orders.pop(data.id())

    def onposition(self, data, callback):
        '''持仓以字典的形式全量更新过来'''
        self.__positions.update(data)
        callback(self, self.__group_name, self.__positions)
         
    def ontrade(self, data, callback):
        self.__trades[data.id()] = data
        callback(self, self.__group_name, data)

    def onbalance(self, data, callback):
        '''持仓以字典的形式更新过来'''
        self.__balances.update(data)
        callback(self, self.__group_name, self.__balances)

    def clear(self):
        '''清理过期的order done等。 或者结算清理'''
        self.__trades.clear()
        for order in list(self.__orders.keys()):
            if (self.__orders[order].status() == OrderStatus.CANCELD or
                self.__orders[order].status() == OrderStatus.TRADED):
                self.__orders.pop(order)
        for position in list(self.__positions.keys()):
            p = self.__positions[position].position()
            if p < MINNUM : 
                self.__positions.pop(position)
        for balance in list(self.__balances.keys()):
            if self.__balances[balance].balance() < MINNUM :
                self.__balances.pop(balance)
       









