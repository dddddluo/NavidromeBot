# NavidromeBot

基于 Telegram 的 Navidrome 账号管理机器人，支持注册码分发、用户管理、签到保号、数据库备份、开放注册、线路管理和 Bot 内管理面板。

项目地址：https://github.com/dddddluo/NavidromeBot

## 功能特性

- Telegram Bot 管理 Navidrome 用户账号
- 生成、查看、删除注册码
- 支持管理员定向分发邀请码
- 开放注册名额控制
- 用户签到保号，超期自动清理
- 强制加入指定 Telegram 群组
- 线路新增、修改和删除
- 消息广播
- MongoDB 数据库备份与恢复
- Bot 内图形化管理面板

## 镜像

```bash
docker pull dddddluo/navidrome_bot:latest
```

## 快速开始

### 方式一：docker compose 同时启动 MongoDB 和 Bot

适合还没有 MongoDB 的用户。

```bash
mkdir -p navidrome_bot/Navidrome/db_backup navidrome_bot/Navidrome/logs
cd navidrome_bot

curl -o docker-compose.yml https://raw.githubusercontent.com/dddddluo/NavidromeBot/main/docker-compose.yml
curl -o Navidrome/config.json https://raw.githubusercontent.com/dddddluo/NavidromeBot/main/config.json
curl -o Navidrome/logo.jpg https://raw.githubusercontent.com/dddddluo/NavidromeBot/main/Navidrome/logo.jpg
```

编辑 `Navidrome/config.json`，并确保其中的 `DB_URL` 与 `docker-compose.yml` 里的 MongoDB 用户名和密码一致。

启动服务：

```bash
docker compose up -d
```

如果你的环境仍使用旧版 Compose，也可以使用：

```bash
docker-compose up -d
```

### 方式二：已有 MongoDB，只启动 Bot

```bash
mkdir -p navidrome_bot/Navidrome/db_backup navidrome_bot/Navidrome/logs
cd navidrome_bot

curl -o Navidrome/config.json https://raw.githubusercontent.com/dddddluo/NavidromeBot/main/config.json
curl -o Navidrome/logo.jpg https://raw.githubusercontent.com/dddddluo/NavidromeBot/main/Navidrome/logo.jpg
```

编辑 `Navidrome/config.json`，将 `DB_URL` 指向已有 MongoDB。

启动容器：

```bash
docker run -d \
  --name navidrome_bot \
  --restart always \
  -v ./Navidrome/config.json:/app/Navidrome/config.json \
  -v ./Navidrome/db_backup:/app/Navidrome/db_backup \
  -v ./Navidrome/logo.jpg:/app/Navidrome/logo.jpg \
  -v ./Navidrome/logs:/app/Navidrome/logs \
  dddddluo/navidrome_bot:latest
```

## 配置文件

容器启动时读取：

```text
/app/Navidrome/config.json
```

推荐将宿主机配置文件挂载到该路径，避免升级镜像时丢失配置。

配置示例：

```json
{
  "TELEGRAM_BOT_TOKEN": "从 @BotFather 获取的 Bot Token",
  "TELEGRAM_BOT_NAME": "your_bot_username",
  "OWNER": 111111111,
  "ADMIN_ID": [111111111, 222222222],
  "ALLOWED_GROUP_IDS": [-1001234567890],
  "GROUP_INVITE_LINK": "https://t.me/your_group",
  "LOG_GROUP_ID": -1001234567890,

  "DB_NAME": "bot",
  "DB_URL": "mongodb://bot:botpwd@mongo:27017/bot?authSource=admin",
  "DB_BACKUP_DIR": "/app/Navidrome/db_backup",
  "DB_BACKUP_RETENTION_DAYS": 7,
  "BACKUP_DB_ENABLE": true,

  "API_BASE_URL": "http://your-navidrome-host:4533",
  "NA_ADMIN_USERNAME": "admin",
  "NA_ADMIN_PASSWORD": "your_password",

  "TIME_USER": "7d",
  "TIME_USER_ENABLE": true,

  "START_PIC": ""
}
```

### 配置项说明

