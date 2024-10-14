import logging
from telegram.ext import CallbackContext
from telegram import Update
from database import users_collection, whitelist_collection
from config import ALLOWED_GROUP_IDS
from handlers.permissions import admin_only
from util import delete_messages
from services.navidrome_client import navidrome_service
# 创建日志记录器
logger = logging.getLogger(__name__)

# 删除用户的函数


async def delete_user_by_telegram_id(telegram_id, context: CallbackContext):
    user_data = users_collection.find_one({"telegram_id": telegram_id})
    mention = None
    for chat_id in ALLOWED_GROUP_IDS:
        chat_member = await context.bot.get_chat_member(chat_id, telegram_id)
        mention = chat_member.user.mention_html()
        break
    if mention is None:
        mention = f'<a href="tg://user?id={telegram_id}">这虎揍</a>'
    if not user_data:
        logger.debug(f"用户 {telegram_id} 未找到。")
        return 400, mention, "没找到这虎揍！"

    logger.debug(f"user_data: {user_data}")  # 添加调试日志
    user_id = user_data.get("user_id")  # 使用 .get() 方法避免 KeyError
    if not user_id:
        return 400, mention, "Navidrome中没有此虎揍！"

    response_data, status = await navidrome_service.delete_user(user_id)

    if status == 200:
        # 从数据库中删除用户记录
        users_collection.delete_one({"telegram_id": telegram_id})
        whitelist_collection.delete_one({"telegram_id": telegram_id})
        return 200, mention, "这虎揍的账号已删除"
    else:
        return 400, mention, f"删除用户失败：{response_data}"

# 处理删除用户命令的函数


@admin_only
async def del_user(update: Update, context: CallbackContext):
    # 获取回复的消息
    replied_message = update.message.reply_to_message

    if replied_message:
        # 如果是回复消息，则删除被回复的用户
        telegram_id = replied_message.from_user.id
    else:
        # 如果不是回复消息，则检查是否提供了参数
        if len(context.args) != 1:
            reply_message = await update.message.reply_text("使用方法: /del_user <telegram_id> 或 回复某人的消息使用 /del_user")
            context.job_queue.run_once(delete_messages, 5, data={
                'chat_id': update.message.chat.id,
                'user_message_id': update.message.message_id,
                'bot_message_id': reply_message.message_id
            })
            return
        telegram_id = int(context.args[0])

    code, mention, result = await delete_user_by_telegram_id(telegram_id, context)
    if code == 200:
        reply_message = await update.message.reply_text(
            f"{mention} {result}", parse_mode='HTML')
        context.job_queue.run_once(delete_messages, 5, data={
            'chat_id': update.message.chat.id,
            'user_message_id': update.message.message_id,
            'bot_message_id': reply_message.message_id
        })
    else:
        reply_message = await update.message.reply_text(
            f"{mention} {result}", parse_mode='HTML')
        context.job_queue.run_once(delete_messages, 5, data={
            'chat_id': update.message.chat.id,
            'user_message_id': update.message.message_id,
            'bot_message_id': reply_message.message_id
        })
    logger.info(f"删除用户：{telegram_id} 结果： {result}")

# 处理用户退出群组事件的函数


async def handle_left_chat_member(update: Update, context: CallbackContext):
    logger.info("Handling left chat member event...")
    left_member = update.message.left_chat_member
    telegram_id = left_member.id
    user_data = users_collection.find_one({"telegram_id": telegram_id})
    if user_data and user_data.get("user_id") is not None:
        code, mention, result = await delete_user_by_telegram_id(telegram_id, context)
        # 发送通知消息到群里
        if code == 200:
            notification_message = f"检测到这虎揍 {mention} 退群，账号已自动删除。"
        else:
            notification_message = f"检测到这虎揍 {mention} 退群，但删除账号时出错：{result}"

        logger.info(f"处理用户 {left_member.username} ({telegram_id}) 退出群组事件：{result}")
        for chat_id in ALLOWED_GROUP_IDS:
            await context.bot.send_message(chat_id=chat_id, text=notification_message, parse_mode='HTML')
    users_collection.delete_one({"telegram_id": telegram_id})
    whitelist_collection.delete_one({"telegram_id": telegram_id})
