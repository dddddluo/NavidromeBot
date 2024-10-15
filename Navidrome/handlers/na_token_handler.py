import logging
from telegram import Update
from telegram.ext import CallbackContext
import config
from services.navidrome_client import navidrome_service
from handlers.permissions import admin_only, private_only

# 创建日志记录器
logger = logging.getLogger(__name__)

# 检查 Navidrome 令牌的函数


@admin_only
@private_only
async def na_token(update: Update, context: CallbackContext):
    if not config.bearer_TOKEN:  # 如果没有令牌，则刷新令牌
        if not await navidrome_service.refresh_bearer_token():
            await update.message.reply_text("Navidrome token获取失败。")
            return

    result = await navidrome_service.check_token()

    logger.info(f"Token check response: Code {result.code}, Message: {result.message}")

    if result.code == 200:  # 如果响应状态码为 200，表示令牌有效
        await update.message.reply_text("Navidrome token有效。")
        logger.info("bearer token is valid.")
    else:
        await update.message.reply_text(f"Navidrome token检查失败，错误码：{result.code}，消息：{result.message}")
        logger.error(f"Navidrome token check failed, status code: {result.code}, message: {result.message}")
