#!/usr/bin/env python3
"""

配置文件 config.ini
[bot]
app_id = 你的APP_ID
app_secret = 你的APP_SECRET


项目使用的sdk为https://github.com/wz0388/easybot，没有上pip install需要从github安装
获取聊天的api为https://tracker.2788.pro/api/bfv/chat/server/{serverid}，小电视提供，你可以自行选择循环时间，但是你自己看不要影响别人
app_id与app_secret，从https://q.qq.com 获取，无需实名认证，需要打开全量消息与主动消息
不建议在大群绑定，由于转发的对话导致群聊或机器人被封禁与本人无关
pip install aiosqlite aiohttp configparser
python bot.py

战地V 服务器聊天转发机器人（原始数据记录北京时间）
- 绑定服务器：-bind 别名 serverid
- 开启/关闭转发：-开启转发 / -关闭转发
- 限流：每群每分钟最多 20 条，全局限流 60 条
- 每个服务器每次只处理最新的 20 条消息
- 每条消息按群记录发送状态，避免重复发送
- 原始聊天数据存储时同时保存时间戳和北京时间字符串
"""

import aiosqlite
import aiohttp
import hashlib
import configparser
from datetime import datetime, timezone, timedelta
from easybot import Bot, Model, MessagesModel

# ---------- 配置 ----------
CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE)
APP_ID = config.get("bot", "app_id")
APP_SECRET = config.get("bot", "app_secret")
DB_PATH = "bot_data.db"

bot = Bot(app_id=APP_ID, app_secret=APP_SECRET)


# ---------- 数据库初始化 ----------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # 群绑定信息
        await db.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id TEXT PRIMARY KEY,
                server_id TEXT NOT NULL,
                alias TEXT,
                enabled INTEGER DEFAULT 1
            )
        ''')
        # 原始聊天数据（增加 beijing_time 字段）
        await db.execute('''
            CREATE TABLE IF NOT EXISTS chat_raw (
                server_id TEXT,
                message_hash TEXT,
                timestamp INTEGER,
                beijing_time TEXT,
                player_name TEXT,
                channel INTEGER,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (server_id, message_hash)
            )
        ''')
        # 兼容旧表：如果已存在但没有 beijing_time 列，则添加
        try:
            await db.execute('ALTER TABLE chat_raw ADD COLUMN beijing_time TEXT')
        except aiosqlite.OperationalError:
            pass  # 列已存在

        # 发送记录（每条消息已发送给哪些群）
        await db.execute('''
            CREATE TABLE IF NOT EXISTS sent_messages (
                server_id TEXT,
                message_hash TEXT,
                group_id TEXT,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (server_id, message_hash, group_id)
            )
        ''')
        await db.commit()


# ---------- 数据库辅助函数 ----------
async def get_all_servers():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT DISTINCT server_id FROM groups')
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_enabled_groups_for_server(server_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            'SELECT group_id FROM groups WHERE server_id=? AND enabled=1',
            (server_id,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_alias_for_server_group(server_id, group_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            'SELECT alias FROM groups WHERE server_id=? AND group_id=?',
            (server_id, group_id)
        )
        row = await cursor.fetchone()
        return row[0] if row else server_id


async def insert_raw_message(server_id, msg_hash, timestamp, beijing_time, player_name, channel, content):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            '''INSERT OR IGNORE INTO chat_raw 
               (server_id, message_hash, timestamp, beijing_time, player_name, channel, content) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (server_id, msg_hash, timestamp, beijing_time, player_name, channel, content)
        )
        await db.commit()


async def is_message_sent_to_group(server_id, msg_hash, group_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            'SELECT 1 FROM sent_messages WHERE server_id=? AND message_hash=? AND group_id=?',
            (server_id, msg_hash, group_id)
        )
        return await cursor.fetchone() is not None


async def mark_message_sent_to_group(server_id, msg_hash, group_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR IGNORE INTO sent_messages (server_id, message_hash, group_id) VALUES (?, ?, ?)',
            (server_id, msg_hash, group_id)
        )
        await db.commit()


# ---------- 辅助函数 ----------
def get_message_hash(timestamp, player_name, content):
    raw = f"{timestamp}|{player_name}|{content}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


def format_beijing_time(timestamp):
    dt = datetime.fromtimestamp(timestamp, tz=timezone(timedelta(hours=8)))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ---------- API 调用 ----------
async def fetch_chat_messages(server_id):
    url = f"https://tracker.2788.pro/api/bfv/chat/server/{server_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list):
                        return data
                    else:
                        bot.logger.error(f"API 返回非列表 (server={server_id})")
                        return []
                else:
                    bot.logger.error(f"API 请求失败 (server={server_id}): {resp.status}")
                    return []
        except Exception as e:
            bot.logger.error(f"拉取聊天记录出错 (server={server_id}): {e}")
            return []


