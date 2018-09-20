# *- coding:utf-8 -*-

#author: winsen.HUANG
#purpose: maintain the positions to sql db
#time: 2018-05-10
#Wechat:winsentess

import logging
from vics.lib.mysql_pool import *
from datetime import datetime

#HOST = '47.74.179.216'
HOST = '47.74.249.179'
PORT = 3308
USER = 'ops'
PWD  = 'ops!@#9988'
DB   = 'test'

mysql = MysqlPool(HOST, PORT, USER, PWD, DB, 'utf8')


def getPosbyExchange(strategy="", period="", parms="", symbol="", posDict=None):
    """
    单策略的交易所的品种持仓
    """
    exchange = symbol.split("--")[0]
    #sym = symbol.split("--")[1]
    sym = symbol
    if posDict is None:
        return None
    else:
        for d in posDict:
            if d["strategyID"]==strategy and d["exchange"]==exchange and d["period"]==period and d["parmsGroup"]==parms and d["symbol"]==sym:
                return d["qty"]
                break
        return 0

def updatePosbyExchange(strategy="", period="", parms="", symbol="", posDict=None, tradedVolume=0):
    """
    更新品种持仓
    """
    findingTag = False
    exchange = symbol.split("--")[0]
    sym = symbol
    if posDict is None:
        return None
    else:
        for d in posDict:
            if d["strategyID"]==strategy and d["exchange"]==exchange and d["period"]==period and d["parmsGroup"]==parms and d["symbol"]==sym:
                d["qty"] = d["qty"] + tradedVolume
                findingTag = True
    if not findingTag:
        tmp = {}
        tmp["strategyID"] = strategy
        tmp["exchange"]   = exchange
        tmp["period"]     = period
        tmp["parmsGroup"] = parms
        tmp["symbol"]     = sym
        tmp["qty"]        = tradedVolume
        posDict.append(tmp)

    return posDict



def getStrategyPos(dbName="positions", fundName="BW1Trend"):
    """
    get the strategy positions of the mysql database
    """
    try:
        sql = "select distinct * from " + dbName + "." + fundName
        myPos = mysql.getAll(sql)
        if not myPos:
            return {} 
        else:
            return list(myPos)
    except Exception as e:
        logging.info("load the strategy pos failed:%s" % e)
        return None

def mySet(myTuple, key=""):
    """
    purpose:去重
    """
    rtn = []
    for d in myTuple:
        if d[key] not in rtn:
            rtn.append(d[key])
    return rtn


def getSetByKey(key="", dbName="positions", fundName="BWAssetFundNo1"):
    """
    """
    sql     = "select " + key + " from " + dbName + "." + fundName 
    dataSet = mySet(mysql.getAll(sql), key)
    return dataSet

def updatePos(strategyID, exchange, symbol, period, parmsGroup, qty, fundName="BWAssetFundNo1", dbName="positions"):
    """
    """
    mysql = MysqlPool(HOST, PORT, USER, PWD, DB, 'utf8')
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """update %s.%s 
                set qty=%s,updateTime='%s' 
                where strategyID='%s'
                  and exchange='%s'
                  and symbol='%s'
                  and period='%s'
                  and parmsGroup='%s';""" 
    sql = sql  % (dbName, fundName, qty, dt, strategyID, exchange, symbol, period, parmsGroup) 
    update_count = mysql.update(sql)
    print("update_count:%s" % update_count)
    if update_count == 0:
        sql = "insert into " + dbName + "." + fundName + "(strategyID, exchange, symbol, period, parmsGroup, qty, updateTime) values('%s', '%s', '%s', '%s', '%s', '%s', '%s');"
        record = (strategyID, exchange, symbol, period, parmsGroup, qty, dt) 
        mysql.insertOne(sql, record)
    mysql.dispose()

def replacePos(strategyID, exchange, symbol, period, parmsGroup, qty, tableName="BW1StrategyHolding", dbName="positions"):
    """
    """
    try:
        sql = "REPLACE INTO " + dbName + "." + tableName + "(strategyID, exchange, symbol, period, parmsGroup, qty, updateTime) values('%s', '%s', '%s', '%s', '%s','%f', '%s');"
        mysql = MysqlPool(HOST, PORT, USER, PWD, DB, 'utf8')
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = (strategyID, exchange, symbol, period, parmsGroup, qty, dt) 
        
        conn = MySQLdb.connect(host=HOST,port=PORT, user=USER,passwd=PWD)
        cur = conn.cursor()
        cur.execute(sql % record)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("replacePos Error %r" % e)

