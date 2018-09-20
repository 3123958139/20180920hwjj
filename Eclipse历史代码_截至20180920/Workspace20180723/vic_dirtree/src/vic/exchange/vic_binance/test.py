from threading import Timer
import time


def f(a=None, b=None):   
    print('%r %r\n' %(a, b)) 


Timer(3, f, a=21212,b=23).start()

time.sleep(10)

