#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8

"""
@date:20180905
@author: David
"""

import os
from apscheduler.schedulers.blocking import BlockingScheduler


def BW_SCHEDULER():
    os.system('clear')
    print('*'*80)
    os.system("""
    python BW1_BASE_DATA.py
    """)
    print('*'*80)
    os.system("""
    python BW2_BASE_DATA.py
    """)
    print('*'*80)
    os.system("""
    python ShowBW1.py
    """)
    print('*'*80)
    os.system("""
    python ShowBW2.py
    """)


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(
        BW_SCHEDULER,
        trigger='interval',
        seconds=1800
    )
    try:
        print('Scheduler starts ...')
        scheduler.start()
    except:
        raise Exception
        # scheduler.remove_all_jobs()