| 配置项 | 说明 |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token，从 `@BotFather` 获取 |
| `TELEGRAM_BOT_NAME` | Bot 用户名，不需要包含 `@` |
| `OWNER` | 所有者 Telegram ID，用于接收备份文件等 |
| `ADMIN_ID` | 管理员 Telegram ID 列表 |
| `ALLOWED_GROUP_IDS` | 允许或要求加入的 Telegram 群组 ID 列表 |
| `GROUP_INVITE_LINK` | 群组邀请链接 |
| `LOG_GROUP_ID` | 日志推送群组 ID，可选 |
| `DB_NAME` | MongoDB 数据库名 |
| `DB_URL` | MongoDB 连接字符串 |
| `DB_BACKUP_DIR` | 数据库备份目录，容器内建议使用 `/app/Navidrome/db_backup` |
| `DB_BACKUP_RETENTION_DAYS` | 备份文件保留天数 |
| `BACKUP_DB_ENABLE` | 是否开启定时数据库备份 |
| `API_BASE_URL` | Navidrome 服务地址，末尾不要加 `/` |
| `NA_ADMIN_USERNAME` | Navidrome 管理员用户名 |
| `NA_ADMIN_PASSWORD` | Navidrome 管理员密码 |
| `TIME_USER` | 签到保号周期，支持 `s`、`m`、`h`、`d` |
| `TIME_USER_ENABLE` | 是否开启签到保号 |
| `START_PIC` | Bot 欢迎图片，可填 HTTP 链接或容器内本地路径；留空使用默认图片 |

## 持久化目录

建议至少挂载以下路径：

| 宿主机路径 | 容器路径 | 说明 |
| --- | --- | --- |
| `./Navidrome/config.json` | `/app/Navidrome/config.json` | Bot 配置文件 |
| `./Navidrome/db_backup` | `/app/Navidrome/db_backup` | 数据库备份目录 |
| `./Navidrome/logs` | `/app/Navidrome/logs` | 日志目录 |
| `./Navidrome/logo.jpg` | `/app/Navidrome/logo.jpg` | 默认欢迎图片，可选 |

## 常用命令

查看日志：

```bash
docker logs -f navidrome_bot
```

重启容器：

```bash
docker restart navidrome_bot
```

停止并删除容器：

```bash
docker stop navidrome_bot
docker rm navidrome_bot
```

升级镜像：

```bash
docker pull dddddluo/navidrome_bot:latest
docker stop navidrome_bot
docker rm navidrome_bot
docker run -d \
  --name navidrome_bot \
  --restart always \
  -v ./Navidrome/config.json:/app/Navidrome/config.json \
  -v ./Navidrome/db_backup:/app/Navidrome/db_backup \
  -v ./Navidrome/logo.jpg:/app/Navidrome/logo.jpg \
  -v ./Navidrome/logs:/app/Navidrome/logs \
  dddddluo/navidrome_bot:latest
```

使用 docker compose 升级：

```bash
docker compose pull
docker compose up -d
```

## Bot 命令

| 命令 | 说明 |
| --- | --- |
| `/start` | 打开主面板 |
| `/help` | 查看帮助信息 |
| `/new_code [数量]` | 生成注册码，默认生成 1 个 |
| `/list_code` | 查看所有注册码 |
| `/del_user <tgid>` | 删除指定用户的 Navidrome 账号 |
| `/new_line <名称> <地址>` | 新增或修改线路 |
| `/del_line <名称>` | 删除线路 |
| `/mm` | 查看用户信息 |
| `/na_token` | 手动刷新 Navidrome Token |

## 安全建议

- 修改 `docker-compose.yml` 中默认 MongoDB 用户名和密码。
- 如果不需要外部访问 MongoDB，请删除 MongoDB 的 `ports` 映射，或改为 `127.0.0.1:27017:27017`。
- 不要公开 `config.json`，其中包含 Telegram Bot Token、数据库连接串和 Navidrome 管理员密码。
- 建议通过反向代理或内网地址访问 Navidrome API。

## 注意事项

- `API_BASE_URL` 末尾不要添加 `/`。
- 使用 compose 内置 MongoDB 时，`DB_URL` 中的主机名应为 `mongo`。
- 使用外部 MongoDB 时，请确认容器能够访问对应地址和端口。
- 升级镜像前请确保 `config.json`、`db_backup` 和 `logs` 已通过卷挂载持久化。
