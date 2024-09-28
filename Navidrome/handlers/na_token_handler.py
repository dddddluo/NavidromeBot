import logging
import requests
from telegram import Update
from telegram.ext import CallbackContext
import config
from handlers.permissions import admin_only, private_only
from services.navidrome_client import navidrome_service
# 创建日志记录器
logger = logging.getLogger(__name__)

# 检查 Navidrome 令牌的函数


@admin_only
@private_only
async def na_token(update: Update, context: CallbackContext):
    global bearer_TOKEN  # 声明全局变量 Navidrome_TOKEN
    if not config.bearer_TOKEN:  # 如果没有令牌，则刷新令牌
        if not navidrome_service.refresh_bearer_token():
            await update.message.reply_text("Navidrome token获取失败。")
            return

    bearer_TOKEN = config.bearer_TOKEN  # 从 config 中获取令牌

    headers = {
        'X-Nd-Authorization': f'bearer {bearer_TOKEN}',  # 设置 Navidrome 令牌
        'Content-Type': 'application/json'  # 设置请求头为 JSON 格式
    }
    response = requests.get(config.na_token_URL,
                            headers=headers)  # 发送 GET 请求检查令牌

    # 记录响应状态码和响应文本
    logger.info(
        f"Token check response: {response.status_code} - {response.text}")

    if response.status_code == 200:  # 如果响应状态码为 200，表示令牌有效
        await update.message.reply_text("Navidrome token有效。")
        logger.info("bearer token is valid.")
    else:
        if response.status_code == 401:  # 如果响应状态码为 401，表示未认证
            logger.info("bearer token expired, fetching a new one.")
            if refresh_bearer_token():  # 刷新 Navidrome 令牌
                bearer_TOKEN = config.bearer_TOKEN  # 更新令牌
                await update.message.reply_text("bearer token已自动更新。")
                logger.info("bearer token has been refreshed.")
            else:
                await update.message.reply_text("Navidrome token更新失败。")
                logger.error("Failed to refresh bearer token.")
        else:  # 处理其他响应状态码
            await update.message.reply_text(f"Navidrome token检查失败，错误码：{response.status_code}")
            logger.error(
                f"Navidrome token check failed, status code: {response.status_code}")
