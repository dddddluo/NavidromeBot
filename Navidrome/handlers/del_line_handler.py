# 删除线路

import logging
from telegram import Update
from telegram.ext import CallbackContext
from database import routes_collection
from handlers.permissions import admin_only, private_only

logger = logging.getLogger(__name__)

@admin_only
@private_only
async def del_line(update: Update, context: CallbackContext):
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("使用方法: /del_line <线路名称>")
        return

    route_name = args[0]
    logger.info(f"Attempting to delete route {route_name}")

    result = routes_collection.update_one({}, {"$unset": {route_name: ""}})

    if result.modified_count > 0:
        await update.message.reply_text(f"线路 {route_name} 已删除")
        logger.info(f"Route {route_name} deleted.")
    else:
        await update.message.reply_text(f"线路 {route_name} 不存在")
        logger.warning(f"Route {route_name} does not exist.")
