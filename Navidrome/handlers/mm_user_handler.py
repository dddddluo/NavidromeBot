from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
import re
from handlers.permissions import admin_only
from database import users_collection
import random
from util import CHINA_TZ, delete_messages
from datetime import datetime
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
                    InlineKeyboardButton("🚫 禁用账户", callback_data=f"ban_user_{target_user_id}"),
                    InlineKeyboardButton("💢 删除账户", callback_data=f"del_user_{target_user_id}")
                ],
                [
                    InlineKeyboardButton("🏆 赠送白名单", callback_data=f"give_whitelist_{target_user_id}"),
                    InlineKeyboardButton("❌ 删除消息", callback_data=f"del_msg_{target_user_id}")
                ]
            ]
            hat = ['🎩', '🧢', '👒', '🎓', '⛑', '🪖', '👑']
            head = ['🤖', '😺', '🤡', '👽', '👾', '😈', '👹', '💀', '🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐻‍❄️', '🐨', '🐯', '🦁', '🐮', '🐷', '🐸', '🐵', '🐔', '🐧', '🐦', '🐣', '🐺', '🐴', '🐛', '🦄', '🎃']
            shirt = ['👙', '🩱', '👘', '🧥', '🥼', '🦺', '👚', '👕', '👖', '🩲', '🩳', '👔', '👗', '👙', '🩱', '👘', '🥻']
            shoes = ['🩴', '🥿', '👠', '👡', '👢', '👞', '👟', '🥾']
            bag = ['👝', '👛', '👜', '💼', '🎒', '🧳']
            is_whitelist = user_info.get('whitelist', False)
            last_sign_in_time = user_info.get('last_sign_in_time', '无')
            if isinstance(last_sign_in_time, datetime):
                last_sign_in_time = last_sign_in_time.strftime('%Y-%m-%d %H:%M:%S')
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
                InlineKeyboardButton("🎁 赠送资格(小虎揍我们走)", callback_data=f"give_reg_{target_user_id}")
            ],[
                InlineKeyboardButton("❌ 删除消息", callback_data=f"del_msg_{target_user_id}")
            ]]
            msg = f"{head[random.randint(0, len(head) - 1)]} 此用户 (TGID: {target_user_id}) 尚未注册"
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(msg, reply_markup=reply_markup)
    @staticmethod
    async def handle_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理用户管理按钮的回调"""
        query = update.callback_query
        await query.answer()
        action, user_id = query.data.split('_', 1)[0], int(query.data.split('_')[2])
        if action == "ban":
            # 禁用用户
            users_collection.update_one(
                {"telegram_id": user_id},
                {"$set": {"banned": True}}
            )
            await query.edit_message_text("已禁用该用户账户")
        elif action == "del":
            # 删除用户
            users_collection.delete_one({"telegram_id": user_id})
            await query.edit_message_text("已删除该用户账户")
        elif action == "give":
            # 赠送注册资格
            users_collection.insert_one({
                "telegram_id": user_id,
                "whitelist": True,
            })
            await query.edit_message_text("已赠送注册资格给该用户")
            
    def register_handlers(self, application):
        """注册处理程序"""
        application.add_handler(CommandHandler("mm", self.show_user_info))
        application.add_handler(CallbackQueryHandler(self.handle_user_action, pattern="^(ban|del|give)_user_"))
