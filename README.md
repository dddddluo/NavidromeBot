# config.json配置项说明
## Telegram Bot 配置
* `TELEGRAM_BOT_TOKEN` - 从 @BotFather 获取机器人令牌

* `OWNER` - 数据库备份和配置文件备份的所有者的tgid，用于发送备份文件

* `ADMIN_ID` - 管理员的 ID /多个 ID 请使用,分隔

* `ALLOWED_GROUP_IDS` - 强制加入的群id

## 数据库配置

##### 可以在宝塔中一键搭建，也可从 https://cloud.mongodb.com 获取

* `DB_NAME` - 数据库名称

* `DB_URL` - 数据库 URL，包含连接字符串

* `DB_BACKUP_DIR` - 数据库备份目录

* `DB_BACKUP_RETENTION_DAYS` - 数据库备份保留天数，单位（天） 如：7

    示例：
    ```
    mongodb://test:数据库密码@127.0.0.1:27017/test?authSource=admin
    ```

## Navidrome API 配置

* `API_BASE_URL` - Navidrome地址，结尾不要有 /

* `NA_ADMIN_USERNAME` - Navidrome-admin用户名

* `NA_ADMIN_PASSWORD` - Navidrome-admin密码

## 保号周期配置

* `TIME_USER` - 保号周期，可配置单位d（天）h（小时）m（分钟）s（秒） 如：7d, 1h, 1m, 1s
* `TIME_USER_ENABLE` - true 是否开启签到保号
## logo配置

* `START_PIC` - Bot发送消息图片，可以设置为http图床链接，也可以是本地文件的路径，如果留空使用内置的默认图片

# 安装与启动
## 没有安装mongo数据库，使用docker-compose启动mongo数据库和bot

- 修改config.json和docker-compose.yml中的配置

- `docker-compose up -d` 启动

## 已有mongo数据库，通过docker启动bot

- 修改config.json文件中的配置

- 拉取镜像 `docker pull dddddluo/navidrome_bot:latest`

- 启动镜像
```
  docker run -d \
  --name navidrome_bot \
  --restart always \
  -v ./config.json:/app/Navidrome/config.json \
  -v ./db_backup:/app/Navidrome/db_backup \
  dddddluo/navidrome_bot:latest
```
# admin 命令
```
/help - 查看帮助信息
/new_code - 创建新的兑换码
/list_code - 查看所有的兑换码
/del_user - 回复消息或tgid删除Navirome账号
/new_line - 新增或修改线路
/del_line - 删除线路
/mm - 查看用户信息
/na_token - 手动刷新Navirome Token
```

[!["Buy Me A Coffee"](https://github.com/user-attachments/assets/3a24f81e-ebc1-4244-9a01-26aecb466214)](https://ko-fi.com/dddddluo)
