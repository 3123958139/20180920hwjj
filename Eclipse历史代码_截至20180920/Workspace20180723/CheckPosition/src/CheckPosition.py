#!/usr/bin/env python
# coding=utf-8

import pandas as pd
from sqlalchemy import create_engine


class CheckPosition(object):
    def __init__(self):
        self._engine = create_engine('mysql://ops:ops!@#9988@47.74.249.179:3308/david?charset=utf8&autocommit=true')

    def _start(self):
        self._con = self._engine.connect()

    def _check_mysql_web(self):
        '''mysql的表同策略的通币种的进行合并，然后跟web进行核对
        '''
        self.no1 = pd.read_sql_table(table_name='NO1StrategyHolding', con=self._con, schema='positions', index_col=None, parse_dates='ts')
        self.exchange = list(set(self.no1['exchange'].values))
        self.symbol = list(set(self.no1['symbol'].values))

        pairs = []
        for exch in self.exchange:
            for sym in ['BCC', 'BTC', 'XRP', 'EOS', 'BCH', 'LTC', 'ETH']:
                if exch != 'BINA' and sym == 'BCC':
                    continue
                if exch == 'BINA' and sym == 'BCH':
                    continue
                pairs.append([exch, sym])

        query = """SELECT ts,exchange,label,currency,holding,price,usdt,btc 
        FROM david.BW1_BASE_DATA WHERE ts = 
        (SELECT DISTINCT ts FROM david.BW1_BASE_DATA ORDER BY ts DESC LIMIT 1);
        """
        df = pd.read_sql(query, self._con)
        # 假设策略不在子账户发单，且只做币币账户
        diff = {}
        for exch, sym in pairs:
            # OKEX、BB0、EOS
            web_qty = df[df['exchange'] == exch][df['label'] == 'BB0'][df['currency'] == sym]['holding'].sum()
            if web_qty is None:
                web_qty = 0.0
            sql_sym = exch+'--'+sym+'--USDT'
            sql_qty = self.no1[self.no1['exchange'] == exch][self.no1['symbol'] == sql_sym]['qty'].sum()
            if sql_qty is None:
                sql_qty = 0.0
            diff[sql_sym] = sql_qty-web_qty
        diff_df = pd.DataFrame(diff, index=[0])
        print(diff_df)

    def _check_mysql_tb(self):
        pass

    def _end(self):
        self._con.close()

    def main(self):
        self._start()
        self._check_mysql_web()
        self._end()


if __name__ == '__main__':
    obj = CheckPosition()
    obj.main()
