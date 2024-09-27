import requests
import logging
from config import LOGIN_URL, NA_ADMIN_USERNAME, NA_ADMIN_PASSWORD

logger = logging.getLogger(__name__)

bearer_TOKEN = None  # 全局变量，用于存储 Navidrome 令牌

# 获取新的 Navidrome 令牌的函数
def refresh_bearer_token():
    global bearer_TOKEN
    payload = {
        "username": NA_ADMIN_USERNAME,
        "password": NA_ADMIN_PASSWORD
    }
    headers = {
        'Content-Type': 'application/json'
    }
    logger.info(f"尝试从 {LOGIN_URL} 获取新的 Navidrome 令牌")
    response = requests.post(LOGIN_URL, json=payload, headers=headers)
    logger.info(f"登录响应: {response.status_code} - {response.text}")
    if response.status_code == 200:
        bearer_TOKEN = response.json().get("token")
        logger.info("Navidrome 令牌刷新成功。")
        return True
    else:
        logger.error("获取新的 Navidrome 令牌失败。")
        return False

# 获取当前 Navidrome 令牌的函数
def get_bearer_token():
    return bearer_TOKEN