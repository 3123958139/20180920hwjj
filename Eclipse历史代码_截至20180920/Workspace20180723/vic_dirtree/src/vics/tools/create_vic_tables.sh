#!/bin/bash


mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"CREATE DATABASE  IF NOT EXISTS vic_ticker DEFAULT CHARACTER  set utf8;"
mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"CREATE DATABASE  IF NOT EXISTS vic_1mk DEFAULT CHARACTER  set utf8;"
mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"CREATE DATABASE  IF NOT EXISTS vic_5mk DEFAULT CHARACTER  set utf8;"
mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"CREATE DATABASE  IF NOT EXISTS vic_1h DEFAULT CHARACTER  set utf8;"
mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"CREATE DATABASE  IF NOT EXISTS vic_1d DEFAULT CHARACTER  set utf8;"
mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"CREATE DATABASE  IF NOT EXISTS vic DEFAULT CHARACTER  set utf8;"


mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"\
CREATE TABLE IF NOT EXISTS  vic_ticker.ticker (\
    ts          DATETIME  NOT NULL,\
    symbol      varchar(32) NOT NULL COMMENT '合约',\
    tradeid     bigint COMMENT '成交id 单一市场唯一',\
    price       double COMMENT '价格',\
    quantity    double COMMENT '成交量',\
    type        TINYINT unsigned NOT NULL COMMENT '1=BUY 2=SELL'\
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 \
PARTITION BY RANGE (TO_DAYS(ts)) (PARTITION p20180301 VALUES LESS THAN (TO_DAYS('2018-03-02')) ENGINE = InnoDB)" 


mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"\
CREATE TABLE IF NOT EXISTS  vic_1mk.1mk (\
    ts          DATETIME  NOT NULL,\
    symbol      varchar(32) NOT NULL  COMMENT '合约',\
    open        double  COMMENT '开盘价',\
    high        double  COMMENT '最高价',\
    low         double  COMMENT '最低价',\
    close       double  COMMENT '收盘价',\
    quantity    double  COMMENT '成交量',\
    turnover    double  COMMENT '成交额',\
    openinterest double COMMENT '持仓量',\
    UNIQUE KEY (ts, symbol)\
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 \
PARTITION BY RANGE (TO_DAYS(ts)) (PARTITION p201001 VALUES LESS THAN (TO_DAYS('2010-02-01')) ENGINE = InnoDB)"


mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"\
CREATE TABLE IF NOT EXISTS  vic_5mk.5mk (\
    ts          DATETIME  NOT NULL,\
    symbol      varchar(32) NOT NULL  COMMENT '合约',\
    open        double  COMMENT '开盘价',\
    high        double  COMMENT '最高价',\
    low         double  COMMENT '最低价',\
    close       double  COMMENT '收盘价',\
    quantity    double  COMMENT '成交量',\
    turnover    double  COMMENT '成交额',\
    openinterest double COMMENT '持仓量',\
    UNIQUE KEY (ts, symbol)\
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 \
PARTITION BY RANGE (TO_DAYS(ts)) (PARTITION p201001 VALUES LESS THAN (TO_DAYS('2010-02-01')) ENGINE = InnoDB)"


mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"\
CREATE TABLE IF NOT EXISTS  vic_1h.1h (\
    ts          DATETIME  NOT NULL,\
    symbol      varchar(32) NOT NULL  COMMENT '合约',\
    open        double  COMMENT '开盘价',\
    high        double  COMMENT '最高价',\
    low         double  COMMENT '最低价',\
    close       double  COMMENT '收盘价',\
    quantity    double  COMMENT '成交量',\
    turnover    double  COMMENT '成交额',\
    openinterest double COMMENT '持仓量',\
    UNIQUE KEY (ts, symbol)\
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 \
PARTITION BY RANGE (TO_DAYS(ts)) (PARTITION p201001 VALUES LESS THAN (TO_DAYS('2010-02-01')) ENGINE = InnoDB)"


mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"\
CREATE TABLE IF NOT EXISTS  vic_1d.1d (\
    ts          DATETIME  NOT NULL,\
    symbol      varchar(32) NOT NULL  COMMENT '合约',\
    open        double  COMMENT '开盘价',\
    high        double  COMMENT '最高价',\
    low         double  COMMENT '最低价',\
    close       double  COMMENT '收盘价',\
    quantity    double  COMMENT '成交量',\
    turnover    double  COMMENT '成交额',\
    openinterest double COMMENT '持仓量',\
    UNIQUE KEY (ts, symbol)\
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 \
PARTITION BY RANGE (TO_DAYS(ts)) (PARTITION p201001 VALUES LESS THAN (TO_DAYS('2010-02-01')) ENGINE = InnoDB)"



#创建分区
for ((i=2010; i<=2018; i++))
do
    for ((j=1; j<=12; j++))
    do
        if [ $j -eq 1 ];then
            p=$(printf "p%d12" $[$i-1])
        else
            p=$(printf "p%d%02d" $i $[$j-1])
        fi
        
        dat=$(printf "%d%02d01" $i $j)
        echo $p $dat
        mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"alter table vic_1mk.1mk add partition(partition ${p} values LESS THAN ( TO_DAYS(${dat}) ));"
        mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"alter table vic_5mk.5mk add partition(partition ${p} values LESS THAN ( TO_DAYS(${dat}) ));"
        mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"alter table vic_1h.1h add partition(partition ${p} values LESS THAN ( TO_DAYS(${dat}) ));"
        mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"alter table vic_1d.1d add partition(partition ${p} values LESS THAN ( TO_DAYS(${dat}) ));"
    done
done

for ((j=290; j>0; j--))
do
    p='p'`date -d "-$[$j+1] day  2019-01-01" +%Y%m%d`
    
    dat=`date -d "-${j} day  2019-01-01" +%Y%m%d`
    
    echo $p  $dat
    
    mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"alter table vic_ticker.ticker add partition(partition ${p} values LESS THAN ( TO_DAYS(${dat}) ));"
done








