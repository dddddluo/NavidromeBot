#删除白名单
from telegram import Update
from telegram.ext import CallbackContext
from database import users_collection, whitelist_collection
from handlers.permissions import admin_only
from util import delete_messages
from log import logger


# 从白名单中删除的处理函数
@admin_only
async def del_whitelist(update: Update, context: CallbackContext):
    # 获取回复的消息
    replied_message = update.message.reply_to_message

    if replied_message:
        # 如果是回复消息，则删除被回复的用户
        telegram_id = replied_message.from_user.id
    else:
        if len(context.args) != 1:
            reply_message = await update.message.reply_text("使用方法: /del_whitelist <telegram_id>")
            context.job_queue.run_once(delete_messages, 5, data={
                'chat_id': update.message.chat.id,
                'user_message_id': update.message.message_id,
                'bot_message_id': reply_message.message_id
            })
            return
        telegram_id = int(context.args[0])

    user = users_collection.find_one({"telegram_id": telegram_id})
    if not user:
        reply_message = await update.message.reply_text(f"用户ID {telegram_id} 不存在。")
        context.job_queue.run_once(delete_messages, 5, data={
            'chat_id': update.message.chat.id,
            'user_message_id': update.message.message_id,
            'bot_message_id': reply_message.message_id
        })
        return

    # 从白名单集合中删除用户
    whitelist_collection.delete_one({"telegram_id": telegram_id})

    reply_message = await update.message.reply_text(f"这虎揍 {telegram_id} 已从白名单中删除")
    context.job_queue.run_once(delete_messages, 5, data={
        'chat_id': update.message.chat.id,
        'user_message_id': update.message.message_id,
        'bot_message_id': reply_message.message_id
    })
    logger.info(f"这虎揍 {telegram_id} 已从白名单中删除")

