#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding:utf-8

"""
@date:20180815
@author: David
"""

import os
from apscheduler.schedulers.background import BackgroundScheduler


def UpdateMySQLSchedule():
    #     os.system('python 1h.py')
    print(1)


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        UpdateMySQLSchedule,
        trigger='cron',
        day_of_week='mon-sun',
        hour=16,
        minute=52,
        second=30
    )
    try:
        print('Scheduler starts ...')
        scheduler.start()
    except Exception as e:
        print(e)
        scheduler.remove_all_jobs()
