from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from database import exchange_codes_collection
from handlers.permissions import admin_only
from database import users_collection
from util import delete_messages, new_exchange_code
from config import TELEGRAM_BOT_NAME
from log import logger


# 处理生成兑换码命令的函数
@admin_only
async def new_code(update: Update, context: CallbackContext):
    # 获取生成兑换码的数量，默认生成一个
    try:
        num_codes = int(context.args[0]) if context.args else 1
    except ValueError:
        reply_message = await context.bot.send_message(chat_id=update.effective_chat.id, text="请输入有效的数字。")
        context.job_queue.run_once(delete_messages, 5, data={
            'chat_id': update.message.chat.id,
            'user_message_id': update.message.message_id,
            'bot_message_id': reply_message.message_id
        })
        return
    # 获取回复的消息
    replied_message = update.message.reply_to_message
    target_id = None
    if replied_message:
        # 如果是回复消息，则删除被回复的用户
        target_id = replied_message.from_user.id
        if users_collection.find_one({"telegram_id": target_id, "user_id": {"$ne": None}, }):
            reply_message = await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{update.message.reply_to_message.from_user.mention_markdown_v2()} 已经注册过Navidrome账号了", parse_mode='MarkdownV2')
            context.job_queue.run_once(delete_messages, 5, data={
                'chat_id': update.message.chat.id,
                'user_message_id': update.message.message_id,
                'bot_message_id': reply_message.message_id
            })
            return
    await update.effective_message.delete()
    if target_id:
        num_codes = 1
    # 生成新的兑换码
    new_codes = []
    for _ in range(num_codes):
        new_code_str = new_exchange_code()
        if target_id:
            exchange_codes_collection.insert_one(
                {"code": new_code_str, "used": False, "owner": target_id})
        else:
            exchange_codes_collection.insert_one(
                {"code": new_code_str, "used": False})
        new_codes.append(new_code_str)
        logger.info(f"New exchange code generated: {new_code_str}")
    # 使用 MarkdownV2 格式回复用户生成的兑换码
    codes_text = "\n".join([f"`{code}`" for code in new_codes])
    # 如果没有指定用户，则只发送给当前执行命令的管理员
    if not target_id:
        await context.bot.send_message(chat_id=update.message.from_user.id, text=f"新的兑换码已生成：\n{codes_text}", parse_mode='MarkdownV2')
    else:
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🎟️虎揍我们走", url=f"https://t.me/{TELEGRAM_BOT_NAME}?start=start_with_code-{target_id}-{new_codes[0]}")
        ]])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{update.message.from_user.mention_markdown_v2()}为{update.message.reply_to_message.from_user.mention_markdown_v2()}生成了一个兑换码\n开启你的音乐之旅吧！", parse_mode='MarkdownV2', reply_markup=reply_markup)
        await context.bot.send_message(chat_id=update.message.from_user.id, text=f"新的兑换码已生成：\n{codes_text}，已经发送给`{target_id}`", parse_mode='MarkdownV2')
