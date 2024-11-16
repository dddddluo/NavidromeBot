import bson
import os
from database import db, users_collection
from config import DB_BACKUP_DIR, OWNER
import datetime
import tarfile
from util import get_now_utc
from handlers.permissions import admin_only
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json
from config import config_path, DB_BACKUP_RETENTION_DAYS
import asyncio
import glob
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from services.navidrome_client import navidrome_service, ApiResponse
import logging
from config import config
logger = logging.getLogger(__name__)

async def backup_db_job(context, scheduler=None):
    if scheduler and not config.get('BACKUP_DB_ENABLE', True):
        logger.info("数据库备份已关闭，跳过备份任务")
        return
    await context.bot.send_message(chat_id=OWNER, text="备份数据库ing")
    collections = db.list_collection_names()
    if not os.path.exists(DB_BACKUP_DIR):
        os.makedirs(DB_BACKUP_DIR)
    # 获取当前时间
    now = datetime.datetime.now()
    # 保留期限设置为7天
    retention_period = datetime.timedelta(days=DB_BACKUP_RETENTION_DAYS)

    # 遍历备份目录中的所有文件
    for filename in os.listdir(DB_BACKUP_DIR):
        if 'mongo_backup' in filename and filename.endswith('.tar.gz'):
            # 解析文件中的日期
            file_date_str = filename.split('_')[-1].replace('.tar.gz', '')
            file_date = datetime.datetime.strptime(file_date_str, '%Y%m%d')
            # 如果文件日期加上保留期限仍早于当前日期，则删除该文件
            if now - file_date > retention_period:
                file_path = os.path.join(DB_BACKUP_DIR, filename)
                os.remove(file_path)
        if 'config_' in filename and filename.endswith('.json'):
            # 解析文件中的日期
            file_date_str = filename.split('_')[-1].replace('.json', '')
            file_date = datetime.datetime.strptime(file_date_str, '%Y%m%d')
            # 如果文件日期加上保留期限仍早于当前日期，则删除该文件
            if now - file_date > retention_period:
                file_path = os.path.join(DB_BACKUP_DIR, filename)
                os.remove(file_path)
    tar_file = dump_db(collections, db, DB_BACKUP_DIR)
    dump_config_file = dump_config_json(config_path, os.path.join(
        DB_BACKUP_DIR, f'config_{now.strftime("%Y%m%d")}.json'))
    
    if dump_config_file:
        await context.bot.send_document(chat_id=OWNER, document=dump_config_file)
    await context.bot.send_document(chat_id=OWNER, document=tar_file)
    await context.bot.send_message(chat_id=OWNER, text=f"备份配置文件完成\n文件名：`{dump_config_file}`\n备份数据库完成\n文件名：`{tar_file}`", parse_mode="MarkdownV2")


@admin_only
async def backup_db_callback(update, context):
    await asyncio.gather(update.callback_query.answer(cache_time=5), backup_db_job(context))


def dump_db(collections, db, path):
    """
    MongoDB Dump

    :param collections: Database collections name
    :param db: client[db]
    :param path:
    :return:

    >>> DB_BACKUP_DIR = './backups'
    >>> conn = MongoClient("mongodb://admin:admin@127.0.0.1:27017", authSource="admin")
    >>> db_name = 'my_db'
    >>> collections = ['collection_name', 'collection_name1', 'collection_name2']
    >>> dump(collections, conn, db_name, DB_BACKUP_DIR)
    """
    now = get_now_utc()
    for coll in collections:
        with open(os.path.join(path, f'{coll}.bson'), 'wb+') as f:
            for doc in db[coll].find():
                f.write(bson.BSON.encode(doc))
    # 打包成压缩包
    tar = tarfile.open(os.path.join(
        path, f'mongo_backup_{now.strftime("%Y%m%d")}.tar.gz'), mode="w:gz")
    for coll in collections:
        tar.add(os.path.join(path, f'{coll}.bson'))
    tar.close()
    # remove temp files
    for coll in collections:
        os.remove(os.path.join(path, f'{coll}.bson'))
    return os.path.join(path, f'mongo_backup_{now.strftime("%Y%m%d")}.tar.gz')


def dump_config_json(sourcepath, destpath):
    if os.path.exists(sourcepath):
        with open(sourcepath, 'r') as config_file:
            config_data = json.load(config_file)
            with open(destpath, 'w') as dest_file:
                json.dump(config_data, dest_file, indent=4)
                return destpath
    return None


def restore(path, db):
    """
    MongoDB Restore

    :param path: Database dumped path
    :param db: MongoDB database instance
    :return: None
    """
    try:
        # 只处理.bson文件
        for filename in os.listdir(path):
            if filename.endswith('.bson'):
                # 从文件名中提取集合名（去掉路径和.bson后缀）
                collection_name = os.path.basename(
                    filename).replace('.bson', '')
                file_path = os.path.join(path, filename)

                # 确保文件存在且是文件
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        data = bson.decode_all(f.read())
                        if data:  # 只在有数据时插入
                            try:
                                # 先删除现有集合
                                db[collection_name].drop()
                                # 插入恢复的数据
                                db[collection_name].insert_many(data)
                                logger.info(
                                    f"已恢复集合 {collection_name}，插入了 {len(data)} 条记录")
                            except Exception as e:
                                raise Exception(
                                    f"恢复集合 {collection_name} 时出错：{str(e)}")
    except Exception as e:
        raise Exception(f"恢复数据时出错：{str(e)}")


