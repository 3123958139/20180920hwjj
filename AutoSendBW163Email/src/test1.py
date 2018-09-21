# coding:utf-8
import poplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import email
import smtplib
import datetime
from email.header import Header

# 当前日期
now = datetime.datetime.now().strftime("%Y.%m.%d")
# 发出邮箱
_user = "m18807739832@163.com"
_pwd = "test123456"
# 邮箱登录
sent = smtplib.SMTP_SSL('smtp.163.com', 465)
sent.login(_user, _pwd)
#


def add_image(path, imgid):
    '''定义添加图片附件的函数
    path    图片路径
    imgid   对应附件id，可以根据id嵌入正文
    '''
    with open(path, 'rb') as img:
        msg_image = MIMEImage(img.read())
        msg_image.add_header('Content-ID', imgid)
    return msg_image


content = MIMEMultipart('related')
attach_img = add_image('BW1_NETVALUE_PIC.jpg', 'BW1')
attach_img['Content-Disposition'] = 'attachment;filename="BW1_NETVALUE_PIC.jpg"'.decode(
    'utf-8').encode('gb18030')
content.attach(attach_img)
attach_txt = MIMEText("""Dear All,\nBelows are net charts of BW fund today, please review the attachment!""")
content.attach(attach_txt)
try:
    to = ['winsen.huang@invesmart.cn']    
    content['Subject'] = now + ' Net charts of BW fund'
    content['From'] = 'm18807739832@163.com'
    content['To'] = ','.join(to)
    sent.sendmail('m18807739832@163.com', to, content.as_string())
    sent.close()
except Exception as e:
    print e
