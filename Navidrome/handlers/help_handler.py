from config import ADMIN_ID
from handlers.permissions import private_only
@private_only
async def help(update, context):
    user_id = update.effective_message.from_user.id
    if user_id in ADMIN_ID:
        message = (
            "命令帮助：\n"
            '/help 查看帮助信息 \n'
            '/start 开启主面板 \n'
            '/mm 查看用户信息 \n'
            '/new_code 创建新的兑换码（默认一个，命令+个数） \n'
            '/del_user 回复消息或tgid删除Navirome账号(命令+tgid) \n'
            '/new_line 新增或修改线路(命令+名字+线路) \n'
            '/del_line 删除线路(命令+名字) \n'
            '/add_whitelist 回复消息或tgid添加白名单(命令+tgid) \n'
            '/del_whitelist 回复消息或tgid删除白名单(命令+tgid) \n'
            '/na_token 手动刷新Navirome Token \n'
        )
        await update.message.reply_text(message)
