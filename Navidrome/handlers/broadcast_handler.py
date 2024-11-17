from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ConversationHandler, ContextTypes
from config import ALLOWED_GROUP_IDS
from database import db
from bson import ObjectId
from datetime import datetime
from log import logger


# 定义会话状态
AWAITING_BROADCAST_MESSAGE = 1
AWAITING_TARGET_SELECTION = 2
AWAITING_PIN_CONFIRMATION = 3

async def broadcast_message_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理广播消息的回调"""
    try:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            "请发送要广播的消息内容：\n\n"
            "（支持文本、图片、视频等格式）\n"
            "发送 /cancel 取消操作"
        )
        return AWAITING_BROADCAST_MESSAGE
    except Exception as e:
        logger.error(f"Error in broadcast_message_callback: {str(e)}")
        await update.callback_query.message.reply_text("发生错误，请重试")
        return ConversationHandler.END

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户发送的广播消息"""
    try:
        context.user_data['broadcast_message'] = update.message
        
        # 如果只有一个群组，直接进入置顶选择
        if len(ALLOWED_GROUP_IDS) == 1:
            context.user_data['broadcast_target'] = 'broadcast_all'
            keyboard = [
                [
                    InlineKeyboardButton("📌 置顶并通知", callback_data='pin_notify'),
                    InlineKeyboardButton("📌 仅置顶", callback_data='pin_only'),
                ],
                [
                    InlineKeyboardButton("➡️ 不置顶", callback_data='no_pin'),
                    InlineKeyboardButton("❌ 取消", callback_data='cancel_broadcast')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "请选择是否置顶消息：",
                reply_markup=reply_markup
            )
            return AWAITING_PIN_CONFIRMATION
        
        # 如果有多个群组，显示群组选择
        keyboard = [
            [
                InlineKeyboardButton("📢 全部群组", callback_data='broadcast_all'),
            ]
        ]
        
        # 为每个群组添加按钮
        for group_id in ALLOWED_GROUP_IDS:
            try:
                chat = await context.bot.get_chat(group_id)
                keyboard.append([InlineKeyboardButton(
                    f"📝 {chat.title}", 
                    callback_data=f'broadcast_group_{group_id}'
                )])
            except Exception as e:
                logger.error(f"Error getting chat info for {group_id}: {str(e)}")
                continue
        
        keyboard.append([InlineKeyboardButton("❌ 取消", callback_data='cancel_broadcast')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "请选择广播目标：",
            reply_markup=reply_markup
        )
        return AWAITING_TARGET_SELECTION
    except Exception as e:
        logger.error(f"Error in handle_broadcast_message: {str(e)}")
        await update.message.reply_text("发生错误，请重试")
        return ConversationHandler.END

async def handle_target_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理目标群组选择"""
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == 'cancel_broadcast':
            await query.edit_message_text("广播已取消")
            return ConversationHandler.END
        
        context.user_data['broadcast_target'] = query.data
        
        keyboard = [
            [
                InlineKeyboardButton("📌 置顶并通知", callback_data='pin_notify'),
                InlineKeyboardButton("📌 仅置顶", callback_data='pin_only'),
            ],
            [
                InlineKeyboardButton("➡️ 不置顶", callback_data='no_pin'),
                InlineKeyboardButton("❌ 取消", callback_data='cancel_broadcast')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "请选择是否置顶消息：",
            reply_markup=reply_markup
        )
        return AWAITING_PIN_CONFIRMATION
    except Exception as e:
        logger.error(f"Error in handle_target_selection: {str(e)}")
        await query.edit_message_text("发生错误，请重试")
        return ConversationHandler.END

async def handle_pin_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理置顶确认并发送广播"""
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == 'cancel_broadcast':
            await query.edit_message_text("广播已取消")
            return ConversationHandler.END
        
        # 获取要广播的群组
        target_groups = ALLOWED_GROUP_IDS if context.user_data['broadcast_target'] == 'broadcast_all' else [int(context.user_data['broadcast_target'].split('_')[2])]
        
        # 获取原始消息
        original_message = context.user_data['broadcast_message']
        
        # 记录已发送的消息ID，用于后续管理
        broadcast_collection = db['broadcasts']
        broadcast_messages = []
        current_time = datetime.now()
        
        # 发送消息到每个目标群组
        for group_id in target_groups:
            try:
                # 转发消息
                new_message = await original_message.copy(chat_id=group_id)
                
                # 处理置顶
                if query.data in ['pin_notify', 'pin_only']:
                    disable_notification = query.data == 'pin_only'
                    await context.bot.pin_chat_message(
                        chat_id=group_id,
                        message_id=new_message.message_id,
                        disable_notification=disable_notification
                    )
                
                # 记录广播消息信息，使用当前时间
                broadcast_messages.append({
                    'group_id': group_id,
                    'message_id': new_message.message_id,
                    'date': current_time
                })
                
            except Exception as e:
                logger.error(f"Error broadcasting to group {group_id}: {str(e)}")
                await query.message.reply_text(f"发送到群组 {group_id} 失败: {str(e)}")
        
        # 保存广播记录到数据库
        if broadcast_messages:
            broadcast_collection.insert_one({
                'messages': broadcast_messages,
                'sender_id': update.effective_user.id,
                'date': current_time
            })
        
        await query.edit_message_text("广播发送完成！")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in handle_pin_confirmation: {str(e)}")
        await query.edit_message_text("发生错误，请重试")
        return ConversationHandler.END

async def delete_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """删除历史广播消息"""
    try:
        query = update.callback_query
        await query.answer()
        
        broadcast_collection = db['broadcasts']
        
        # 获取最近的广播记录
        broadcasts = list(broadcast_collection.find().sort('date', -1).limit(5))
        
        if not broadcasts:
            await query.edit_message_caption(caption="没有找到历史广播消息")
            return
        
        keyboard = []
        for broadcast in broadcasts:
            # 使用第一条消息的时间作为显示
            date_str = broadcast['date'].strftime("%Y-%m-%d %H:%M")
            keyboard.append([InlineKeyboardButton(
                f"删除 {date_str} 的广播",
                callback_data=f"del_broadcast_{str(broadcast['_id'])}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙返回", callback_data='back_to_admin')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_caption(
            caption="选择要删除的广播消息：",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error in delete_broadcast_callback: {str(e)}")
        await query.edit_message_caption(caption=f"发生错误，请重试: {str(e)}")

async def handle_delete_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理删除特定广播消息的请求"""
    try:
        query = update.callback_query
        await query.answer()
        
        broadcast_id = query.data.split('_')[2]
        
        broadcast_collection = db['broadcasts']
        
        # 获取广播记录
        broadcast = broadcast_collection.find_one({'_id': ObjectId(broadcast_id)})
        
        if not broadcast:
            await query.edit_message_caption(caption="未找到该广播记录")
            return
        
        # 删除每个群组中的消息
        for message in broadcast['messages']:
            try:
                await context.bot.delete_message(
                    chat_id=message['group_id'],
                    message_id=message['message_id']
                )
            except Exception as e:
                logger.error(f"Error deleting message: {str(e)}")
                continue
        
        # 删除数据库记录
        broadcast_collection.delete_one({'_id': ObjectId(broadcast_id)})
        
        await query.edit_message_caption(caption="广播消息已删除")
        
        # 添加延迟后返回管理菜单
        from asyncio import sleep
        await sleep(2)
        keyboard = [
            [InlineKeyboardButton("🔙返回管理菜单", callback_data='back_to_admin')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_caption(
            caption="操作完成，点击返回管理菜单",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in handle_delete_broadcast: {str(e)}")
        await query.edit_message_caption(caption=f"发生错误，请重试: {str(e)}")