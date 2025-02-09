from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
import re
from handlers.permissions import admin_only
from database import users_collection, exchange_codes_collection
import random
from util import delete_messages, new_exchange_code, get_user_from_message, get_user_from_id
from datetime import datetime
from services.navidrome_client import navidrome_service
from config import TELEGRAM_BOT_NAME, ALLOWED_GROUP_IDS
hat = ['🎩', '🧢', '👒', '🎓', '⛑', '🪖', '👑']
head = ['🤖', '😺', '🤡', '👽', '👾', '😈', '👹', '💀', '🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼',
        '🐻‍❄️', '🐨', '🐯', '🦁', '🐮', '🐷', '🐸', '🐵', '🐔', '🐧', '🐦', '🐣', '🐺', '🐴', '🐛', '🦄', '🎃']
shirt = ['👙', '🩱', '👘', '🧥', '🥼', '🦺', '👚', '👕',
         '👖', '🩲', '🩳', '👔', '👗', '👙', '🩱', '👘', '🥻']
shoes = ['🩴', '🥿', '👠', '👡', '👢', '👞', '👟', '🥾']
bag = ['👝', '👛', '👜', '💼', '🎒', '🧳']


class MMUserHandler:
    def __init__(self):
        pass

    @staticmethod
    @admin_only
    async def show_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示用户信息的处理函数"""
        if not update.message.reply_to_message and not context.args:
            message = await update.message.reply_text("🫡 尊敬的虎揍管理员，请回复用户消息或提供用户的 TGID")
            await update.message.delete()
            context.job_queue.run_once(delete_messages, 5, data={
                'chat_id': update.message.chat.id,
                'bot_message_id': message.message_id
            })
            return
        # 获取目标用户ID
        if update.message.reply_to_message:
            target_user_id = update.message.reply_to_message.from_user.id
        else:
            # 验证输入的TGID是否为数字
            if not re.match(r'^\d+$', context.args[0]):
                await update.message.delete()
                message = await update.message.reply_text("🫡 尊敬的虎揍管理员，请回复用户消息或提供用户 TGID")
                context.job_queue.run_once(delete_messages, 5, data={
                    'chat_id': update.message.chat.id,
                    'bot_message_id': message.message_id
                })
                return
            target_user_id = int(context.args[0])
            await update.message.delete()
        # 获取用户信息
        user_info = users_collection.find_one({"telegram_id": target_user_id})

        # 准备按钮
        buttons = []
        if user_info:
            # 用户存在，添加管理按钮
            buttons = [
                [
                    InlineKeyboardButton(
                        "💢 删除账户", callback_data=f"deluser_{target_user_id}"),
                    InlineKeyboardButton(
                        "🏆 赠送白名单", callback_data=f"givewhitelist_{target_user_id}"),
                ],
                [
                    InlineKeyboardButton(
                        "✅ 好的", callback_data=f"delmsg_{target_user_id}")
                ]
            ]
            is_whitelist = user_info.get('whitelist', False)
            last_sign_in_time = user_info.get('last_sign_in_time', '无')
            if isinstance(last_sign_in_time, datetime):
                last_sign_in_time = last_sign_in_time.strftime(
                    '%Y-%m-%d %H:%M:%S')
            # 格式化用户信息
            msg = (
                f"{hat[random.randint(0, len(hat) - 1)]} 用户信息:\n"
                f"{head[random.randint(0, len(head) - 1)]} TGID: {user_info['telegram_id']}\n"
                f"{shirt[random.randint(0, len(shirt) - 1)]} 用户名: {user_info.get('username', '无')}\n"
                f"{shoes[random.randint(0, len(shoes) - 1)]} 等级: {'🧸 普通用户' if not is_whitelist else '🏆 白名单用户'}\n"
                f"{bag[random.randint(0, len(bag) - 1)]} 签到时间: {last_sign_in_time}"
            )
        else:
            # 用户不存在，添加赠送注册资格按钮
            buttons = [[
                InlineKeyboardButton(
                    "🎁 赠送资格(小虎揍我们走)", callback_data=f"givereg_{target_user_id}")
            ], [
                InlineKeyboardButton(
                    "✅ 好的", callback_data=f"delmsg_{target_user_id}")
            ]]
            msg = f"{head[random.randint(0, len(head) - 1)]} 此用户 (TGID: {target_user_id}) 没有 Navidrome 账户"
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(msg, reply_markup=reply_markup)

    @staticmethod
    @admin_only
    async def handle_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理用户管理按钮的回调"""
        query = update.callback_query
        await query.answer()
        action, user_id = query.data.split(
            '_', 1)[0], int(query.data.split('_')[-1])
        user_info = users_collection.find_one({"telegram_id": user_id})
        target_user = await get_user_from_id(context, user_id)
        ok_keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "✅ 好的", callback_data=f"delmsg_{user_id}")
        ]])
        if action == "deluser":
            if user_info.get("user_id"):
                await navidrome_service.delete_user(user_info["user_id"])
            else:
                await query.edit_message_text(f"💢 {target_user.mention_markdown_v2()}尚未注册Navidrome账户", parse_mode='MarkdownV2', reply_markup=ok_keyboard)
            # 删除用户
            users_collection.delete_one({"telegram_id": user_id})
            await query.edit_message_text(f"💢 已删除{target_user.mention_markdown_v2()}的Navidrome账户", parse_mode='MarkdownV2', reply_markup=ok_keyboard)
        elif action == "givereg":
            new_code_str = new_exchange_code()
            exchange_codes_collection.insert_one(
                {"code": new_code_str, "used": False, "owner": user_id})
            reply_markup = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "🎟️虎揍我们走", url=f"https://t.me/{TELEGRAM_BOT_NAME}?start=start_with_code-{user_id}-{new_code_str}")
            ]])
            await query.delete_message()
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{query.from_user.mention_markdown_v2()}为{target_user.mention_markdown_v2()}生成了一个兑换码\n开启你的音乐之旅吧！", parse_mode='MarkdownV2', reply_markup=reply_markup)
        elif action == "givewhitelist":
            # 赠送白名单
            users_collection.update_one(
                {"telegram_id": user_id},
                {"$set": {"whitelist": True}}
            )
            await query.edit_message_text(f"🏆 已赠送白名单给{target_user.mention_markdown_v2()}", parse_mode='MarkdownV2', reply_markup=ok_keyboard)
        elif action == "delmsg":
            await query.message.delete()

    def register_handlers(self, application):
        """注册处理程序"""
        application.add_handler(CommandHandler("mm", self.show_user_info))
        application.add_handler(CallbackQueryHandler(
            self.handle_user_action, pattern="^(deluser|givereg|givewhitelist|delmsg)"))
