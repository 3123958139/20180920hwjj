# -*- coding:utf-8 -*-  

import logging
import os, sys

#   NOTSET  无输出
#   DEBUG   调试
#   INFO    消息
#   WARNING 警告
#   ERROR   错误
#   CRITICAL严重错误

loglevel = os.environ.get('LOG_LEVEL', 'INFO')
numeric_level = getattr(logging, loglevel.upper(), 10)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)

logging.basicConfig(
    stream=sys.stdout,
    level=numeric_level,
    format='%(asctime)s[%(filename)s:%(lineno)d:%(funcName)s]%(levelname)s %(message)s'
)




