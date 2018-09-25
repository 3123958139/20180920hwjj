# coding:utf-8

"""
date  : 20180925
author: david
"""

import datetime
import pandas as pd
from sqlalchemy import create_engine

class CheckHoding(object):
    """实现持仓的两个核对
    1、tb与mysql :tb手动更新数据得到信号，导出信号为txt，python读取信号整理成mysql格式；然后与mysql一一匹配；
    2、web与mysql:mysql的信号按品种合并，然后与web核对。
    """

    def __init__(self):
        pass

    def _start(self):        
        self._engine = create_engine('mysql+pymysql://ops:ops!@#9988@47.74.249.179:3308/david?charset=utf8&autocommit=true')
        self._con = self._engine.connect()

    def _end(self):
        self._con.close()

    def _check_web(self):
        """核对web和mysql的持仓
        """
        

    def _check_tb(self):
        """核对tb和mysql的持仓
        """
        def __read_tb_signal(txt='StrategySignals.txt'):
            """tb导出的信号整理成df，其中strategyID、symbol是联合字段唯一
            """
            tb_signal_df = pd.DataFrame(columns=['strategyID', 'symbol', 'tb_signal'])
            with open(txt, 'r') as f:
                for line in f:
                    if line[0]=='[':
                        strategyID = line[1:-2].upper()
                        continue
                    else:
                        symbol = line[:-3].upper()
                        signal = float(line[-2])
                        data_dict = {
                            'strategyID': strategyID,
                            'symbol'    : symbol,
                            'tb_signal' : signal,
                            }
                        tb_signal_df = tb_signal_df.append(pd.Series(data_dict), ignore_index=True)
            return tb_signal_df                        
        def __read_mysql_qty(table_name='NO1StrategyHolding'):
            """mysql的信号整理成df，其中strategyID、symbol是联合字段唯一
            """
            mysql_qty_df = pd.read_sql_table(table_name=table_name, con=self._con, schema='positions', columns=['strategyID', 'symbol', 'qty'])
            mysql_qty_df['strategyID'] = mysql_qty_df['strategyID'].map(lambda x: x.upper())
            mysql_qty_df['symbol']     = mysql_qty_df['symbol'].map(lambda x: x.upper())
            mysql_qty_df.rename(columns={'qty':'qty_mysql'}, inplace=True)
            return mysql_qty_df
        def __caculate_position(product_info_dict={}):
            """传入产品信息计算头寸
            product_info_dict = {
                'product_name'  : 'BW1',
                'asset_total'   : 347467,
                'ratio_position': 0.5,
                'num_strategy'  : 8,
                'allo_exchange' : {
                    'BINA' : 0.5,
                    'HUOBI': 0.4,
                    'OKEX' : 0.1,
                },
                'allo_currency' : {
                    'BTC': 0.2,
                    'EOS': 0.2,
                    'ETH': 0.2,
                    'XRP': 0.2,
                    'BCH': 0.1,
                    'LTC': 0.1,
                },
            }
            """
            def ___get_currency_price(list_currency=['BTC', 'EOS', 'ETH', 'XRP', 'BCH', 'LTC']):
                """获取currency的价格提供给头寸计算
                """
                import urllib.request
                cur_price_dict = {}
                headers = {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'}
                for cur in list_currency:                    
                    req = urllib.request.Request(url='https://www.okex.com/api/v1/ticker.do?symbol=%s_usdt' % cur.lower(), headers=headers) 
                    cur_data = eval(urllib.request.urlopen(req).read())
                    cur_price_dict[cur] = float(cur_data['ticker']['buy'])
                return cur_price_dict
            product_info_dict = product_info_dict
            cur_price_dict = ___get_currency_price()
            list_position = []
            for sym in product_info_dict['allo_currency'].keys():
                for exch in product_info_dict['allo_exchange'].keys():
                    exch_sym = exch+'--'+sym+'--USDT'
                    list_position.append([exch_sym, product_info_dict['asset_total']*product_info_dict['ratio_position']/product_info_dict['num_strategy']*product_info_dict['allo_exchange'][exch]*product_info_dict['allo_currency'][sym]/cur_price_dict[sym]])
            return list_position    
        # tb信号、mysql信号、头寸计算三个df合并        
        tb_signal_df = __read_tb_signal()
        mysql_qty_df = __read_mysql_qty()
        product_info_dict = {
                'product_name'  : 'BW1',
                'asset_total'   : 347467,
                'ratio_position': 0.5,
                'num_strategy'  : 8,
                'allo_exchange' : {
                    'BINA' : 0.5,
                    'HUOBI': 0.4,
                    'OKEX' : 0.1,
                },
                'allo_currency' : {
                    'BTC': 0.2,
                    'EOS': 0.2,
                    'ETH': 0.2,
                    'XRP': 0.2,
                    'BCH': 0.1,
                    'LTC': 0.1,
                },
            }
        tb_position_df = pd.DataFrame(data=__caculate_position(product_info_dict=product_info_dict), columns=['symbol', 'tb_position'])
        check_df = pd.merge(tb_signal_df, mysql_qty_df, on=['strategyID', 'symbol'])
        check_df = pd.merge(check_df, tb_position_df, how='outer', on='symbol')
        check_df.dropna(inplace=True)
        check_df['qty_tb'] = check_df['tb_signal']*check_df['tb_position']
        check_df['qty_tb_minus_mysql'] = check_df['qty_tb'] - check_df['qty_mysql']
        check_df['ts'] = datetime.datetime.now()
        check_df = check_df[['ts', 'strategyID', 'symbol', 'tb_signal', 'tb_position', 'qty_tb', 'qty_mysql', 'qty_tb_minus_mysql']]
        check_df.to_sql('BW1_CHECK_TB', con=self._con, schema='david', index=False, if_exists='append', chunksize=500)

    def main(self):
        self._start()
        self._check_tb()
        self._end()


if __name__ == '__main__':
    obj = CheckHoding()
    obj.main()
