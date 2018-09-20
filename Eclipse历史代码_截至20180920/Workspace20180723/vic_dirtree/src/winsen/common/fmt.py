# -*- coding:utf-8 -*-
from datetime import datetime


def timestamp2str(timestamp):
    """
    """
    return datetime.fromtimestamp(timestamp).isoformat()

def pricePrecise(data):
    """
    """
    return round(data, 4)



if __name__ == "__main__":
    timestamp=1440741417.283
    print(timestamp2str(timestamp))
