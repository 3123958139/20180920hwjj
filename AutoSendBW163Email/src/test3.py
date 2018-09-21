#"-*- coding: utf-8 -*-"
import smtplib
from email.mime.text import MIMEText

mail_user="m18807739832@163.com"
mail_password="test123456"
mailto_list=["3123958139@qq.com"]
mail_host="smtp.163.com"
mail_postfix="163.com"

def sendmail(to_list,sub,content):
    me="徐书奎"+"<"+mail_user+"@"+mail_postfix+">"
    msg=MIMEText("<a href='http://www.cnblogs.com/xiaowuyi'>小五义</a>","html","utf-8")
    msg['Subject']=sub
    msg['From']=me
    msg['To']=",".join(to_list)
    try:
        server=smtplib.SMTP()
        server.connect(mail_host)
        server.login(mail_user,mail_password)
        server.sendmail(me,to_list,msg.as_string())
        server.close()
        return True
    except Exception,e:
        print str(e)
        return False
if sendmail(mailto_list,"标题:发送的是html格式","<a href='http://www.cnblogs.com/xiaowuyi'>小五义</a>"):
    print "done!"
else:
    print "falsed!"