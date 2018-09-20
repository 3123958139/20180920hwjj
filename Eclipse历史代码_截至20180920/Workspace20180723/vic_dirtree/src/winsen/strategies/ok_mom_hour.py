# -*- coding: utf-8 -*-

"""
# anaconda
    time
    logging
    sys
    numpy
    Queue
    talib
# winsen
    winsen.algorithm
    winsen.common
    winsen.config
# vic
    vic.core
    vic.exchange
# vics
    vics.lib 
"""

from time import clock
import logging
import sys
import time

from numpy import abs, array, floor, sum

from algorithm.twap import *
from algorithm.vol import avgVol
from common.fmt import *
from common.initHelper import *
from common.loadData import *
from common.msg import *
from common.posManager import *
from common.signal import *
from common.tradeHelper import *
from config.account import *
from config.portfolio import UNIT_AMOUNT
from vic.core.livebroker import Broker
from vic.core.livefeed import Feed
from vic.core.strategy import StrategyBase
from vic.core.struct import Bar, DateType, OrderStatus, OrderType
from vic.exchange.vic_binance.binance_http_thread import BinaHttpThread
from vic.exchange.vic_binance.binance_ws_thread import BinaWsThread
from vic.exchange.vic_huobi.huobi_http_thread import HuobiHttpThread
from vic.exchange.vic_huobi.huobi_ws_thread import HuobiWsThread
from vic.exchange.vic_okex.okex_http_thread import OkexHttpThread
from vic.exchange.vic_okex.okex_ws_thread import OkexWsThread
from vic.exchange.vic_okex.okexft_http import OkexftHttp
from vic.exchange.vic_okex.okexft_http_thread import OkexftHttpThread
from vic.exchange.vic_okex.okexft_ws_thread import OkexftWsThread
from vics.lib.mysql_pool import MysqlPool
import Queue
import talib


sys.path.append("..")

http = OkexftHttp(HTTP_OKEXFT, APIKEY_OKEXFT, APISECRET_OKEXFT)

