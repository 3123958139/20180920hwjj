#!/usr/bin/env python
#coding=utf-8

import os
import sys
import time
import click
import logging
from datetime import datetime as dt


from viclib.netvalue.binance_netvalue import BinanService
from viclib.netvalue.okex_netvalue import OkexService
from viclib.netvalue.huobi_netvalue import HuobiService

from viclib.common.xsl import XLSWriter
from viclib.common.qyapi_weixin  import QyWeixin
from viclib.common.mysql_pool  import MysqlPool

qy = QyWeixin()

@click.group()
def cli(): pass


'''
# sendmsg 

#净值相关
python netvalue_risk_tools.py sendmsg -u 685540.57 -e usdt 41624.91 -t 'Dreamy|Dreamy' 


#权益相关
python netvalue_risk_tools.py balance -e okex/okexft/bina/huobi

python netvalue_risk_tools.py balance -e okexft -s exchange

下单撤单
python netvalue_risk_tools.py place_order -e okex 

python netvalue_risk_tools.py cancel_order -e okex

'''

def exchange_handle(exchange, account):
    handle = {
        'bina' : ['bina', BinanService], 
        'huobi': ['huobi', HuobiService],
        'okex' : ['okex', OkexService],
    }.get(exchange)
    handle[1] = handle[1](account)
    return handle

def usdt2btc(usdt):
    return  round(usdt/OkexService().tousdt('btc'), 8)

def print_exchange_position(fun):
    bs = fun[1].balances_list()
    for c in bs:
        vol = bs[c]['free'] + bs[c]['freezed']
        ft = bs[c].get('future') if bs[c].get('future') else 0
        usdt = fun[1].tousdt(c) * (vol+ft)
        btc = usdt2btc(usdt)
        print('%-8s%-8s%16.4f%16.4f%16.4f%16.4f' %(fun[0], c, vol, ft, usdt, btc))
           
def print_currency_position(_funs):
    balances={}
    for fun in _funs:
        bs = fun[1].balances_list()
        for c in bs:
            vol = bs[c]['free'] + bs[c]['freezed'] + (bs[c].get('future') if bs[c].get('future') else 0)
            if not balances.get(c): balances[c] = {'free':0, 'usdt':0}
            balances[c]['free'] += vol
            balances[c]['usdt'] += fun[1].tousdt(c) * vol 
    for c in balances:
        print('%-8s%16.4f%16.4f%16.4f' %(c, balances[c]['free'], balances[c]['usdt'], usdt2btc(balances[c]['usdt'])))


# python netvalue_risk_tools.py sendmsg              \
# --fund '恶水1号'                                   \
# --to "bruce|Dreamy|winsen|rickon|Kevin|calvin|tau" \
# --units 138195.51                                  \
# --extra usdt 19041.367                             \
# --account okex 13651401725                         \
# --account huobi 'kevinwang126@163.com'             \
# --account bina 'kevinwang126@163.com'               

@click.command()
@click.option('--fund', '-f',  help=u'基金名称')
@click.option('--units', '-u', type=float, help=u'基金份额')
@click.option('--to',    '-t', help=u'发送净值给用户')
@click.option('--extra', '-e', multiple=True, type=(unicode, float), help=u'不能读取到的币种金额')
@click.option('--account','-a', multiple=True, type=(unicode, unicode),help=u'统计账户')
def sendmsg(fund, units, to, extra, account):
    handles = []
    for item in account: 
        logging.info('%r', item)
        handles.append(exchange_handle(item[0], item[1])[1])
    
    _sum = 0
    for handle in handles:
        _sum += handle.sum_usdt()
   
    for item in extra:  
        _sum += OkexService().tousdt(item[0]) * item[1] 

    #美元转换为btc
    btc = usdt2btc(_sum)
    
    current_time = time.strftime('%Y-%m-%d %H:%M',time.localtime())
    message = u'%s   %s   法币净值 : %s  法币权益 : %s$  btc净值:%s btc权益:%sbtc' % (fund, current_time, round(float(_sum/units), 4), round(_sum, 2), round(float(btc/units), 4), round(btc, 4))
    secret = 'xzNVWx-_Ub_HwDsWZn3ISOjtbRem56Izkg1ZMUW4z1g'
    agentid = 1000003
    resp = qy.sendtxt(secret, agentid, message, to)
    print('message:%s, resp:%s' % (message, resp))
    
    #balance = {}
    #balance['product']      = '恶水1号' 
    #balance['all_usdt']     = round(_sum, 4)
    #balance['bina_rate']    = round(bina/_sum , 4) 
    #balance['huobi_rate']   = round(huobi/_sum, 4)
    #balance['okex_rate']    = round(okex/_sum , 4)
    #balance['netvalue']     = round(float(_sum/units), 4)
    #balance['date']         = datetime.datetime.now()
    #_mysql = MysqlPool('47.74.249.179', 3308, 'ops', 'ops!@#9988', 'vic')
    #_mysql = MysqlPool(host, 3308, 'ops', 'ops!@#9988', 'vic')
    #insert_vic_equity(_mysql, balance)


# python netvalue_risk_tools.py balance   \
# --show  exchange                        \
# --account okex 13651401725              \
# --account huobi 'kevinwang126@163.com'  \
# --account bina 'kevinwang126@163.com'     
@click.command()
@click.option('--show',  '-s', type=click.Choice(['exchange', 'currency', 'usdt']), help=u'输出数据')
@click.option('--account','-a', multiple=True, type=(unicode, unicode),help=u'账户')
def balance(show, account):
    handles = []
    for item in account: 
        logging.info('%r', item)
        handles.append(exchange_handle(item[0], item[1]))
    
    def show_exchange(): 
        for handle in handles: print_exchange_position(handle)
    
    def show_currency(): 
        print_currency_position(handles)
    
    def show_usdt(): 
        for handle in handles: 
            print('%-8s%16.4f' %(handle[0], handle[1].sum_usdt()))
    
    {
        'exchange':show_exchange, 
        'currency':show_currency,
        'usdt': show_usdt,
    }.get(show)()

@click.command()
def help():
    print("基金产品账户组:\n\
            --account okex 13651401725              \\\n\
            --account huobi 'kevinwang126@163.com'  \\\n\
            --account bina 'kevinwang126@163.com'   \\\n\
                                                    \\\n\
            --account okex 'Kevin.wang@126.com  '   \\\n\
            --account huobi 'Kevin.wang@126.com'    \\\n\
            --account bina 'Kevin.wang@126.com  ' ")

    print("查询持仓信息:\n\
           python netvalue_risk_tools.py balance   \\\n\
           --show  exchange                        \\\n\
           --account okex 13651401725              \\\n\
           --account huobi 'kevinwang126@163.com'  \\\n\
           --account bina 'kevinwang126@163.com'     ")
    
    print("估值:\n\
           python netvalue_risk_tools.py sendmsg              \\\n\
           --fund '恶水1号'                                   \\\n\
           --to 'bruce|Dreamy|winsen|rickon|Kevin|calvin|tau' \\\n\
           --units 138195.51                                  \\\n\
           --extra usdt 19041.367                             \\\n\
           --account okex 13651401725                         \\\n\
           --account huobi 'kevinwang126@163.com'             \\\n\
           --account bina 'kevinwang126@163.com' ")

cli.add_command(sendmsg)
cli.add_command(balance)
cli.add_command(help)

if __name__ == "__main__":
    cli()










