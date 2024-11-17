from telegram import Update
from telegram.ext import CallbackContext
from database import routes_collection
from handlers.permissions import admin_only, private_only
from log import logger

@admin_only
@private_only
async def new_line(update: Update, context: CallbackContext):
    # 获取命令参数
    args = context.args
    if len(args) != 2:  # 检查参数是否正确
        await update.message.reply_text("使用方法: /new_line <线路名称> <URL>")
        return

    # 提取线路名称和URL
    route_name, route_value = args
    logger.info(f"设置线路 {route_name} 为 {route_value}")

    # 更新数据库中的线路信息，如果不存在则插入新的记录
    routes_collection.update_one(
        {}, {"$set": {route_name: route_value}}, upsert=True)
    await update.message.reply_text(f"线路信息已更新：{route_name}: {route_value}")
