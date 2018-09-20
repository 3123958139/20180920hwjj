#!/bin/bash

#每5分中一个数据
mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"\
create table IF NOT EXISTS vic.equity(\
    id          int(11)  primary key not null auto_increment,\
    product     varchar(64)   NOT NULL  comment '产品名',\
    all_usdt    double        NOT NULL  comment '总美元权益',\
    bina_rate   double        NOT NULL  comment '币安资金占比',\
    huobi_rate  double        NOT NULL  comment '火币资金占比',\
    okex_rate   double        NOT NULL  comment 'okex资金占比',\
    netvalue    double        NOT NULL  comment '净值',\
    date        datetime      NOT NULL  comment '提交时间'\
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
"

#持仓品种份额表  每天结算的时候录入一条
mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"\
create table IF NOT EXISTS vic.currency_equity(\
    id          int(11)  primary key not null auto_increment,\
    product     varchar(64)   NOT NULL  comment '产品名',\
    currency    varchar(32)   NOT NULL  comment '货币',\
    balance     double        NOT NULL  comment '权益',\
    tousdt      double        NOT NULL  comment '折合美元',\
    rate        double        NOT NULL  comment '资金占比',\
    date          datetime      NOT NULL  comment '提交时间' \
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
"

#交易所持仓表  每天结算的时候录入一条
mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e"\
create table IF NOT EXISTS vic.exchange_equity(\
    id          int(11)  primary key not null auto_increment,\
    product     varchar(64)  NOT NULL   comment '产品名',\
    exchange    varchar(32)  NOT NULL   comment '交易所',\
    currency    varchar(32)  NOT NULL   comment '货币',\
    balance  double       NOT NULL   comment '币币权益',\
    ft_balance  double       NOT NULL   comment '期货权益',\
    tousdt      double       NOT NULL   comment '折合美元', \ 
    date          datetime      NOT NULL  comment '提交时间' \
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
"





