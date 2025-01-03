import asyncio
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, AIORateLimiter, ConversationHandler, TypeHandler
from handlers.permissions import restricted
from handlers.start_handler import start
from handlers.new_code_handler import new_code
from handlers.new_line_handler import new_line
from handlers.del_line_handler import del_line
from handlers.na_token_handler import na_token
from handlers.help_handler import help
from handlers.list_code_handler import list_code, code_pagination, clear_all_codes
from handlers.message_handler import handle_message, cancel, timeout
from handlers.button_handler import back_to_start, close, user_info, server_info, use_code, check_in, admin_menu_callback, back_to_admin
from handlers.del_user_handler import del_user, handle_left_chat_member, delete_not_in_group
from handlers.time_user_handler import check_in_handler, delete_inactive_user_scheduler
from handlers.add_whitelist_handler import add_whitelist
from handlers.del_whitelist_handler import del_whitelist
from handlers.time_user_handler import delete_inactive_callback
from handlers.reset_password_handler import reset_password
from handlers.open_register_handler import open_register_user_callback, open_register_user_handler, open_register_admin_callback, open_register_admin_num_handler, close_register_admin_callback
from jobs.set_bot_command import set_bot_command_scheduler
from jobs.backup_db import backup_db_scheduler, backup_db_callback, list_backup_files, restore_db_sync_navidrome, restore_db_only
from handlers.view_users_handler import view_users, view_users_pagination, view_whitelist, view_whitelist_pagination
from config import TELEGRAM_BOT_TOKEN, AWAITING_CODE, AWAITING_USERNAME, AWAITING_OPEN_REGISTER_USERNAME, AWAITING_OPEN_REGISTER_SLOTS, MESSAGE_HANDLER_TIMEOUT
from handlers.broadcast_handler import (
    broadcast_message_callback, handle_broadcast_message,
    handle_target_selection, handle_pin_confirmation,
    delete_broadcast_callback, handle_delete_broadcast,
    AWAITING_BROADCAST_MESSAGE, AWAITING_TARGET_SELECTION, AWAITING_PIN_CONFIRMATION
)
from handlers.task_control_handler import task_control_menu, toggle_backup, toggle_time_user
from error_handler import error_handler

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
back_to_admin = restricted(back_to_admin)
close = restricted(close)
user_info = restricted(user_info)
check_in = restricted(check_in)
server_info = restricted(server_info)
use_code = restricted(use_code)
del_user = restricted(del_user)
add_whitelist = restricted(add_whitelist)
del_whitelist = restricted(del_whitelist)
delete_inactive_callback = restricted(delete_inactive_callback)
delete_not_in_group = restricted(delete_not_in_group)
admin_menu_callback = restricted(admin_menu_callback)
view_users = restricted(view_users)
view_users_pagination = restricted(view_users_pagination)
view_whitelist = restricted(view_whitelist)
view_whitelist_pagination = restricted(view_whitelist_pagination)
task_control_menu = restricted(task_control_menu)
toggle_backup = restricted(toggle_backup)
toggle_time_user = restricted(toggle_time_user)

