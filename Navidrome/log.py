import logging
import os
from logging.handlers import TimedRotatingFileHandler
# 系统日志
# 检查日志目录是否存在，不存在则创建
log_dir = "./logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

handler = TimedRotatingFileHandler(os.path.join(log_dir, 'rotating_log.log'), when='D', interval=3, backupCount=10,
                                   encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
handler.suffix = '%Y%m%d'
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)