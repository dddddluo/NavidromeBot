# 线路信息

import logging
from database import routes_collection
from handlers.permissions import private_only

# 创建日志记录器
logger = logging.getLogger(__name__)

# 处理 /line 命令的函数
@private_only
async def line(update, context):
    # 从数据库中查找一条线路记录
    routes = routes_collection.find_one({})
    if routes:
        # 如果找到了线路记录，构建返回消息
        message = "当前线路：\n" + "\n".join([f"{key}: {value}" for key, value in routes.items() if key != '_id'])
        await update.message.reply_text(message)  # 发送消息给用户
        logger.info("Returned current routes.")  # 记录日志
    else:
        # 如果没有找到线路记录，提示用户没有设置线路信息
        await update.message.reply_text("当前没有设置线路信息，快找管理员设置叭")
        logger.warning("No routes found.")  # 记录日志
