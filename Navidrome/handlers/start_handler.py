# 初始化*按钮
import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from config import START_PIC, ADMIN_ID
from database import exchange_codes_collection, users_collection
from config import AWAITING_USERNAME
# 创建日志记录器
logger = logging.getLogger(__name__)

# 处理 /start 命令的函数
async def start(update, context):
    await update.effective_message.delete()
    if update.effective_message.chat.type == 'private':
        if update.effective_message and update.effective_message.text and 'start_with_code' in update.effective_message.text:
            if users_collection.find_one({"telegram_id": update.message.from_user.id, "user_id": {"$ne": None}, }):
                await update.message.reply_text("你已经注册过Navidrome账号了。")
                return ConversationHandler.END
            code_owner = int(update.effective_message.text.split('-')[1])
            if code_owner != update.effective_message.from_user.id:
                await update.effective_message.reply_text("别看了，这个兑换码不是你的")
                return ConversationHandler.END
            code = update.effective_message.text.split('-')[2]
            code_in_db = exchange_codes_collection.find_one({"code": code})
            if code_in_db is not None and code_in_db.get('owner') == code_owner and code_in_db.get('used') == False:
                await update.effective_message.reply_text("兑换码有效, 请输入你的用户名，当然了如果你不想要，你也可以取消注册 /cancel")
                context.user_data['code'] = code
                context.user_data['awaiting_code'] = False
                context.user_data['awaiting_username'] = True
                return AWAITING_USERNAME
            else:
                await update.effective_message.reply_text("兑换码无效")
                return ConversationHandler.END
    else:
        await update.effective_message.reply_text("请在私人聊天中使用")
    user = update.message.from_user if update.message else update.callback_query.from_user
    logger.info(f"User {user.username} started the conversation.")

    # 创建内联键盘
    keyboard = [
        [
            InlineKeyboardButton("👥用户", callback_data='user_info'),
            InlineKeyboardButton("🌐线路", callback_data='server_info')
        ],
        [
            InlineKeyboardButton("👑创建账号", callback_data='open_register_user'),
            InlineKeyboardButton("🎟️用注册码", callback_data='use_code')
        ]
    ]
    if user.id in ADMIN_ID:
        keyboard.append([
            InlineKeyboardButton("✅开放注册", callback_data='open_register_admin'),
            InlineKeyboardButton("❎关闭注册", callback_data='close_register_admin'),
            ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    # 发送欢迎消息和图片
    if START_PIC:
        photo = START_PIC
        caption = f"嗨！小虎揍 {user.first_name}！请选择功能👇"
        if update.message:
            await update.message.reply_photo(photo=photo, caption=caption, reply_markup=reply_markup)
        else:
            await update.callback_query.message.reply_photo(photo=photo, caption=caption, reply_markup=reply_markup)
    else:
        if update.message:
            await update.message.reply_text(f"嗨！小虎揍 {user.first_name}！请选择功能👇", reply_markup=reply_markup)
        else:
            await update.callback_query.message.reply_text(f"嗨！小虎揍 {user.first_name}！请选择功能👇", reply_markup=reply_markup)
    return ConversationHandler.END

