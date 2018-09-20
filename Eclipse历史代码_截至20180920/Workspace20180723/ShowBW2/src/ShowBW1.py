#!/usr/bin/env python
# coding=utf-8

from sqlalchemy import create_engine
from viclib.common.conf import VConf
from viclib.exchange.vic_okex.okex_http import OkexHttp
import pandas as pd
import time

class ShowBW1(object):
    def __init__(self):
        self.engine = create_engine('mysql://ops:ops!@#9988@47.74.249.179:3308/david?charset=utf8&autocommit=true')

    def _start(self):
        '''准备工作，如建立mysql的链接
        '''
        self._con = self.engine.connect()

    def _btc_usdt(self, account='13651401725'):
        '''获取btc的usdt价格，默认是okex的ticker数据
        '''
        conf          = VConf()
        url           = conf.get_http('okex')
        apikey        = conf.get_apikey('okex', account)
        apisecret     = conf.get_secret('okex', account)
        okexhttp      = OkexHttp(url, apikey, apisecret)
        self.btc_usdt = float(okexhttp.ticker('btc_usdt')['ticker']['last'])

    def _df(self):
        '''选出最近时间的数据，用于生成一条统计记录
        '''
        query = """SELECT ts,exchange,label,currency,holding,price,usdt,btc 
        FROM david.BW1_BASE_DATA WHERE ts = 
        (SELECT DISTINCT ts FROM david.BW1_BASE_DATA ORDER BY ts DESC LIMIT 1);
        """
        self.df = pd.read_sql(query, self._con)
        self.ts = list(set(self.df['ts'].values))[0]

    def _group(self):
        '''将currency分组：
        pt 平台币
        bb 币币币
        ft 合约币
        '''
        self.currency = list(set(self.df['currency'].values))
        pt = ['BNB', 'HT', 'OKB']
        ft2 = sorted([x for x in self.currency if x[-4:] == 'WEEK' or x[-4:] == 'RTER'])
        bbft1 = [x for x in self.currency if x not in pt and x not in ft2]
        self.group = [pt, ft2, bbft1]

    def _total_account_usdtvalue(self, out_of_account_usdtvalue=19041.37):
        '''计算总权益=账外权益+bb0权益+ft1权益
        '''
        self.out_of_account_usdtvalue = out_of_account_usdtvalue
        [pt, _, bbft1] = self.group
        self.total_account_usdtvalue = self.df[self.df['currency'].isin(pt+bbft1)]['usdt'].sum() + self.out_of_account_usdtvalue
        self.out_of_account_ratio = self.out_of_account_usdtvalue / self.total_account_usdtvalue*100

    def _exchange_usdtvalue_ratio(self):
        '''分交易所计算权益和比率
        '''
        okex_cur = self.df[self.df['exchange'].str.contains('OKEX')]
        self.okex_usdtvalue = okex_cur[okex_cur['label'].isin(['BB0', 'FT1'])]['usdt'].sum()
        self.okex_ratio = self.okex_usdtvalue / self.total_account_usdtvalue*100
        bina_cur = self.df[self.df['exchange'].str.contains('BINA')]
        self.bina_usdtvalue = bina_cur[bina_cur['label'].isin(['BB0'])]['usdt'].sum()
        self.bina_ratio = self.bina_usdtvalue / self.total_account_usdtvalue*100
        huobi_cur = self.df[self.df['exchange'].str.contains('HUOBI')]
        self.huobi_usdtvalue = huobi_cur[huobi_cur['label'].isin(['BB0'])]['usdt'].sum()
        self.huobi_ratio = self.huobi_usdtvalue / self.total_account_usdtvalue*100

    def _currency_qty_ratio(self):
        '''根据currency的分组计算币种的持仓和比率
        '''
        [pt, _, bbft1] = self.group
        self.cur_qty_ratio = {}
        for cur in pt+bbft1:
            cur_qty = self.df[self.df['currency'].isin([cur])]['holding'].sum()
            cur_ratio = self.df[self.df['currency'].isin([cur])]['usdt'].sum()/self.total_account_usdtvalue*100
            self.cur_qty_ratio[cur] = [cur_qty, cur_ratio]

    def _total_spot_usdtvalue_ratio(self):
        '''计算币币账户的总权益，不含OKEX的合约部分
        '''
        self.total_spot_usdtvalue = self.df[self.df['label'] == 'BB0']['usdt'].sum()
        self.total_spot_ratio = self.total_spot_usdtvalue / self.total_account_usdtvalue*100

    def _total_futures_usdtvalue_ratio(self):
        '''计算合约部分的净头寸=合约持仓总额-合约权益总额，和比率
        '''
        self.total_futures_usdtvalue = self.df[self.df['label'].isin(['FT1', 'FT2'])]['usdt'].sum()
        self.total_futures_ratio = self.total_futures_usdtvalue / self.total_account_usdtvalue*100

    def _end(self):
        '''收尾工作，如关闭mysql的链接
        '''
        self._con.close()

    def main(self):
        '''根据bruce的excel表整理
        '''
        sql_dict = {}
        self._start()
        self._df()
        sql_dict['ts'] = self.ts
        self._group()
        self._total_account_usdtvalue()
        sql_dict['out_of_account_usdtvalue'] = self.out_of_account_usdtvalue
        sql_dict['out_of_account_ratio']     = self.out_of_account_ratio
        sql_dict['total_account_usdtvalue']  = self.total_account_usdtvalue
        self._currency_qty_ratio()
        cur_qty_ratio = self.cur_qty_ratio
        for cur in cur_qty_ratio.keys():
            sql_dict[cur+'_qty']   = cur_qty_ratio[cur][0]
            sql_dict[cur+'_ratio'] = cur_qty_ratio[cur][1]
        self._exchange_usdtvalue_ratio()
        sql_dict['okex_usdtvalue']  = self.okex_usdtvalue
        sql_dict['bina_usdtvalue']  = self.bina_usdtvalue
        sql_dict['huobi_usdtvalue'] = self.huobi_usdtvalue
        sql_dict['okex_ratio']      = self.okex_ratio
        sql_dict['bina_ratio']      = self.bina_ratio
        sql_dict['huobi_ratio']     = self.huobi_ratio
        self._total_spot_usdtvalue_ratio()
        self._total_futures_usdtvalue_ratio()
        sql_dict['total_spot_usdtvalue']    = self.total_spot_usdtvalue
        sql_dict['total_spot_ratio']        = self.total_spot_ratio
        sql_dict['total_futures_usdtvalue'] = self.total_futures_usdtvalue
        sql_dict['total_futures_ratio']     = self.total_futures_ratio
        sql_dict['net_position_usdtvalue']  = self.total_futures_usdtvalue + self.total_spot_usdtvalue
        sql_dict['net_position_ratio']      = sql_dict['net_position_usdtvalue'] / sql_dict['total_account_usdtvalue']*100
        # 查询sql的表的字段，如果跟df的字段不一致，
        # sql缺乏df的字段，则先在sql表新增，
        # 最后插入。
        df = pd.DataFrame(sql_dict, index=[0])
        # df['xxxxxxxxxxxxx'] = 1
        columns = sorted(list(set(df.columns.values)))
        df = df[columns]
        # CREATE TABLE IF NOT EXISTS david.BW1_STAT(ts datetime DEFAULT NULL, UNIQUE KEY ts (ts) USING BTREE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        query = """
        select COLUMN_NAME from information_schema.columns where table_name='BW1_STAT';
        """
        sql_df      = pd.read_sql(query, self._con)
        sql_columns = list(sql_df['COLUMN_NAME'].values)
        diff        = [x for x in columns if x not in sql_columns]
        if len(diff) > 0:
            for dif in diff:
                query = """ALTER TABLE david.BW1_STAT ADD COLUMN %s DOUBLE DEFAULT NULL;                
                """ % dif
                self._con.execute(query)
            time.sleep(2)
        try:
            y = raw_input('Write to mysql?y\\n?')
            if y == 'y':
                df.to_sql('BW1_STAT', self._con, schema='david', index=False, if_exists='append', chunksize=500)
        except:
            raise Exception
        self._end()


if __name__ == '__main__':
    obj = ShowBW1()
    obj.main()