def replaceSlippage(strategyID, exchange, symbol, period, parmsGroup, signalPrc, tradedPrc, tradedQty, isbuy, algorithm, tableName="BW1TradingRecords", dbName="positions"):
    """
    """
    try:
        sql = "REPLACE INTO " + dbName + "." + tableName + "(strategyID, exchange, symbol, period, parmsGroup, signalPrc, tradedPrc, tradedQty, isbuy, algorithm, updateTime) values('%s', '%s', '%s', '%s', '%s','%f','%f','%f','%s','%s', '%s');"
        mysql = MysqlPool(HOST, PORT, USER, PWD, DB, 'utf8')
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = (strategyID, exchange, symbol, period, parmsGroup, float(signalPrc), float(tradedPrc), float(tradedQty), isbuy, algorithm, dt) 
        
        conn = MySQLdb.connect(host=HOST,port=PORT, user=USER,passwd=PWD)
        cur = conn.cursor()
        cur.execute(sql % record)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("replaceSlippage Error:%r" % e)


def create_position_table(dbName="", tableName=""):
    """
    purpose: save the strategy positions
    """
    conn = MySQLdb.connect(host=HOST,port=PORT, user=USER,passwd=PWD)
    cur = conn.cursor()
    sql = """
          create table %s(strategyID varchar(40),
                          exchange   varchar(20),
                          symbol     varchar(20),
                          period     varchar(20),
                          parmsGroup varchar(20),
                          qty        float,
                          updatetime varchar(20),
                          primary key(strategyID,
                                      exchange,
                                      symbol,
                                      period,
                                      parmsGroup));
                                      """
    conn.select_db("%s" % dbName )
    cur.execute(sql % tableName)
    conn.commit()
    cur.close()
    conn.close()

def create_slippage_table(dbName="", tableName=""):
    """
    purpose: save the traded record for slippage analysis later
    """
    conn = MySQLdb.connect(host=HOST, port=PORT, user=USER, passwd=PWD)
    cur = conn.cursor()
    sql = """
          create table %s(strategyID varchar(40),
                          exchange   varchar(20),
                          symbol     varchar(20),
                          period     varchar(20),
                          parmsGroup varchar(20),
                          signalPrc  float,
                          tradedPrc  float,
                          tradedQty  float,
                          isBuy      varchar(10),
                          algorithm  varchar(20),
                          updatetime varchar(20));
                          """
    conn.select_db("%s" % dbName )
    cur.execute(sql % tableName)
    conn.commit()
    cur.close()




def create_db_table(dbName="", tableName=""):
    '''
    purpose: create position database
    table: strategyID, exchange, symbol, period, parmsGroup, qtiy, updatetime
    tableName: using fund name
    '''
    try:
        conn = MySQLdb.connect(host='47.74.179.216',port=3308, user='ops',passwd='ops!@#9988')
        conn = MySQLdb.connect(host=HOST,port=3308, user='ops',passwd='ops!@#9988')
        cur = conn.cursor()
        cur.execute("create database if not exists %s" % dbName)
        conn.select_db("%s" % dbName)
        cur.execute("create table %s(strategyID varchar(20),exchange varchar(20), symbol varchar(20), period varchar(20), parmsGroup varchar(20), qty float , updateTime varchar(20))" % tableName)
        conn.commit()
        cur.close()
        conn.close()
    except MySQLdb.Error as e:
        logging.info("Create database Error %d: %s" % (e.args[0], e.args[1]))


if __name__ == "__main__":
    #create_db_table(dbName="positions", tableName="BWAssetFundNo1")
    #pos = ["BFBG", "BINA", "BTC", "4HOUR", "sensitive", '100']
    #pos = ["BFBG", "BINA", "BTC", "4HOUR", "sensitive", '100']
    #insertPos(pos)
    #mysql = MysqlPool(HOST, PORT, USER, PWD, DB, 'utf8')
    #updatePos("KtnBBands", "HUOBI", "HUOBI--ETH--USDT", "5mk", "notSen", "8888")
    
    #持仓记录
    #create_position_table("positions", "BW1StrategyHolding")
    #create_position_table("positions", "BW1StrategyHolding")

    #滑点记录
    #create_slippage_table("positions", "BW1TradingRecords")
    #replacePos("myKtnBBandss", "HUOBI", "HUOBI--ETH--USDT", "5mk", "notSen", 18888, tableName="BW1StrategyHolding", dbName="positions")

    #查询trend持仓数据
    pos = getStrategyPos(dbName="positions", fundName="BW1StrategyHolding")
    print(pos)

    #print(getPosbyExchange(strategy="KtnBBands", period="5mk", parms="notSen", symbol="OKEX--EOS--USDT", posDict=pos))
    #print("====")
    updated = updatePosbyExchange(strategy="test", period="15mk", parms="notSen", symbol="HUOBI--EOS--USDT", posDict=pos, tradedVolume=3)
    #updated = updatePosbyExchange(strategy="test", period="15mk", parms="notSen", symbol="HUOBI--EOS--USDT", posDict=pos, tradedVolume=3)

    print("====updated====")
    print(updated)

    print("="*20)
    pos = getStrategyPos(dbName="positions", fundName="BW1StrategyHolding")
    print(pos)
    replacePos("AAA", "BBB", "CCC", "day", "notSen", 1, tableName="BW1StrategyHolding", dbName="positions")






