# virtual currency database

## 数据库说明 
```
vic                 : 基本信息      
vic_1d.1d           : 日k
vic_1h.1h           : 1小时k
vic_1mk.1mk         : 1分k
vic_5mk.5mk         : 5分k
vic_ticker.ticker   : 成交
```

## 数据库字段
```
mysql> select * from vic_1mk.1mk where ts>'2018-04-11' limit 1\G;    
*************************** 1. row ***************************
          ts: 2018-04-11 00:01:00       #时间
      symbol: OKEX--BCH--BTC            #符号
        open: 0.09491044                #开盘价
        high: 0.09491044                #最高价
         low: 0.09491044                #最低价
       close: 0.09491044                #收盘价
    quantity: 1.846                     #成交量
    turnover: 0                         #成交额
openinterest: 0                         #持仓量 期货用


mysql> select * from vic_ticker.ticker where ts>'2018-04-11' limit 1\G
*************************** 1. row ***************************
      ts: 2018-04-11 00:00:04           #时间戳 
  symbol: OKEX--ETH--USDT               #符号 
   price: 415.45                        #成交价格 
quantity: 0.07221                       #成交量 
    type: 1                             #1:买方成交 2:卖方成交
 tradeid: 168784381                     #对应合约交易所

```