def main():
    print(TELEGRAM_BOT_TOKEN)
    dispatcher = ApplicationBuilder().connect_timeout(10).read_timeout(10).write_timeout(10).token(TELEGRAM_BOT_TOKEN).rate_limiter(AIORateLimiter(overall_max_rate=0, overall_time_period=0, group_max_rate=0, group_time_period=0, max_retries=5)).build()
    
    # 添加广播消息处理器
    broadcast_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_message_callback, pattern="^broadcast_message$")],
        states={
            AWAITING_BROADCAST_MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, handle_broadcast_message)],
            AWAITING_TARGET_SELECTION: [CallbackQueryHandler(handle_target_selection, pattern="^broadcast_")],
            AWAITING_PIN_CONFIRMATION: [CallbackQueryHandler(handle_pin_confirmation, pattern="^pin_|^no_pin$|^cancel_broadcast$")],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$"),
            CallbackQueryHandler(close, pattern="^close$"),
            MessageHandler(filters.COMMAND, cancel),
        ],
        conversation_timeout=MESSAGE_HANDLER_TIMEOUT,
    )
    dispatcher.add_handler(broadcast_conv_handler)

    
    # 定义对话处理器
    use_code_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(use_code, pattern="^use_code$"), CommandHandler("start", start)],
        states={
            AWAITING_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            AWAITING_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_to_start, pattern="^back_to_start$"),
            CallbackQueryHandler(close, pattern="^close$"),
            MessageHandler(filters.COMMAND, cancel),
        ],
        conversation_timeout=MESSAGE_HANDLER_TIMEOUT,
    )
    dispatcher.add_handler(use_code_conv_handler)

    
    open_register_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(open_register_user_callback, pattern="^open_register_user$")],
        states={
            AWAITING_OPEN_REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, open_register_user_handler)],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_to_start, pattern="^back_to_start$"),
            CallbackQueryHandler(close, pattern="^close$"),
            MessageHandler(filters.COMMAND, cancel),
        ],
        conversation_timeout=MESSAGE_HANDLER_TIMEOUT,
    )
    dispatcher.add_handler(open_register_conv_handler)

    opne_register_admin_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(open_register_admin_callback, pattern="^open_register_admin$")],
        states={
            AWAITING_OPEN_REGISTER_SLOTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, open_register_admin_num_handler)],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, timeout)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$"),
            CallbackQueryHandler(close, pattern="^close$"),
            MessageHandler(filters.COMMAND, cancel),
        ],
        conversation_timeout=MESSAGE_HANDLER_TIMEOUT,
    )
    dispatcher.add_handler(opne_register_admin_conv_handler)

    # 修改处理器的添加顺序
    # 1. 先添加命令处理器
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("new_line", new_line))
    dispatcher.add_handler(CommandHandler("del_line", del_line))
    dispatcher.add_handler(CommandHandler("new_code", new_code))
    dispatcher.add_handler(CommandHandler("na_token", na_token))
    dispatcher.add_handler(CommandHandler("del_user", del_user))
    dispatcher.add_handler(CommandHandler("add_whitelist", add_whitelist))
    dispatcher.add_handler(CommandHandler("del_whitelist", del_whitelist))
    
    # 2. 添加消息处理器
    dispatcher.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_left_chat_member))
    dispatcher.add_handler(check_in_handler)
    
    # 4. 添加管理菜单相关的回调查询处理器
    dispatcher.add_handler(CallbackQueryHandler(admin_menu_callback, pattern="^admin_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(back_to_admin, pattern="^back_to_admin$"))
    dispatcher.add_handler(CallbackQueryHandler(delete_broadcast_callback, pattern="^delete_broadcast$"))
    dispatcher.add_handler(CallbackQueryHandler(handle_delete_broadcast, pattern="^del_broadcast_[a-f0-9]+$"))
    
    # 5. 添加其他回调查询处理器
    dispatcher.add_handler(CallbackQueryHandler(list_code, pattern="^list_code$"))
    dispatcher.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    dispatcher.add_handler(CallbackQueryHandler(close, pattern="^close$"))
    dispatcher.add_handler(CallbackQueryHandler(user_info, pattern="^user_info$"))
    dispatcher.add_handler(CallbackQueryHandler(server_info, pattern="^server_info$"))
    dispatcher.add_handler(CallbackQueryHandler(check_in, pattern="^check_in$"))
    dispatcher.add_handler(CallbackQueryHandler(reset_password, pattern="^reset_password$"))
    dispatcher.add_handler(CallbackQueryHandler(delete_inactive_callback, pattern="^delete_inactive$"))
    dispatcher.add_handler(CallbackQueryHandler(code_pagination, pattern='^code_page_'))
    dispatcher.add_handler(CallbackQueryHandler(backup_db_callback, pattern="^backup_db$"))
    dispatcher.add_handler(CallbackQueryHandler(view_users, pattern="^view_users$"))
    dispatcher.add_handler(CallbackQueryHandler(view_users_pagination, pattern="^users_page_"))
    dispatcher.add_handler(CallbackQueryHandler(view_whitelist, pattern="^view_whitelist$"))
    dispatcher.add_handler(CallbackQueryHandler(view_whitelist_pagination, pattern="^whitelist_page_"))
    dispatcher.add_handler(CallbackQueryHandler(close_register_admin_callback, pattern="^close_register_admin$"))
    dispatcher.add_handler(CallbackQueryHandler(list_backup_files, pattern="^restore_db$"))
    dispatcher.add_handler(CallbackQueryHandler(restore_db_only, pattern="^restore_db_only_"))
    dispatcher.add_handler(CallbackQueryHandler(restore_db_sync_navidrome, pattern="^restore_db_sync_navidrome"))
    dispatcher.add_handler(CallbackQueryHandler(task_control_menu, pattern="^task_control$"))
    dispatcher.add_handler(CallbackQueryHandler(toggle_backup, pattern="^toggle_backup$"))
    dispatcher.add_handler(CallbackQueryHandler(toggle_time_user, pattern="^toggle_time_user$"))
    dispatcher.add_handler(CallbackQueryHandler(clear_all_codes, pattern="^clear_all_codes$"))
    dispatcher.add_handler(CallbackQueryHandler(delete_not_in_group, pattern="^delete_not_in_group$"))
    
    # 启动调度器
    delete_inactive_user_scheduler(dispatcher)
    set_bot_command_scheduler(dispatcher)
    backup_db_scheduler(dispatcher)
    # the error handler
    dispatcher.add_error_handler(error_handler)
    # 启动机器人
    # 使用 asyncio 来运行程序
    asyncio.run(dispatcher.run_polling(allowed_updates=[Update.MESSAGE, Update.CHAT_MEMBER, Update.CALLBACK_QUERY]))


if __name__ == '__main__':
    try:
        import uvloop
        uvloop.install()
        print("uvloop 已启用")
    except ImportError:
        print("未找到 uvloop,使用默认事件循环")
    main()