# ---------- 定时任务（每分钟） ----------
@bot.on_timer(interval=60)
async def periodic_check(event: Model.TimerEvent):
    bot.logger.info(f"定时检测开始，第 {event.tick_count} 次")

    # 收集所有待发送任务（消息+群）
    pending_tasks = []  # 每个元素: (server_id, msg_hash, timestamp, player_name, content, group_id, alias)

    servers = await get_all_servers()
    for server_id in servers:
        groups = await get_enabled_groups_for_server(server_id)
        if not groups:
            continue

        # 拉取该服务器的聊天记录
        messages = await fetch_chat_messages(server_id)
        if not messages:
            continue

        # 按时间戳降序排列，取最新的 20 条
        messages.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        latest_20 = messages[:20]

        # 处理每条消息
        for msg in latest_20:
            ts = msg.get('timestamp')
            player_name = msg.get('playerName', '未知玩家')
            channel = msg.get('channel', 0)
            content = msg.get('content', '')
            if ts is None:
                continue

            msg_hash = get_message_hash(ts, player_name, content)
            beijing_time = format_beijing_time(ts)

            # 1. 保存原始数据（如果不存在），包含北京时间
            await insert_raw_message(server_id, msg_hash, ts, beijing_time, player_name, channel, content)

            # 2. 检查每个群是否已收到该消息
            for group_id in groups:
                if not await is_message_sent_to_group(server_id, msg_hash, group_id):
                    alias = await get_alias_for_server_group(server_id, group_id)
                    pending_tasks.append({
                        'server_id': server_id,
                        'msg_hash': msg_hash,
                        'timestamp': ts,
                        'player_name': player_name,
                        'content': content,
                        'group_id': group_id,
                        'alias': alias
                    })

    if not pending_tasks:
        bot.logger.info("无新消息需要发送")
        return

    # 按时间升序排列（旧→新）
    pending_tasks.sort(key=lambda x: x['timestamp'])

    # 限流计数器
    group_counters = {}  # group_id -> 发送计数
    global_count = 0
    max_per_group = 20
    max_global = 60

    # 遍历并发送
    for task in pending_tasks:
        group_id = task['group_id']
        # 检查群限流
        if group_counters.get(group_id, 0) >= max_per_group:
            continue
        # 检查全局限流
        if global_count >= max_global:
            break  # 全局已满，停止后续发送

        # 构造发送内容
        send_text = (
            f"服务器[{task['alias']}][{task['server_id']}]\n"
            f"{format_beijing_time(task['timestamp'])}\n"
            f"{task['player_name']}：\n"
            f"{task['content']}"
        )

        try:
            await bot.api.send_group_message(
                group_openid=group_id,
                content=send_text
            )
            bot.logger.info(f"已发送消息 {task['msg_hash'][:8]} 到群 {group_id}")
            # 记录发送成功
            await mark_message_sent_to_group(task['server_id'], task['msg_hash'], group_id)
            group_counters[group_id] = group_counters.get(group_id, 0) + 1
            global_count += 1
        except Exception as e:
            bot.logger.error(f"发送消息到群 {group_id} 失败: {e}")

    bot.logger.info(f"本次共发送 {global_count} 条消息，各群计数: {group_counters}")


# ---------- 启动事件 ----------
@bot.on_startup
async def on_startup(event: Model.StartupEvent):
    bot.logger.info("=" * 50)
    bot.logger.info("机器人启动，初始化数据库...")
    await init_db()
    bot.logger.info("数据库就绪，定时任务已注册（每分钟执行）")
    bot.logger.info(f"启动时间：{event.timestamp}")
    bot.logger.info("=" * 50)


# ---------- 命令处理 ----------
@bot.on_group_full_message
async def handle_all(msg: Model.GroupMessage):
    content = msg.content.strip()
    if not content.startswith('-'):
        return

    parts = content.split()
    cmd = parts[0][1:]  # 去掉 '-'
    group_id = msg.group_id

    if cmd == 'bind':
        if len(parts) < 3:
            await msg.reply("用法: -bind 别名 serverid")
            return
        alias = parts[1]
        server_id = parts[2]
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT OR REPLACE INTO groups (group_id, server_id, alias, enabled)
                VALUES (?, ?, ?, COALESCE((SELECT enabled FROM groups WHERE group_id=?), 1))
            ''', (group_id, server_id, alias, group_id))
            await db.commit()
        await msg.reply(f"已绑定群 {group_id} 到服务器 {server_id}（别名: {alias}）")

    elif cmd == '开启转发':
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT server_id FROM groups WHERE group_id=?', (group_id,))
            if await cursor.fetchone() is None:
                await msg.reply("请先使用 -bind 绑定服务器")
                return
            await db.execute('UPDATE groups SET enabled=1 WHERE group_id=?', (group_id,))
            await db.commit()
        await msg.reply("已开启转发")

    elif cmd == '关闭转发':
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT server_id FROM groups WHERE group_id=?', (group_id,))
            if await cursor.fetchone() is None:
                await msg.reply("请先使用 -bind 绑定服务器")
                return
            await db.execute('UPDATE groups SET enabled=0 WHERE group_id=?', (group_id,))
            await db.commit()
        await msg.reply("已关闭转发")
    elif cmd == 'help':
        try:
            # 步骤1：上传网络图片（通过 URL）
            result = await bot.api.upload_media(
                file_type=1,  # 1=图片
                url="https://pic1.imgdb.cn/i/034KA1AOT4o9isiKiS0ZpR.png",  # 网络图片 URL
                group_openid=msg.group_openid,
            )

            #bot.logger.info(f"上传成功，file_info: {result.file_info}")

            # 步骤2：发送消息引用媒体
            await msg.reply(
                "有问题联系bfv@050820.xyz",
                media_file_info=result.file_info,
            )

        except Exception as e:
            bot.logger.error(f"发送网络图片失败: {e}")
            await msg.reply("❌ 网络图片发送失败")
    else:
        await msg.reply(f"未知命令: {cmd}")


# ---------- 启动 ----------
if __name__ == "__main__":
    bot.start()
