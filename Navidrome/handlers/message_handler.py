import logging
from telegram.ext import ConversationHandler
from database import exchange_codes_collection, users_collection
from util import get_now_utc
from services.navidrome_client import navidrome_service
from handlers.start_handler import start
from config import AWAITING_USERNAME, MESSAGE_HANDLER_TIMEOUT, AWAITING_CODE
# 创建日志记录器
logger = logging.getLogger(__name__)

# 处理用户发送的消息


async def handle_message(update, context):
    if users_collection.find_one({"telegram_id": update.message.from_user.id, "user_id": {"$ne": None}, }):
        await update.message.reply_text("虎揍，有号了还注册！！！")
        return ConversationHandler.END
    user = update.message.from_user  # 获取发送消息的用户
    text = update.message.text  # 获取消息文本

    logger.info(f"Received message: {text} from user: {user.username}")  # 调试日志

    if context.user_data.get('awaiting_code'):
        logger.info(f"Awaiting code from user: {user.username}")  # 调试日志
        # 用户正在输入注册码
        code = text.strip()
        exchange_code = exchange_codes_collection.find_one(
            {"code": code, "used": False})
        if exchange_code:
            logger.info(f"Code {code} is valid. Awaiting username.")  # 调试日志
            # 验证成功，进入下一阶段
            context.user_data['code'] = code
            context.user_data['awaiting_code'] = False
            context.user_data['awaiting_username'] = True
            await update.message.reply_text(
                "🔋【虎揍马上成功啦！】：\n\n"
                f"- 请在{MESSAGE_HANDLER_TIMEOUT}s内对我发送你的用户名\n"
                "退出点 /cancel"
            )
            return AWAITING_USERNAME
        else:
            logger.info(f"Code {code} is invalid or already used.")  # 调试日志
            await update.message.reply_text("虎揍这兑换码无效，请重新输入兑换码！")
            return AWAITING_CODE

    elif context.user_data.get('awaiting_username'):
        logger.info(f"Awaiting username from user: {user.username}")  # 调试日志
        # 用户正在输入用户名
        username = text.strip()
        password = navidrome_service.generate_random_password()
        code = context.user_data['code']
        name = username
        # 发送请求创建新用户
        response, status_code = await navidrome_service.create_na_user(username, name, password)
        if status_code == 200:
            logger.info(f"User {username} created successfully.")  # 调试日志
            user_id = response.get("id")  # 获取用户ID

            # 标记兑换码为已使用，并记录使用者的信息和使用时间
            exchange_codes_collection.update_one(
                {"code": code},
                {"$set": {"used": True, "used_by": user.id,
                          "used_time": get_now_utc()}}
            )
            if users_collection.find_one({"telegram_id": update.message.from_user.id}):
                users_collection.update_one(
                    {"telegram_id": update.message.from_user.id},
                    {"$set": {
                        "username": username,
                        "name": name,
                        "password": password,
                        "user_id": user_id,
                    }}
                )
            else:
                users_collection.insert_one({
                    "telegram_id": update.message.from_user.id,
                    "username": username,
                    "name": name,
                    "password": password,
                    "user_id": user_id,  # 保存用户ID
                    "created_at": get_now_utc(),  # 添加创建时间
                    "last_check_in": None  # 添加最后签到时间，初始为None
                })
            await update.message.reply_text(
                f"虎揍你的账号创建成功啦！\n👥用户名: `{username}`\n🔑密码: `{password}`\n🆔用户ID: `{user_id}`",
                parse_mode='MarkdownV2'
            )
            context.user_data.clear()
            return ConversationHandler.END
        else:
            logger.error(f"Failed to create user: {response}")  # 调试日志
            if isinstance(response, dict) and 'errors' in response:
                errors = response['errors']
                if 'userName' in errors and errors['userName'] == 'ra.validation.unique':
                    await update.message.reply_text("虎揍用户名重复啦！\n请在120s内对我发送你的用户名\n退出点 /cancel")
                    return AWAITING_USERNAME
                else:
                    await update.message.reply_text("创建用户失败，请稍后重试。")
            else:
                await update.message.reply_text("创建用户失败，请稍后重试。")
            context.user_data.clear()
            return ConversationHandler.END

async def timeout(update, context):
    try:
        res = await context.bot.send_message(chat_id=update.effective_chat.id, text='虎揍你超时了，会话已结束！')
    except Exception as e:
        logger.warning(e)
        pass
    return ConversationHandler.END

async def cancel(update, context):
    user = update.message.from_user
    logger.info(f"User {user.username} canceled the conversation.")
    await update.message.reply_text('已取消操作。')
    context.user_data.clear()
    await start(update, context)  # 返回到start界面
    return ConversationHandler.END
