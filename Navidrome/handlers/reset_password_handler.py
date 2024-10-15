import logging
from telegram import Update
from telegram.ext import CallbackContext
from database import users_collection
from services.navidrome_client import navidrome_service
from handlers.permissions import private_only

# 创建日志记录器
logger = logging.getLogger(__name__)

# 转义 MarkdownV2 特殊字符的函数


@private_only
async def reset_password(update: Update, context: CallbackContext):
    query = update.callback_query  # 获取回调查询
    # 查询数据库中是否有此用户，并且有na账号
    user_data = users_collection.find_one({"telegram_id": query.from_user.id})
    if not user_data:
        await query.answer(text="虎揍没号，你点什么点！", show_alert=True, cache_time=5)  # 回答查询以防止超时
        return
    user_id = user_data.get("user_id")
    new_password = user_data.get("password")
    name = user_data.get("name")
    username = user_data.get("username")
    if user_id is None or name is None or username is None:
        await query.answer(text="虎揍没号，你点什么点！", show_alert=True, cache_time=5)  # 回答查询以防止超时
        return
    await query.answer(cache_time=5)
    result = await navidrome_service.reset_password(user_id, name, username, new_password)
    if result.code == 200:
        await update.effective_chat.send_message(text=f"虎揍你的新鲜密码为: `{new_password}`", parse_mode="MarkdownV2")
    else:
        await update.effective_chat.send_message(text="重置密码失败。")
