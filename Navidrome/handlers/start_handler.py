# 初始化*按钮
import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from config import START_PIC, ADMIN_ID, config
from database import exchange_codes_collection, users_collection
from config import AWAITING_USERNAME
import asyncio
# 创建日志记录器
logger = logging.getLogger(__name__)

# 处理 /start 命令的函数


async def start(update, context):
    if update.effective_message.chat.type == 'private':
        if update.effective_message and update.effective_message.text and 'start_with_code' in update.effective_message.text:
            if users_collection.find_one({"telegram_id": update.message.from_user.id, "user_id": {"$ne": None}, }):
                await asyncio.gather(update.effective_message.delete(), update.message.reply_text("你已经注册过Navidrome账号了。"))
                return ConversationHandler.END
            code_owner = int(update.effective_message.text.split('-')[1])
            if code_owner != update.effective_message.from_user.id:
                await asyncio.gather(update.effective_message.delete(), update.message.reply_text("别看了，这个兑换码不是你的"))
                return ConversationHandler.END
            code = update.effective_message.text.split('-')[2]
            code_in_db = exchange_codes_collection.find_one({"code": code})
            if code_in_db is not None and code_in_db.get('owner') == code_owner and code_in_db.get('used') == False:
                await asyncio.gather(update.effective_message.delete(), update.message.reply_text("兑换码有效, 请输入你的用户名，当然了如果你不想要，你也可以取消注册 /cancel"))
                context.user_data['code'] = code
                context.user_data['awaiting_code'] = False
                context.user_data['awaiting_username'] = True
                return AWAITING_USERNAME
            else:
                await asyncio.gather(update.effective_message.delete(), update.message.reply_text("兑换码无效"))
                return ConversationHandler.END
    user = update.message.from_user if update.message else update.callback_query.from_user
    logger.info(f"User {user.username} started the conversation.")

    # 创建内联键盘
    keyboard = [
        [
            InlineKeyboardButton("👥用户", callback_data='user_info'),
            InlineKeyboardButton("🌐线路", callback_data='server_info'),
        ],
        [
            InlineKeyboardButton("👑创建账号", callback_data='open_register_user'),
            InlineKeyboardButton("🎟️用注册码", callback_data='use_code')
        ]
    ]
    TIME_USER_ENABLE = config.get('TIME_USER_ENABLE', True)
    if TIME_USER_ENABLE:
        keyboard[0].append(
            InlineKeyboardButton("🔔签到", callback_data='check_in')
        )
    if user.id in ADMIN_ID:
        keyboard.append([
            InlineKeyboardButton("🔧管理面板", callback_data='admin_menu'),
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    caption = f"嗨！小虎揍 {user.first_name}！请选择功能👇"
    if update.message:
        await asyncio.gather(update.message.delete(), context.bot.send_photo(chat_id=update.effective_chat.id, photo=START_PIC, caption=caption, parse_mode='HTML', reply_markup=reply_markup))
    else:
        await asyncio.gather(context.bot.edit_message_caption(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id, caption=caption, parse_mode='HTML', reply_markup=reply_markup))
    return ConversationHandler.END
