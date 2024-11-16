import json
import os
import logging
# 从 config.json 读取配置
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
logger = logging.getLogger(__name__)

global config
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# Telegram Bot 配置
TELEGRAM_BOT_TOKEN = config.get('TELEGRAM_BOT_TOKEN')  # Telegram bot 令牌
TELEGRAM_BOT_NAME = config.get('TELEGRAM_BOT_NAME')  # Telegram bot 名称
OWNER = config.get('OWNER')  # 所有者
ADMIN_ID = config.get('ADMIN_ID')  # 管理员 Telegram ID
ALLOWED_GROUP_IDS = config.get('ALLOWED_GROUP_IDS') # Telegram群ID
GROUP_INVITE_LINK = config.get('GROUP_INVITE_LINK')
# Navidrome 令牌
bearer_TOKEN = None  # 全局变量，用于存储 Navidrome 令牌

# 数据库配置
DB_NAME = config.get('DB_NAME')  # 数据库名称
DB_URL = config.get('DB_URL')  # 数据库 URL，包含连接字符串
BACKUP_DB_ENABLE = config.get('BACKUP_DB_ENABLE', True)  # 数据库备份开关
DB_BACKUP_DIR = config.get('DB_BACKUP_DIR')  # 数据库备份目录
DB_BACKUP_RETENTION_DAYS = config.get('DB_BACKUP_RETENTION_DAYS')  # 数据库备份保留期限
# Navidrome API 配置
API_BASE_URL = config.get('API_BASE_URL')  # Navidrome 基础 URL
LOGIN_URL = f"{API_BASE_URL}/auth/login"  # 登录 URL
na_token_URL = f"{API_BASE_URL}/api/translation/zh-Hans"  # 检查令牌 URL
NA_ADMIN_USERNAME = config.get('NA_ADMIN_USERNAME')  # 管理员用户名
NA_ADMIN_PASSWORD = config.get('NA_ADMIN_PASSWORD')  # 管理员密码

# 时间参数配置
TIME_USER = config.get('TIME_USER')  # 默认是7天   秒（s）、分钟（m）、小时（h）、天（d）
TIME_USER_ENABLE = config.get('TIME_USER_ENABLE', True)

# 初始化图片logo
if config.get('START_PIC'):
    START_PIC = config.get('START_PIC')  # 初始化图片logo
    if not START_PIC.startswith("http"):
        START_PIC = os.path.join(os.path.dirname(__file__), START_PIC)
        if not os.path.exists(START_PIC):
            START_PIC = os.path.join(os.path.dirname(__file__), "logo.jpg")
else:
    START_PIC = os.path.join(os.path.dirname(__file__), "logo.jpg")  # 初始化图片logo
MESSAGE_HANDLER_TIMEOUT = 120
AWAITING_CODE, AWAITING_USERNAME, AWAITING_OPEN_REGISTER_USERNAME,AWAITING_OPEN_REGISTER_SLOTS, \
AWAITING_BROADCAST_MESSAGE, AWAITING_TARGET_SELECTION, AWAITING_PIN_CONFIRMATION = range(7)

def update_config(key: str, value: bool):
    """更新配置文件和内存中的配置"""
    global config  # 声明使用全局变量
    try:
        # 更新内存中的配置
        config[key] = value
        
        # 更新配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        logger.info(f"配置 {key} 已更新为 {value}")
    except Exception as e:
        logger.error(f"更新配置文件失败: {str(e)}") 