# 初始化调度器
scheduler = AsyncIOScheduler()


def backup_db_scheduler(dispatcher):
    scheduler.add_job(backup_db_job, 'cron', hour=4,
                      minute=0, second=0, args=[dispatcher, scheduler])
    scheduler.start()


async def list_backup_files(update, context):
    # 确保使用绝对路径
    backup_dir = os.path.abspath(DB_BACKUP_DIR)

    try:
        # 检查目录是否存在
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)

        # 检查目录权限
        if not os.access(backup_dir, os.R_OK | os.W_OK):
            await update.callback_query.answer("备份目录权限不足！", show_alert=True)
            return

        # 使用绝对路径查找备份文件
        backup_files = []
        backup_pattern = os.path.join(backup_dir, 'mongo_backup_*.tar.gz')
        for filename in glob.glob(backup_pattern):
            if os.path.isfile(filename):  # 确保是文件而不是目录
                backup_files.append(os.path.basename(filename))

        if not backup_files:
            await update.callback_query.answer("没有找到可用的备份文件！", show_alert=True)
            return

        # 创建键盘按钮
        keyboard = []
        time_emoji = ["🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"]
        i = 0
        for file in sorted(backup_files, reverse=True):
            keyboard.append([
                InlineKeyboardButton(f"{time_emoji[i]}恢复 {file}", callback_data=f"restore_db_only_{file}")
            ])
            i += 1

        # 添加同步和返回按钮
        keyboard.append([
            InlineKeyboardButton("🔙返回", callback_data='admin_menu'),
            InlineKeyboardButton("📥同步到Navidrome", callback_data="restore_db_sync_navidrome")
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)

        # 更新消息
        await update.callback_query.edit_message_caption(
            caption="请选择要恢复的备份文件和操作方式：\n\n- 恢复：恢复数据库数据\n- 同步到Navidrome：同步数据库用户到Navidrome",
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.callback_query.answer(f"处理备份文件列表时出错", show_alert=True)


@admin_only
async def restore_db_only(update, context):
    query = update.callback_query
    # 从callback_data中提取文件名
    file_name = query.data.split('restore_db_only_')[-1]
    await query.answer("正在恢复数据库，请稍候...", show_alert=True)

    try:
        backup_path = os.path.join(DB_BACKUP_DIR, file_name)
        temp_dir = os.path.join(DB_BACKUP_DIR, "temp_restore")

        # 确保备份文件存在
        if not os.path.isfile(backup_path):
            raise FileNotFoundError(f"备份文件不存在：{backup_path}")

        # 创建临时目录
        if os.path.exists(temp_dir):
            # 清理已存在的临时目录
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(temp_dir)
        os.makedirs(temp_dir)

        # 解压备份文件
        with tarfile.open(backup_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith('.bson'):
                    member.name = os.path.basename(member.name)
                    tar.extract(member, temp_dir)

        # 恢复数据
        restore(temp_dir, db)

        # 清理临时文件
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(temp_dir)

        # 返回结果消息
        result_message = "✅ 数据库恢复已完成！"

        keyboard = [[InlineKeyboardButton(
            "🔙返回管理菜单", callback_data='admin_menu')]]
        await update.callback_query.edit_message_caption(
            caption=result_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        keyboard = [[InlineKeyboardButton(
            "🔙返回管理菜单", callback_data='admin_menu')]]
        await update.callback_query.edit_message_caption(
            caption=f"❌ 数据库恢复失败！\n错误信息：{str(e)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # 确保清理临时目录
        try:
            if os.path.exists(temp_dir):
                for root, dirs, files in os.walk(temp_dir, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(temp_dir)
        except Exception:
            pass


async def restore_db_sync_navidrome(update, context):
    query = update.callback_query
    await query.answer("正在同步数据库用户到Navidrome，请稍候...", show_alert=True)
    existing_users = await navidrome_service.get_users()
    back_to_admin_keyboard = [[InlineKeyboardButton("🔙返回管理菜单", callback_data='admin_menu')]]

    if existing_users.code != 200:
        await query.edit_message_caption(
            caption=f"❌ 同步到Navidrome失败！\n错误信息：{existing_users.message}",
            reply_markup=InlineKeyboardMarkup(back_to_admin_keyboard)
        )
        return
    existing_usernames = {user['userName'] for user in existing_users.data}

    restored_users = users_collection.find({})

    success_count = 0
    fail_count = 0
    for user in restored_users:
        if user['username'] not in existing_usernames:
            try:
                if user.get('user_id') and user.get('username'):
                    password = user.get('password', navidrome_service.generate_random_password())
                    await navidrome_service.create_na_user(
                        username=user['username'],
                        name=user.get('name', user['username']),
                        password=password,
                    )
                    success_count += 1
            except Exception as e:
                fail_count += 1
                logger.error(f"创建用户 {user['username']} 失败: {str(e)}")

    # 返回结果消息
    result_message = "✅ 同步到Navidrome已完成！"
    result_message += f"\n\n同步到Navidrome结果：\n- 成功：{success_count}个用户\n- 失败：{fail_count}个用户"

    await update.callback_query.edit_message_caption(
        caption=result_message,
        reply_markup=InlineKeyboardMarkup(back_to_admin_keyboard)
    )
