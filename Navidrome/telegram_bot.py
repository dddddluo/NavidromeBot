import logging
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, AIORateLimiter, ConversationHandler, TypeHandler
from handlers.permissions import restricted
from handlers.start_handler import start
from handlers.new_code_handler import new_code
from handlers.new_line_handler import new_line
from handlers.del_line_handler import del_line
from handlers.help_handler import help
from handlers.na_token_handler import na_token
from handlers.list_code_handler import list_code, code_pagination
from handlers.message_handler import handle_message, cancel, timeout
from handlers.button_handler import back_to_start, close, user_info, server_info, use_code
from handlers.del_user_handler import del_user, handle_left_chat_member
from handlers.time_user_handler import check_in_handler, start_scheduler
from handlers.add_whitelist_handler import add_whitelist
from handlers.del_whitelist_handler import del_whitelist
from handlers.time_user_handler import delete_inactive
from handlers.reset_password_handler import reset_password
from handlers.open_register_handler import open_register_user_callback, open_register_user_handler, open_register_admin_callback, open_register_admin_num_handler, close_register_admin_callback
from jobs.set_bot_command import set_bot_command_scheduler
from jobs.backup_db import backup_db, backup_db_scheduler
from config import TELEGRAM_BOT_TOKEN, AWAITING_CODE, AWAITING_USERNAME, AWAITING_OPEN_REGISTER_USERNAME, AWAITING_OPEN_REGISTER_SLOTS, MESSAGE_HANDLER_TIMEOUT
# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# 装饰现有处理函数
start = restricted(start)
new_code = restricted(new_code)
new_line = restricted(new_line)
del_line = restricted(del_line)
na_token = restricted(na_token)
help = restricted(help)
list_code = restricted(list_code)
handle_message = restricted(handle_message)
cancel = restricted(cancel)
back_to_start = restricted(back_to_start)
close = restricted(close)
user_info = restricted(user_info)
server_info = restricted(server_info)
use_code = restricted(use_code)
del_user = restricted(del_user)
add_whitelist = restricted(add_whitelist)
del_whitelist = restricted(del_whitelist)
delete_inactive = restricted(delete_inactive)


def main():
    print(TELEGRAM_BOT_TOKEN)
    dispatcher = ApplicationBuilder().connect_timeout(10).read_timeout(10).write_timeout(10).token(TELEGRAM_BOT_TOKEN).rate_limiter(AIORateLimiter(overall_max_rate=0, overall_time_period=0, group_max_rate=0, group_time_period=0, max_retries=10)).build()
    # 定义对话处理器
    use_code_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(use_code, pattern="^use_code"), CommandHandler("start", start)],
        states={
            AWAITING_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),],
            AWAITING_USERNAME: [MessageHandler(
                filters.TEXT & ~filters.COMMAND, handle_message)],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)]
        },
        fallbacks=[CommandHandler('cancel', cancel),
                   CallbackQueryHandler(
                       back_to_start, pattern="^back_to_start"),
                   CallbackQueryHandler(close, pattern="^close$")],
        conversation_timeout=MESSAGE_HANDLER_TIMEOUT
    )
    dispatcher.add_handler(use_code_conv_handler)
    open_register_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(open_register_user_callback, pattern="^open_register_user")],
        states={
            AWAITING_OPEN_REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, open_register_user_handler)],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)]
        },
        fallbacks=[CommandHandler('cancel', cancel),
                   CallbackQueryHandler(back_to_start, pattern="^back_to_start"),
                   CallbackQueryHandler(close, pattern="^close$")],
        conversation_timeout=MESSAGE_HANDLER_TIMEOUT
    )
    dispatcher.add_handler(open_register_conv_handler)
    opne_register_admin_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(open_register_admin_callback, pattern="^open_register_admin")],
        states={
            AWAITING_OPEN_REGISTER_SLOTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, open_register_admin_num_handler),],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=MESSAGE_HANDLER_TIMEOUT
    )
    dispatcher.add_handler(opne_register_admin_conv_handler)
    # 添加命令处理器
    dispatcher.add_handler(CommandHandler("start", start))  # 初始化
    dispatcher.add_handler(CommandHandler("help", help))  # 获取帮助
    dispatcher.add_handler(CommandHandler("new_line", new_line))  # 添加线路（名字+线路）
    dispatcher.add_handler(CommandHandler("del_line", del_line))  # 删除线路（命令+名字）
    dispatcher.add_handler(CommandHandler(
        "new_code", new_code))  # 创建新的邀请码（默认一个）
    dispatcher.add_handler(CommandHandler("list_code", list_code))  # 查看兑换码
    dispatcher.add_handler(CommandHandler(
        "na_token", na_token))  # 检测Navidrome Token
    dispatcher.add_handler(CommandHandler("del_user", del_user))
    dispatcher.add_handler(CommandHandler("add_whitelist", add_whitelist))
    dispatcher.add_handler(CommandHandler("del_whitelist", del_whitelist))
    dispatcher.add_handler(MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_left_chat_member))  # 处理用户退出群组事件
    dispatcher.add_handler(check_in_handler)  # 添加签到消息处理器
    dispatcher.add_handler(CallbackQueryHandler(
        back_to_start, pattern="^back_to_start"))  # 返回start界面
    dispatcher.add_handler(CallbackQueryHandler(
        close, pattern="^close$"))  # 关闭消息
    dispatcher.add_handler(CallbackQueryHandler(
        user_info, pattern="^user_info"))  # 用户功能
    dispatcher.add_handler(CallbackQueryHandler(
        server_info, pattern="^server_info"))  # 服务器
    dispatcher.add_handler(CallbackQueryHandler(
        reset_password, pattern="^reset_password"))  # 重置密码
    # 添加回调查询处理器
    dispatcher.add_handler(CallbackQueryHandler(code_pagination, pattern='^code_page_'))
    dispatcher.add_handler(CommandHandler(
        "backup_db", backup_db))  # 备份数据库
    dispatcher.add_handler(CommandHandler(
        "delete_inactive", delete_inactive))  # 删除不活跃用户
    dispatcher.add_handler(CallbackQueryHandler(close_register_admin_callback, pattern="^close_register_admin"))
    # 启动调度器
    start_scheduler(dispatcher)
    set_bot_command_scheduler(dispatcher)
    backup_db_scheduler(dispatcher)
    # 启动机器人
    dispatcher.run_polling()


if __name__ == '__main__':
    main()