"""
__init__
onstart

onend
"""
class MOMENTUM(StrategyBase):
    def __init__(self, queue):
        super(MOMENTUM, self).__init__(queue)
        self.startDate  = "2018-06-01 00:00:00"
        self.db = "positions"
        self.fund = "test"
        self.trend = "BW1StrategyHolding"
        self.slippageTable = "BW1TradingRecords"
        self.strategyName = "OK_MOM_HOUR"
        self.period = "1h"
        self.parmsType = "None"
        self.algorithm = "TWAP"
        
        #������ֵ�Ժ󳷵�
        self.slippageMax = 0.02
        self.orderFlag = False
        self.RMALen  = 12
        self.longSignal  = False
        self.shortSiganl = False
        self.strategyInitTag = False
        self.__loadingTag = False
        self.dbPos = None
        self.signalPos = None
        self.dbPosDict = None
        self.balance = {}
        self.newOrder = None
        self.newOrderID = None
        self.isOrderTag  = None
        self.isFutureOrder = None
        self.orderTest = False
        self.firstLegFilled = False
        self.lastTradedVolume = None
        self.ask = 0
        self.bid = 0
        self.thisAvgVol = 0
        self.isCompleted = False
        self.amountOnce = 20
        self.version = "V1.1"
        self.productTime = "2018-07-21"
        self.barTime = 0
        self.testQty = 10

    def init(self):
        super(MOMENTUM, self).init()
        self.resample(60*60,  self.onbar)
        #self.resample(60*5,  self.onAlgorithmBar)
        self.newOrderID, self.isOrderTag = initOrder(self.symbols())
        self.dbPos = getStrategyPos(self.db, self.trend)
        self.orderPrc = initDict(self.symbols())
        self.isFutureOrder = initTag(self.symbols())
        self.devolveTag = initTag(self.symbols())
        self.lastTradedVolume = initDict(self.symbols())
        self.isCompleted = initDict(self.symbols())
        self.signalPos   = initSignal(self.symbols())
        self.strategyInitTag = True


    def onorder(self, handle, group, order):
        symbol, abbr, balance_abbr = relateSymbol(group, order)
        #�Ƕ���Ʒ��
        if symbol not in self.signalPos.keys():
            return
        signalPrc = self.signalPos[symbol]["signalPrc"][-1]
        orderStatus, orderId, tradedPrc = order.status(), order.id(), order.price()
        dbSymbol = group + "--" + abbr + "--USDT"
        dbQty  = getPosbyExchange(self.strategyName, self.period, self.parmsType, dbSymbol, self.dbPos)

        #�ǲ��Ա�����������
        if orderId not in self.newOrderID[symbol]:
            return

        if orderStatus == OrderStatus.SUBMITED:
            logging.info(SUBMIT_MSG % (self.fund, self.strategyName, self.period, symbol))
            self.orderPrc[symbol] = tradedPrc
            return

        elif orderStatus == OrderStatus.CANCELD:
            logging.info(CANCEL_MSG % (self.fund, self.strategyName, self.period, symbol))
            if orderId in self.newOrderID[symbol]:
                self.newOrderID[symbol].remove(orderId)
                self.isOrderTag[symbol] = False
                if okexCheck(group):
                    spotSymbol, mirrorSymbol = doubleMapSymbol(group, symbol)
                    self.isFutureOrder[spotSymbol] = False
                    self.isFutureOrder[mirrorSymbol] = False
                    self.firstLegFilled = False
                return

        else:
            if orderStatus == OrderStatus.TRADED:
                logging.info(TRADED_MSG % (self.fund, self.strategyName, self.period, symbol))
                volume = order.volume()
                if orderId in self.newOrderID[symbol]:
                    self.newOrderID[symbol].remove(orderId)
            
            #*****���ֳɽ���������ⵥ������            
            elif orderStatus == OrderStatus.TRADEDPART:
                logging.info(PART_FILLED_MSG % (self.fund, self.strategyName, self.period, symbol))
                volume = order.volume() - self.lastTradedVolume[symbol]
                self.lastTradedVolume[symbol] = order.volume()
                
            #convert volume signal by direction
            dbQty, volume = orderQtyConvert(order, dbQty, volume)
            self.signalPos[symbol]["qty"] = round(self.signalPos[symbol]["qty"], QTY_PRECISE)
            
            #sendMsg
            sendTradeMsg(FILLED_MSG % (self.fund, self.strategyName, self.period, symbol, orderSideConvert(order), volume))

            if orderStatus == OrderStatus.TRADED:
                #update mysql databasae
                logging.info("signalPrc:%r tradedPrc:%r volume:%r" % (signalPrc, tradedPrc, volume))
                #logging.info("signalPrc:%r tradedPrc:%r volume:%r, type:%r %r %r" % (signalPrc, tradedPrc, volume, type(signalPrc, type(tradedPrc), type(signalPrc))))
                replaceSlippage(self.strategyName, group, symbol, self.period, self.parmsType, signalPrc, tradedPrc, volume, orderSideConvert(order), self.algorithm, tableName=self.slippageTable, dbName=self.db)
                self.isOrderTag[symbol] = False
                if not okexCheck(group):
                    logging.info(UPDATE_DB_MSG % (self.fund, self.strategyName, self.period, symbol))
                    self.dbPos = updatePosbyExchange(self.strategyName, self.period, self.parmsType, symbol, self.dbPos, volume)
                    replacePos(self.strategyName, group, symbol, self.period, self.parmsType, dbQty, tableName=self.trend, dbName=self.db)
               
                #OKEX--OKEXFT
                if okexCheck(group):  
                    volume = order.volume()
                    futureSymbol = okexFtrSym(abbr)
                    spotSymbol, mirrorSymbol = doubleMapSymbol(group, symbol)
                    if self.isFutureOrder[spotSymbol] and not self.isFutureOrder[mirrorSymbol]:
                        thisAmount = piece2qty(symbol, tradedPrc, volume)
                        if group == OKEX:
                            self.firstLegFilled = True
                            '''��ѯ�ֲ�����Ƿ��㹻'''
                            symbol, abbr, balance_abbr = relateSymbol(group, order)
                            thisBalance = dealBalance(balance_abbr, self.balance)
                            devolveVolume = min(thisBalance, volume)
                            devolveResult = http.future_devolve(futureSymbol, '1', devolveVolume)

                    if self.isFutureOrder[spotSymbol] and self.isFutureOrder[mirrorSymbol]:
                        logging.info("-----update db-----")
                        dbSymbol = group + "--" + abbr + "--USDT"
                        logging.info("dbQty:%r" % (dbQty))
                        logging.info("dbPos:%r" % self.dbPos)

                        self.dbPos = updatePosbyExchange(self.strategyName, self.period, self.parmsType, dbSymbol, self.dbPos, volume)
                        dbQty, volume = orderQtyConvert(order, dbQty, volume)

                        replacePos(self.strategyName, group, dbSymbol, self.period, self.parmsType, dbQty, tableName=self.trend, dbName=self.db)
                        dbQty, volume = orderQtyConvert(order, dbQty, volume)
                        self.isFutureOrder[spotSymbol] = False
                        self.isFutureOrder[mirrorSymbol] = False
                        self.firstLegFilled = False
                        #logging.info("======================dbPos:%r" % (self.dbPos))

                print("\n")
                    
    def onbalance(self, handle, group, balance):
        self.balance.update(balance)
    
    def onorderbook(self, handle, group, data):
        if self.dbPos is None:
            sendTradeMsg(DB_POS_ERR_MSG % (self.fund, self.strategyName))
            return
        if not self.strategyInitTag:
            return

        self.ask, self.bid, spread = mySpread(data)
        symbol, abbr, balance_abbr = relateSymbol(group, data)
        thisBalance = dealBalance(balance_abbr, self.balance)
        okexFutureOrder = False
        
        cash = usdtCash(group, self.balance) 
        thisSignalQty = transferSiganlQty(group, symbol, self.signalPos)      
        #dbQty  = getPosbyExchange(self.strategyName, self.period, self.parmsType, symbol, self.dbPos)
        #minQty       = round(self.amountOnce / self.ask, 1)
        #thisOrderQty = min(minQty, abs(thisSignalQty - dbQty))

        if okexCheck(group):
            spotSymbol,  mirrorSymbol = doubleMapSymbol(group, symbol)
        
        #δ�鵽�����źţ����������߼��ж�
        if symbol not in self.signalPos.keys(): 
            logging.info(NOT_IN_SIGANL % (self.strategyName, self.period, symbol))
            return
        else:
            #����δ�ɽ���ʱ�����ҵ�
            if self.isOrderTag[symbol]:
                return

            #----------------------------------------------------------------------
            orderResult = False
            dbSymbol = group + "--" + abbr + "--USDT"
            dbQty  = getPosbyExchange(self.strategyName, self.period, self.parmsType, dbSymbol, self.dbPos)
            minQty       = round(self.amountOnce / self.ask, QTY_PRECISE)
            thisOrderQty = min(minQty, abs(thisSignalQty - dbQty))
            thisOrderQty = round(thisOrderQty, QTY_PRECISE)
            thisOrderAmount = thisOrderQty*self.bid
            if thisOrderAmount <= 10:
                return

            if thisSignalQty >= 0:
                self.isOrderTag[symbol] = True
                if thisSignalQty < dbQty:
                    '''====�������===='''
                    if thisBalance > thisOrderQty:
                        orderResult = self.sell_limit(symbol, self.bid, thisOrderQty)
                    elif thisBalance > 0:
                        orderResult = self.sell_limit(symbol, self.bid, thisBalance)
                    elif thisBalance == 0:
                        logging.info(NOT_ENOUGH_MSG % (self.fund, self.strategyName, symbol))
                        sendTradeMsg(NOT_ENOUGH_MSG % (self.fund, self.strategyName, symbol))
                        self.isOrderTag[symbol] = False
                       # return

                elif thisSignalQty > dbQty and dbQty >= 0:
                    '''====���Ӳ�===='''
                    if cash > thisOrderQty * self.bid: 
                        orderResult = self.buy_limit(symbol, self.ask, thisOrderQty)
                    else:
                        self.isOrderTag[symbol] = False
                        sendTradeMsg(NOT_ENOUGH_USDT_MSG % (self.fund, self.strategyName, group))
                        logging.info(NOT_ENOUGH_USDT_MSG % (self.fund, self.strategyName, group))
                       # return

                elif dbQty < 0:
                    '''====���HB��BA���֣�OKEX����ƽ��===='''
                    if okexCheck(group):
                        mirrorSymbol = mapSymbol(group, symbol)
                        thisPiece    = qty2piece(mirrorSymbol, self.ask, thisOrderQty)
                        futureSymbol = okexFtrSym(abbr)
                        logging.info("======futureSymbol:%s" % futureSymbol) 
                        #�����һ���µ��������µ����ɼ���
                        if self.isFutureOrder[mirrorSymbol] and group == OKEXFT:
                            #��Լ����
                            futureHoldingQty = futureHolding(http, futureSymbol)
                            thisOrderPiece   = min(thisPiece, futureHolingQty-thisPiece)
                            orderResult      = self.buy_limit(symbol, self.ask, -thisPiece) 

                        if self.isFutureOrder[mirrorSymbol] and group == OKEX:
                            if self.isFutureOrder[symbol]:
                                #ƽ��:ת��֮ǰȷ�����
                                orderResult = self.sell_limit(symbol, self.bid, thisOrderQty)
                    else:
                        orderResult = self.sell_limit(symbol, self.bid, thisOrderQty)

            #----------------------------------------------------------------------
           

            #----------------------------------------------------------------------
            if thisSignalQty < 0:
                futureSymbol = okexFtrSym(abbr)
                if okexCheck(group):
                    spotSymbol, mirrorSymbol = doubleMapSymbol(group, symbol)
                    thisPiece = qty2piece(mirrorSymbol, self.ask, thisOrderQty)
                    futureHoldingQty = futureHolding(http, futureSymbol)
                    thisOrderPiece = abs(min(thisPiece, futureHoldingQty - thisPiece))

                if thisSignalQty < dbQty and dbQty <= 0:
                    '''====�������ּӲ�OKEXFT===='''
                    if okexCheck(group):
                        spotSymbol, mirrorSymbol = doubleMapSymbol(group, symbol)

                        if not self.isFutureOrder[mirrorSymbol] and self.isFutureOrder[spotSymbol] and group == OKEXFT and self.firstLegFilled: 
                            if thisBalance >= thisOrderQty * MARGINRATIO:
                                orderResult = self.sell_limit(mirrorSymbol, self.bid, thisOrderPiece)
                                okexFutureOrder = True
                            else:
                                logging.info(NOT_ENOUGH_MARGIN % (self.fund, self.strategyName, self.period, mirrorSymbol))
                                sendTradeMsg(NOT_ENOUGH_MARGIN % (self.fund, self.strategyName, self.period, mirrorSymbol))

                        if not self.isFutureOrder[spotSymbol] and not self.isFutureOrder[mirrorSymbol] and group == OKEX and not self.firstLegFilled:
                            #ƽ��:ת��֮ǰȷ�����
                            orderResult = self.buy_limit(spotSymbol, self.ask, thisOrderQty)
                            okexFutureOrder = True
                    else:
                        #�Ұ������������
                        orderResult = self.buy_limit(symbol, self.ask, thisOrderQty) 

                elif thisSignalQty > dbQty:
                    '''====����ƽOKEX����===='''
                    if okexCheck(group):
                        if not self.isFutureOrder[mirrorSymbol] and not self.isFutureOrder[spotSymbol] and group == OKEXFT and not self.firstLegFilled: 
                            orderResult = self.buy_limit(mirrorSymbol, self.ask, -thisOrderPiece) 
                            okexFutureOrder = True

                        if not self.isFutureOrder[spotSymbol] and self.isFutureOrder[mirrorSymbol] and group == OKEX and self.firstLegFilled:
                            orderResult = self.sell_limit(spotSymbol, self.bid, thisOrderQty)
                            okexFutureOrder = True

                elif dbQty > 0:
                    '''====����ƽ��OKEX�����뿪��HB BA===='''
                    if okexCheck(group):
                        if not self.isFutureOrder[mirrorSymbol] and not self.isFutureOrder[spotSymbol] and group == OKEXFT and not self.firstLegFilled: 
                            orderResult = self.buy_limit(mirrorSymbol, self.ask, -thisOrderPiece) 
                            okexFutureOrder = True

                        if self.isFutureOrder[mirrorSymbol] and not self.isFutureOrder[spotSymbol] and group == OKEX and self.firstLegFilled:
                            orderResult = self.sell_limit(spotSymbol, self.bid, thisOrderQty)
                            okexFutureOrder = True

                    if cash > thisOrderQty * self.bid: 
                        orderResult = self.buy_limit(symbol, self.ask, thisOrderQty)
                    else:
                        logging.info(NOT_ENOUGH_MSG % (self.fund,  self.strategyName, symbol))
                        sendTradeMsg(NOT_ENOUGH_MSG % (self.fund,  self.strategyName, symbol))
            #----------------------------------------------------------------------
            
            #�µ��������
            if not orderResult:
                self.isOrderTag[symbol] = False
                okexFutureOrder = False
                return
            else:
                orderid = orderResult.id()
                self.newOrderID[symbol].append(orderid)
                if okexCheck(group) and okexFutureOrder:
                    self.isFutureOrder[symbol] = True

    def onticker(self, handle, group, ticker):
        #���������߼�
        #�۸�ƫ��̫���򳷵����¹�
        #algorithm update order volume
        return 
        sym = ticker.symbol()
        if self.isCompleted[sym]:
            if self.algorithm == "TWAP":
                if len(bar["close"]) > 20:
                    #self.prc = twap(bar)
                    #print(twap(bar), bar['close'][-1])
                    pass
            elif self.algorithm == "VWAP":
                pass
            elif self.algorithm == "PoV":
                pass
            elif self.algorithm == "IS":
                pass
    
    def onAlgorithmBar(self, handle, group, period, bar):
        #average volume
        self.thisAvgVol = avgVol(bar, maxLen=12)


    def onbar(self, handle, group, period, bar):
        """
        """
        time   = timestamp2str(bar["timestamp"][-1])
        symbol = bar["symbol"][-1]
        if len(bar["close"]) < self.RMALen:
            return
        
        RMA = talib.MA(array(bar["close"]), self.RMALen)
        close = bar["close"]
        DRD   = RMA[-self.RMALen:] - close[-self.RMALen:]
        NDV   = sum(DRD)
        TDV   = sum(abs(DRD))
        RDV = 100 * NDV / TDV
        
        symbol = bar["symbol"][-1]
        abbr   = symbol.split("--")[1]
        time   = timestamp2str(bar["timestamp"][-1])
        groupTmp  = groupConvert(group)

        if time <> self.barTime:
            logging.info(STRATEGY_ALIVE_MSG % (self.fund, self.strategyName, self.period))
            self.barTime = time
        if abbr in UNIT_AMOUNT[groupTmp].keys():
            thisAmount = UNIT_AMOUNT[groupTmp][abbr]
        else:
            logging.info(NOT_IN_CAPITAL_MSG % (self.fund, self.strategyName, self.period, symbol))
            return
        
        lastClose = bar["close"][-1]
        if RDV > 0:
            qty = round(thisAmount / lastClose, QTY_PRECISE)
            qty = self.testQty 
            if symbol in self.signalPos.keys():
                if self.signalPos[symbol]["qty"] <= 0:
                    if group <> OKEXFT:
                        updateSignalPos(self.signalPos, symbol, qty, close, "long")


        elif RDV < 0:
            qty = round(thisAmount / lastClose, QTY_PRECISE)
            if symbol in self.signalPos.keys():
                if self.signalPos[symbol]["qty"] >= 0:
                    if group <> OKEXFT:
                        #Binance Huobi�ұ�ֻ����
                        updateSignalPos(self.signalPos, symbol, 0,   close, "long")

        
    def onstart(self):
        logging.info(START_LOAD_DATA % (self.fund, self.strategyName, self.period))
        datas = loadData(self.period, self.startDate)
        timestamp = 0
        for data in datas:
            group = data['symbol'].split('--')[0]
            if not self.check(group, data['symbol']): 
                continue
            data['period'] = 60
            data['timestamp'] = data['timestamp']*1000 
            self.get_deque().appendleft((DateType.ON_MKT_KLINE, group, Bar(data)))
            if(timestamp and timestamp < data['timestamp']): 
                self.get_deque().appendleft((DateType.ON_TIMESTAMP, group, {'timestamp': timestamp}))
            timestamp = data['timestamp']
        logging.info(LOAD_DATA_OK % (self.fund, self.strategyName, self.period))
        self.__loadingTag = True
        sendTradeMsg(INIT_MSG % (self.fund, self.strategyName, self.period, self.symbols()))

    def onend(self):
        """
        CTRL+C ��ֹ����
        """
        try:
            loop = 1
            while loop < 5:
                loop += 1
                if self.newOrderID:
                    for sym, orderId in self.newOrderID.items():
                        cancelResult = self.cancle_order(orderId, sym)
                        logging.info("cancel result:%r" % cancelResult)
                        logging.info(CANCEL_ORDER_MSG % (self.fund, self.strategyName, self.period, orderId, sym))
                        if cancelResult:
                            self.newOrderID.pop(sym)

                if not self.newOrderID:
                    logging.info(END_MSG % (self.fund, self.strategyName, self.period, self.symbols()))
                    sendTradeMsg(END_MSG % (self.fund, self.strategyName, self.period, self.symbols()))
                    break
        except:
            logging.info(END_MSG % (self.fund, self.strategyName, self.period, self.symbols()))
            sendTradeMsg(END_MSG % (self.fund, self.strategyName, self.period, self.symbols()))



