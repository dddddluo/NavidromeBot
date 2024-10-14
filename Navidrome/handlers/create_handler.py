# 注册用户

import logging
import datetime
from config import API_BASE_URL
from database import exchange_codes_collection, users_collection
from services.navidrome_client import navidrome_service
from handlers.permissions import private_only
from util import get_now_utc

# 创建日志记录器
logger = logging.getLogger(__name__)

# 生成随机密码的函数


@private_only
async def create(update, context):
    args = context.args
    user_data = users_collection.find_one(
        {"telegram_id": update.message.from_user.id})
    if user_data and user_data.get("user_id") is not None:
        await update.message.reply_text("虎揍，有号了还注册！！！")
        return
    if len(args) != 2:  # 检查参数是否正确
        await update.message.reply_text("使用方法: /create <兑换码> <用户名>")
        return

    code, username = args
    name = username  # 名字设为和用户名一样
    password = navidrome_service.generate_random_password()  # 生成随机密码

    # 检查兑换码是否存在且未使用
    exchange_code = exchange_codes_collection.find_one(
        {"code": code, "used": False})

    if not exchange_code:  # 如果兑换码无效或已被使用
        await update.message.reply_text("虎揍这兑换码无效！")
        return

    # 发送请求创建新用户
    response = await navidrome_service.create_na_user(username, name, password)

    if response is None:
        await update.message.reply_text("创建用户失败：Navidrome token 更新失败。")
        return
    # 处理响应
    if response.status_code == 200:  # 如果创建成功
        nauser_data = response.json()
        user_id = nauser_data.get("id")  # 获取用户ID

        # 标记兑换码为已使用，并记录使用者的信息和使用时间
        exchange_codes_collection.update_one(
            {"code": code},
            {"$set": {"used": True, "used_by": update.message.from_user.id,
                      "used_time": datetime.datetime.now().isoformat()}}
        )
        if user_data:
            users_collection.update_one(
                {"telegram_id": update.message.from_user.id},
                {"$set": {
                    "username": username,
                    "name": name,
                    "password": password,
                    "user_id": user_id
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
            f"虎揍 {username} 创建成功啦。\n👥用户名: `{username}`\n🔑密码: `{password}`\n🆔用户ID: `{user_id}`",
            parse_mode='MarkdownV2'
        )
        logger.info(f"虎揍 {username} 创建成功。")
    else:  # 如果创建失败
        if "ra.validation.unique" in response.text:
            await update.message.reply_text("虎揍换个用户名！")
        else:
            await update.message.reply_text("创建用户失败")
        logger.error(f"创建用户失败：{response}")
