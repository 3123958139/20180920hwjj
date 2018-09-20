from datetime import datetime
import os
import time

from apscheduler.schedulers.background import BackgroundScheduler


def UpdateMySQL():
    os.system("python 1h.py")
    print('Tick! The time is: %s' % datetime.now())


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        UpdateMySQL,
        trigger='cron',
        day_of_week='mon-sun',
        hour=17,
        minute=46,
        second=1
    )
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