if __name__ == "__main__":
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(asctime)s[%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s')

    queue = Queue.deque()
    strategy = MOMENTUM(queue)

    channels = ["OKEX--EOS--USDT"]
    okexws      = OkexWsThread(WSS_OKEX, channels, None, None, queue, 'OKEX')
    okexhttp    = OkexHttpThread(HTTP_OKEX, WSS_OKEX, channels, APIKEY_OKEX, APISECRET_OKEX, queue, 'OKEX')
    strategy.set_handle_thread(type=MOMENTUM.MARKET, group='OKEX', plugin=okexws, maxlen=300)
    strategy.set_handle_thread(type=MOMENTUM.TRADE,  group='OKEX', plugin=okexhttp, bit={})
   
    #channels = ["HUOBI--EOS--USDT","HUOBI--XRP--USDT", "HUOBI--BTC--USDT", "HUOBI--ETH--USDT", "HUOBI--BCH--USDT", "HUOBI--LTC--USDT"]
    #channels = ["HUOBI--BCH--USDT"]
    #huobiws      = HuobiWsThread(WSS_HUOBI, channels, None, None, queue, 'HUOBI')
    #huobihttp    = HuobiHttpThread(HTTP_HUOBI, WSS_HUOBI, channels, APIKEY_HUOBI, APISECRET_HUOBI, queue, 'HUOBI')
    #strategy.set_handle_thread(type=MOMENTUM.MARKET, group='HUOBI', plugin=huobiws, maxlen=300)
    #strategy.set_handle_thread(type=MOMENTUM.TRADE,  group='HUOBI', plugin=huobihttp, bit={})


    #channels = ["BINA--BTC--USDT", "BINA--ETH--USDT", "BINA--XRP--USDT", "BINA--BCC--USDT", "BINA--LTC--USDT"]
    #binaws    = BinaWsThread(WSS_BINA, channels, None, None, queue, 'BINA')
    #binahttp  = BinaHttpThread(HTTP_BINA, WSS_BINA, channels, APIKEY_BINA, APISECRET_BINA, queue, 'BINA')
    #strategy.set_handle_thread(type=MOMENTUM.MARKET, group='BINA', plugin=binaws, maxlen=300)
    #strategy.set_handle_thread(type=MOMENTUM.TRADE,  group='BINA', plugin=binahttp, bit={})
    strategy.run()

