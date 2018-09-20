# -*- utf8 -*-

import sys
sys.path.append("..")
from vics.lib.qyapi_weixin import *
from datetime import datetime


AGENG_ID = 5
SECRET = "nVzt0pYQWNFccZiGcpjHLKSG5TqxB6T3_KgMhqXHGMU"
TO_USER = "winsen|rickon|bruce|simons|calvin|kevin|nicole|suri"
#TO_USER = "winsen"

def sendTradeMsg(msg):
    reload(sys)
    sys.setdefaultencoding('utf-8')
    toparty = 4 
    msg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")+ " " + msg
    qy = QyWeixin()
    qy.sendtxt(SECRET, AGENG_ID, msg, TO_USER, toparty)


if __name__ == "__main__":
    sendTradeMsg("test")
