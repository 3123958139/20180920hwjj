# -*- coding:utf-8 -*-  

import logging
import os, sys

#   NOTSET  �����
#   DEBUG   ����
#   INFO    ��Ϣ
#   WARNING ����
#   ERROR   ����
#   CRITICAL���ش���

loglevel = os.environ.get('LOG_LEVEL', 'INFO')
numeric_level = getattr(logging, loglevel.upper(), 10)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)

logging.basicConfig(
    stream=sys.stdout,
    level=numeric_level,
    format='%(asctime)s[%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s'
)




