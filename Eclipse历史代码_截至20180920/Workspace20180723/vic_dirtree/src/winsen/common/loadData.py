# -*- coding: utf-8 -*-

from vics.lib.mysql_pool import MysqlPool

def loadData(period="1mk", start="2018-05-09"):
    """
    查询数据库历史行情数据
    dbName: 数据库名称，用于指定加载历史数据的周期，如1mk 5mk etc.
    start:字符型日期格式，""
    dbName: ticker, 1mk, 5mk, 1d
    exchange:OKEX OKEXFT HUOBI BINA
    """
    dbName = "vic_" + period + "." + period
    mysql = MysqlPool('47.74.179.216', 3308, 'ops', 'ops!@#9988', 'vic', 'utf8')
    sql = 'select symbol, unix_timestamp(ts) as timestamp, high, low, open, close, quantity as volume, turnover as amount, openinterest  from %s where ts > "%s";' % (dbName, start) 
    datas = mysql.getAll(sql)
    datas = list(datas)
    #datas["timestamp"]=[x+8 for x in datas["timestamp"]]
    datas.reverse()
    mysql.dispose()
    return datas


if __name__ == "__main__":
    d = loadData(period="1h", start="2018-05-12")
    print(d)
