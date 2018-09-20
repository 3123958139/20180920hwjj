#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8


import time
from apscheduler.schedulers.background import BackgroundScheduler

sched = BackgroundScheduler()


@sched.scheduled_job('interval', seconds=5)
def my_job():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))


sched.start()

"""
@date:20180905
@author: David
"""
'''
import os
from apscheduler.schedulers.background import BackgroundScheduler


def PrintNetValue():
    print('*' * 80)
    os.system("""python netvalue_risk_tools.py sendmsg --fund 'BW1' --to 'david|bruce|Dreamy|winsen|rickon|Kevin|calvin|tau|Windy|sheldon' --units 325059.2879 --extra usdt 19041.37 --account okex 13651401725 --account huobi 'kevinwang126@163.com' --account bina 'kevinwang126@163.com' --account okex BW1Hedge""")
    print('*' * 80)
    os.system("""python netvalue_risk_tools.py sendmsg --fund 'BW2' --to 'david|bruce|Dreamy|winsen|rickon|Kevin|calvin|tau|Windy|sheldon' --units 66.6618  --extra usdt 120151.31 --account okex 'Kevin.wang@126.com' --account huobi 'Kevin.wang@126.com' --account bina 'Kevin.wang@126.com' --account okex thetrading""")
    """
    os.system("python netvalue_risk_tools.py balance -s currency -a okex 13651401725 -a huobi 'kevinwang126@163.com' -a bina 'kevinwang126@163.com' -a okex 'BW1Hedge'|grep -e USDT -e HT -e BNB -e OKB -e BTC -e BCH -e BCC -e ETH -e LTC -e EOS -e XRP")
   
    os.system("python netvalue_risk_tools.py balance -s usdt -a okex 13651401725 -a huobi 'kevinwang126@163.com' -a bina 'kevinwang126@163.com' -a okex 'BW1Hedge'")

    os.system("python netvalue_risk_tools.py balance -s currency  -a bina 'Kevin.wang@126.com' -a okex 'Kevin.wang@126.com' -a huobi 'Kevin.wang@126.com' -a okex 'thetrading'| grep -e USDT -e HT -e BNB -e OKB -e BTC -e BCH -e BCC -e ETH -e LTC -e EOS -e XRP")

    os.system("python netvalue_risk_tools.py balance -s usdt  -a bina 'Kevin.wang@126.com' -a okex 'Kevin.wang@126.com' -a huobi 'Kevin.wang@126.com' -a okex 'thetrading'")
    """


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        PrintNetValue,
        trigger='interval',
        seconds=3
    )
    try:
        print('Scheduler starts ...')
        scheduler.start()
    except Exception as e:
        print(e)
        scheduler.remove_all_jobs()
'''
