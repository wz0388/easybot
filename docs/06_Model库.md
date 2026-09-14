# Model 库

本章用于整理 EasyBot 当前 SDK 中与事件处理最相关的模型结构，帮助你在编写事件回调、命令处理器和生命周期逻辑时，快速判断 callback 会收到什么对象、这些对象有哪些字段，以及常见嵌套结构应该如何理解。

EasyBot 的 `Model` 主要用于两件事：

- 给事件 callback 提供明确的类型提示
- 帮你快速确认事件字段结构，降低字段名写错和结构理解错误的概率

同时需要注意：

- 本章主线是**事件回调会直接收到的模型**
- 主动构造发送消息内容时，应使用 `MessagesModel.*`，而不是 `Model.*`
- 文中部分“子结构”只是字段结构说明，不代表它们一定还能通过 `Model.xxx` 单独导入

***

## 一、Model

**模块**：`easybot.models`  
**导入**：`from easybot import Model`

### 1.1 基本用法

```python
from easybot import Bot, Model

bot = Bot(app_id="your_app_id", app_secret="your_app_secret")

@bot.on_guild_message
async def handle(msg: Model.GuildMessage):
    if "你好" in msg.treated_msg:
        await msg.reply("你好，世界")
```

当 callback 标注成正确的 `Model` 类型后，IDE 通常可以直接提示字段和方法。

### 1.2 callback 类型规则

- 单事件装饰器会传入固定的具体模型
- 聚合事件装饰器建议标注为 `Model.BaseModel`
- `on_command` / `before_command` 只会传入四种消息模型
- `on_startup` / `on_shutdown` / `on_timer` 会传入独立的生命周期模型

### 1.3 命令场景与消息模型

| `valid_scenes` | callback 类型 |
| --- | --- |
| `CommandValidScenes.GUILD` | `Model.GuildMessage` |
| `CommandValidScenes.GROUP` | `Model.GroupMessage` |
| `CommandValidScenes.C2C` | `Model.C2CMessage` |
| `CommandValidScenes.DM` | `Model.DirectMessage` |
| 多场景组合 | `Model.Message`（四种消息的联合类型别名） |

### 1.4 `Model` 与 `MessagesModel` 的区别

| 场景 | 推荐类型 |
| --- | --- |
| 事件回调参数 | `Model.*` |
| 命令 / 预处理器 callback 参数 | `Model.*` 中的消息模型 |
| 主动构造发送消息内容 | `MessagesModel.*` |

例如：

```python
from easybot import MessagesModel

@bot.on_group_message
async def handle(msg: Model.GroupMessage):
    await msg.reply(MessagesModel.MessageEmbed(title="收到群聊消息"))
```

***

## 二、数据结构速查

| 场景 | 主要装饰器 | callback 类型 |
| --- | --- | --- |
| 频道消息 | `@bot.on_guild_message` / `@bot.on_guild_full_message` | `Model.GuildMessage` |
| 群聊消息 | `@bot.on_at_group_message` / `@bot.on_group_message` | `Model.GroupMessage` |
| 单聊消息 | `@bot.on_c2c_message` | `Model.C2CMessage` |
| 频道私信 | `@bot.on_direct_message` | `Model.DirectMessage` |
| 消息删除 | `@bot.on_message_delete` / `@bot.on_public_message_delete` / `@bot.on_direct_message_delete` | `Model.MessageDelete` |
| 消息审核 | `@bot.on_message_audit_pass` / `@bot.on_message_audit_reject` | `Model.MessageAudited` |
| 表态事件 | `@bot.on_reaction_add` / `@bot.on_reaction_remove` | `Model.MessageReaction` |
| 互动事件 | `@bot.on_interaction` | `Model.Interaction` |
| 频道事件 | `@bot.on_guild_*` | `Model.Guild` |
| 子频道事件 | `@bot.on_channel_*` | `Model.Channel` |
| 成员事件 | `@bot.on_guild_member_*` | `Model.MemberWithGuildID` |
| 群聊事件 | `@bot.on_group_*` | `Model.GroupEvent` |
| 好友事件 | `@bot.on_friend_*` / `@bot.on_c2c_msg_*` | `Model.FriendEvent` |
| 论坛主题 | `@bot.on_forum_thread_*` | `Model.Thread` |
| 论坛评论 | `@bot.on_forum_post_*` | `Model.Post` |
| 论坛回复 | `@bot.on_forum_reply_*` | `Model.Reply` |
| 论坛审核结果 | `@bot.on_forum_publish_audit_result` | `Model.AuditResult` |
| 开放论坛事件 | `@bot.on_open_forum_*` | `Model.OpenForumEvent` |
| 音频事件 | `@bot.on_audio_*` | `Model.AudioAction` |
| 音视频频道成员 | `@bot.on_audio_or_live_channel_member_*` | `Model.LiveChannelMember` |
| 聚合事件 | `@bot.on_all_intent_events` 等 | `Model.BaseModel` |
| 生命周期 | `@bot.on_startup` / `@bot.on_shutdown` / `@bot.on_timer(...)` | 对应 `Model.StartupEvent` / `Model.ShutdownEvent` / `Model.TimerEvent` |

***

## 三、公共基类

### 3.1 `BaseModel`

大多数事件模型都继承自 `BaseModel`。

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `event_id` | `str` | 事件 ID |
| `seq` | `int \| None` | 事件序号 |
| `opcode` | `int` | Gateway 操作码 |
| `event_type` | `str` | 事件类型 |

常用能力：

| 成员 | 说明 |
| --- | --- |
| `from_dict(data)` | 从字典构造模型 |
| `to_dict()` | 模型转字典 |
| `reply(...)` | 对支持 reply strategy 的事件快速回复 |
| `api` | 获取关联 API |

`reply()` 的常见调用形式：

```python
await msg.reply(
    content=None,
    reference=False,
    image=None,
    file_image=None,
    media_file_info=None,
    msg_type=None,
    is_wakeup=False,
    channel_id=None,
)
```

其中 `channel_id` 主要用于 `GUILD_MEMBER_*` 这类没有默认回复子频道的被动事件。

### 3.2 `MessageBase`

所有消息事件都继承自 `MessageBase`。

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | 消息 ID |
| `content` | `str` | 消息原始内容 |
| `timestamp` | `str` | 消息时间 |
| `author` | `Author \| None` | 发送者结构 |
| `attachments` | `list[Attachment]` | 附件结构列表 |
| `treated_msg` | `str` | 处理后的消息内容 |

附加能力：

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `msg_id` | `str` | `id` 的别名 |
| `reply(...)` | 异步方法 | 快速回复 |
| `api` | `API \| None` | API 入口 |

### 3.3 生命周期模型

`StartupEvent`、`ShutdownEvent`、`TimerEvent` 是独立 dataclass，不继承 `BaseModel`。

**StartupEvent**

| 字段名 | 类型 |
| --- | --- |
| `bot` | `Bot` |
| `timestamp` | `float` |

**ShutdownEvent**

| 字段名 | 类型 |
| --- | --- |
| `bot` | `Bot` |
| `timestamp` | `float` |

**TimerEvent**

| 字段名 | 类型 |
| --- | --- |
| `bot` | `Bot` |
| `timestamp` | `float` |
| `tick_count` | `int` |

***

## 四、频道与成员事件

### 4.1 `Guild`

来源装饰器：

- `@bot.on_guild_create`
- `@bot.on_guild_update`
- `@bot.on_guild_delete`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | 频道 ID |
| `name` | `str` | 频道名 |
| `icon` | `str` | 频道头像 URL |
| `owner_id` | `str` | 频道主 ID |
| `owner` | `bool` | 是否为频道主 |
| `member_count` | `int` | 当前成员数 |
| `max_members` | `int` | 最大成员数 |
| `description` | `str` | 频道简介 |
| `joined_at` | `str` | 机器人加入频道时间 |

### 4.2 `Channel`

来源装饰器：

- `@bot.on_channel_create`
- `@bot.on_channel_update`
- `@bot.on_channel_delete`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | 子频道 ID |
| `guild_id` | `str` | 所属频道 ID |
| `name` | `str` | 子频道名 |
| `type` | `int` | 子频道类型 |
| `sub_type` | `int` | 子频道子类型 |
| `position` | `int` | 排序值 |
| `parent_id` | `str` | 所属分组 ID |
| `owner_id` | `str` | 频道主 ID |
| `private_type` | `int` | 私密类型 |
| `speak_permission` | `int` | 发言权限 |
| `permissions` | `str` | 当前权限 |
| `application_id` | `str \| None` | 应用子频道标识 |
| `op_user_id` | `str \| None` | 操作人 ID |

子频道类型常量：

| 常量 | 值 |
| --- | --- |
| `TYPE_TEXT` | `0` |
| `TYPE_VOICE` | `2` |
| `TYPE_CATEGORY` | `4` |
| `TYPE_LIVE` | `10005` |
| `TYPE_APP` | `10006` |
| `TYPE_FORUM` | `10007` |

### 4.3 `MemberWithGuildID`

来源装饰器：

- `@bot.on_guild_member_add`
- `@bot.on_guild_member_update`
- `@bot.on_guild_member_remove`

`MemberWithGuildID` 继承 `Member`，并新增：

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `guild_id` | `str` | 频道 ID |
| `op_user_id` | `str \| None` | 操作人 ID |

结构：`Member`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `user` | `Author \| None` | 用户结构 |
| `nick` | `str` | 频道昵称 |
| `roles` | `list[str]` | 身份组 ID 列表 |
| `joined_at` | `str` | 入群时间 |

结构：`Author`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | 用户 ID |
| `username` | `str` | 用户名 |
| `avatar` | `str` | 头像 URL |
| `bot` | `bool` | 是否机器人 |
| `member_openid` | `str \| None` | 群成员 openid |
| `user_openid` | `str \| None` | 用户 openid |
| `union_openid` | `str \| None` | union_openid |
| `union_user_account` | `str \| None` | union 用户标识 |

### 4.4 `GroupMember`

来源：`GET /v2/groups/{group_openid}/members`（群成员列表）

QQ 群成员对象（基于 openid），与频道成员 `Member` 区分。

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `member_openid` | `str` | 成员 OpenID |
| `username` | `str` | 用户昵称 |
| `member_role` | `str` | 群成员角色：`member` 普通成员 / `owner` 群主 / `admin` 管理员 |
| `bot` | `bool` | 是否机器人 |
| `joined_at` | `str` | 入群时间戳（RFC3339 格式） |
| `union_openid` | `str \| None` | 用户在应用/开放平台下的统一标识（如有） |

便捷属性：

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `is_owner` | `bool` | 是否为群主 |
| `is_admin` | `bool` | 是否为管理员或群主 |

### 4.5 `GroupMembersResponse`

来源：`GET /v2/groups/{group_openid}/members`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `members` | `list[GroupMember]` | 成员列表，每次最多返回 30 条 |
| `next_cursor` | `str` | 下一页游标，空串表示已到末页 |
| `is_end` | `bool`（属性） | 是否已到末页 |

角色常量 `Model.GroupMemberRole`：`MEMBER` / `OWNER` / `ADMIN`

***

## 五、消息事件

### 5.1 `GuildMessage`

来源装饰器：

- `@bot.on_guild_message`
- `@bot.on_guild_full_message`
- `@bot.on_command(..., valid_scenes=CommandValidScenes.GUILD)`
- `@bot.before_command(..., valid_scenes=CommandValidScenes.GUILD)`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `channel_id` | `str` | 子频道 ID |
| `guild_id` | `str` | 频道 ID |
| `content` | `str` | 消息内容 |
| `id` | `str` | 消息 ID |
| `timestamp` | `str` | 消息时间 |
| `edited_timestamp` | `str \| None` | 编辑时间 |
| `author` | `Author \| None` | 作者结构 |
| `member` | `Member \| None` | 成员结构 |
| `attachments` | `list[Attachment]` | 附件结构 |
| `mentions` | `list[Author]` | @用户列表 |
| `message_reference` | `MessageReference \| None` | 引用消息结构 |
| `seq` | `int \| None` | 消息序号 |
| `seq_in_channel` | `str \| None` | 子频道内消息序号 |
| `tts` | `bool` | 是否 TTS |
| `mention_everyone` | `bool` | 是否 @全体 |
| `pinned` | `bool` | 是否精华消息 |
| `type` | `int` | 消息类型 |
| `flags` | `int` | 消息标记 |
| `treated_msg` | `str` | 处理后的消息 |

结构：`Attachment`

| 字段名 | 类型 |
| --- | --- |
| `url` | `str` |
| `content_type` | `str \| None` |
| `filename` | `str \| None` |
| `height` | `int \| None` |
| `width` | `int \| None` |
| `size` | `int \| None` |
| `voice_wav_url` | `str \| None` |
| `asr_refer_text` | `str \| None` |

结构：`MessageReference`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `message_id` | `str` | 被引用的消息 ID |

### 5.2 `GroupMessage`

来源装饰器：

- `@bot.on_at_group_message`
- `@bot.on_group_message`
- `@bot.on_command(..., valid_scenes=CommandValidScenes.GROUP)`
- `@bot.before_command(..., valid_scenes=CommandValidScenes.GROUP)`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `group_openid` | `str` | 群 openid |
| `group_id` | `str` | 群 ID |
| `id` | `str` | 消息 ID |
| `content` | `str` | 消息内容 |
| `timestamp` | `str` | 消息时间 |
| `author` | `Author \| None` | 作者结构 |
| `attachments` | `list[Attachment]` | 附件结构 |
| `message_scene` | `MessageScene \| None` | 消息场景结构 |
| `message_type` | `int` | 消息类型（103 表示引用消息） |
| `msg_elements` | `list[MessageElement]` | 消息元素列表（包含引用的消息内容） |
| `treated_msg` | `str` | 处理后的消息 |

结构：`MessageScene`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ext` | `list[str]` | 扩展信息列表 |
| `source` | `str` | 来源 |

结构：`MessageElement`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `content` | `str` | 引用的消息内容 |
| `msg_idx` | `str` | 消息索引 |
| `attachments` | `list[Attachment]` | 附件列表（图片、视频等） |

### 5.3 `C2CMessage`

来源装饰器：

- `@bot.on_c2c_message`
- `@bot.on_command(..., valid_scenes=CommandValidScenes.C2C)`
- `@bot.before_command(..., valid_scenes=CommandValidScenes.C2C)`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | 消息 ID |
| `content` | `str` | 消息内容 |
| `timestamp` | `str` | 消息时间 |
| `author` | `Author \| None` | 作者结构 |
| `attachments` | `list[Attachment]` | 附件结构 |
| `message_scene` | `MessageScene \| None` | 消息场景结构 |
| `message_type` | `int` | 消息类型（103 表示引用消息） |
| `msg_elements` | `list[MessageElement]` | 消息元素列表（包含引用的消息内容） |
| `treated_msg` | `str` | 处理后的消息 |

### 5.4 `DirectMessage`

来源装饰器：

- `@bot.on_direct_message`
- `@bot.on_command(..., valid_scenes=CommandValidScenes.DM)`
- `@bot.before_command(..., valid_scenes=CommandValidScenes.DM)`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `channel_id` | `str` | 私信子频道 ID |
| `guild_id` | `str` | 私信频道 ID |
| `member` | `Member \| None` | 成员结构 |
| `direct_message` | `bool` | 是否为私信标志 |
| `message_reference` | `MessageReference \| None` | 消息引用结构 |
| `src_guild_id` | `str` | 源频道 ID |
| `id` | `str` | 消息 ID |
| `content` | `str` | 消息内容 |
| `timestamp` | `str` | 消息时间 |
| `author` | `Author \| None` | 作者结构 |
| `attachments` | `list[Attachment]` | 附件结构 |
| `treated_msg` | `str` | 处理后的消息 |

### 5.5 `MessageDelete`

来源装饰器：

- `@bot.on_message_delete`
- `@bot.on_public_message_delete`
- `@bot.on_direct_message_delete`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `message` | `GuildMessage \| None` | 被撤回消息 |
| `op_user` | `Author \| None` | 操作人 |

### 5.6 `MessageAudited`

来源装饰器：

- `@bot.on_message_audit_pass`
- `@bot.on_message_audit_reject`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `audit_id` | `str` | 审核 ID |
| `message_id` | `str` | 消息 ID |
| `guild_id` | `str` | 频道 ID |
| `channel_id` | `str` | 子频道 ID |
| `audit_time` | `str` | 审核时间 |
| `create_time` | `str` | 消息创建时间 |
| `seq_in_channel` | `str` | 子频道消息序号 |

### 5.7 `MessageReaction`

来源装饰器：

- `@bot.on_reaction_add`
- `@bot.on_reaction_remove`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `user_id` | `str` | 表态用户 ID |
| `guild_id` | `str` | 频道 ID |
| `channel_id` | `str` | 子频道 ID |
| `target` | `ReactionTarget \| None` | 表态目标结构 |
| `emoji` | `Emoji \| None` | 表情结构 |

结构：`ReactionTarget`

| 字段名 | 类型 |
| --- | --- |
| `id` | `str` |
| `type` | `int` |

结构：`Emoji`

| 字段名 | 类型 |
| --- | --- |
| `id` | `str` |
| `type` | `int` |

### 5.8 `Interaction`

来源装饰器：

- `@bot.on_interaction`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | 互动 ID |
| `type` | `int` | 互动类型 |
| `scene` | `str` | 场景 |
| `chat_type` | `int` | 会话类型 |
| `timestamp` | `str` | 时间 |
| `guild_id` | `str \| None` | 频道 ID |
| `channel_id` | `str \| None` | 子频道 ID |
| `user_openid` | `str \| None` | 用户 openid |
| `group_openid` | `str \| None` | 群 openid |
| `group_member_openid` | `str \| None` | 群成员 openid |
| `data` | `InteractionData \| None` | 互动数据结构 |
| `version` | `int` | 版本 |

结构：`InteractionData`

| 字段名 | 类型 |
| --- | --- |
| `type` | `int` |
| `resolved` | `InteractionDataResolved \| None` |

结构：`InteractionDataResolved`

| 字段名 | 类型 |
| --- | --- |
| `button_data` | `str` |
| `button_id` | `str` |
| `user_id` | `str` |
| `message_id` | `str` |

Interaction 内置 ClassVar 常量：

| 常量 | 值 | 说明 |
| --- | --- | --- |
| `TYPE_BUTTON` | `11` | 按钮类型互动 |
| `TYPE_MENU` | `12` | 菜单类型互动 |
| `SCENE_C2C` | `"c2c"` | 单聊场景 |
| `SCENE_GROUP` | `"group"` | 群聊场景 |
| `SCENE_GUILD` | `"guild"` | 频道场景 |
| `CHAT_TYPE_GUILD` | `0` | 频道会话类型 |
| `CHAT_TYPE_GROUP` | `1` | 群聊会话类型 |
| `CHAT_TYPE_C2C` | `2` | 单聊会话类型 |

***

## 六、群聊与好友事件

### 6.1 `GroupEvent`

来源装饰器：

- `@bot.on_group_add`
- `@bot.on_group_delete`
- `@bot.on_group_msg_reject`
- `@bot.on_group_msg_receive`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `timestamp` | `int` | 时间戳 |
| `group_openid` | `str` | 群 openid |
| `op_member_openid` | `str` | 操作成员 openid |

### 6.2 `FriendEvent`

来源装饰器：

- `@bot.on_friend_add`
- `@bot.on_friend_delete`
- `@bot.on_c2c_msg_reject`
- `@bot.on_c2c_msg_receive`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `timestamp` | `int` | 时间戳 |
| `openid` | `str` | 用户 openid |
| `scene` | `int \| None` | 场景值 |
| `scene_param` | `str \| None` | 场景参数 |

### 6.3 `GroupJoinRequestEvent`

来源装饰器：`@bot.on_group_join_request`（事件 `GROUP_JOIN_REQUEST`，Intent `GROUP_MEMBER_EVENT`）

> 只有当机器人是群管理员时才可以收到此事件。

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `group_openid` | `str` | 群 OpenID |
| `join_request_id` | `str` | 申请 ID，审批时需回传 |
| `risk_tips` | `str` | 安全提示语 |
| `top_tips` | `str` | 顶部安全提示语 |
| `union_openid` | `str \| None` | 用户在应用/开放平台下的统一标识 |
| `member_openid` | `str` | 申请人 openid |
| `username` | `str` | 申请人昵称 |
| `apply_at` | `str` | 申请时间戳（RFC3339） |
| `apply_source` | `str` | 申请来源：`self_apply` 主动申请 / `invited` 被邀请 |
| `invited_by` | `str` | 邀请人 openid（`apply_source=invited` 时有效） |
| `bot` | `bool` | 是否为机器人账号 |
| `verify_info` | `VerifyInfo \| None` | 入群验证方式 |
| `auto_approved` | `AutoApproved \| None` | 自动审批通过的扩展信息 |

便捷属性：

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `is_invited` | `bool` | 是否由其他成员邀请入群 |
| `is_auto_approved` | `bool` | 是否由自动审批策略直接通过 |

结构：`VerifyInfo`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `method` | `str` | 验证方式：`verify_message` / `admin_review_qa` |
| `verify_message` | `str` | 验证消息内容 |
| `review_qa_list` | `list[ReviewQA]` | 问答列表 |

结构：`ReviewQA`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `question` | `str` | 管理员设置的问题 |
| `answer` | `str` | 申请人填写的答案 |

结构：`AutoApproved`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `strategy_id` | `str` | 自动审批通过的策略 ID |

### 6.4 `GroupMemberEvent`

来源装饰器：

- `@bot.on_group_member_add`（`GROUP_MEMBER_ADD`，群成员加入）
- `@bot.on_group_member_remove`（`GROUP_MEMBER_REMOVE`，群成员退出）

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `timestamp` | `int` | 事件时间戳（Unix 秒） |
| `group_openid` | `str` | 群 OpenID |
| `member_openid` | `str` | 变动成员的 OpenID |
| `user_openid` | `str` | 变动成员的用户 OpenID（可能为空） |

### 6.5 `SubscribeMessageStatusEvent`

来源装饰器：`@bot.on_subscribe_message_status`（事件 `SUBSCRIBE_MESSAGE_STATUS`，Intent `GROUP_AND_C2C_EVENT`）

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `group_openid` | `str` | 群 OpenID（群订阅场景时有值） |
| `openid` | `str` | 用户 OpenID（个人订阅场景时有值） |
| `result` | `list[SubscribeMsgTemplateResult]` | 各模板的授权结果列表 |

方法：`find_template(template_id)` 可按平台模板 ID 查找授权结果。

结构：`SubscribeMsgTemplateResult`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `template_id` | `int` | 平台提供的订阅模板 ID |
| `custom_template_id` | `str` | 自定义订阅模板 ID |
| `op` | `int` | 用户操作：`1` 允许订阅 / `2` 拒绝订阅 |
| `subscribe_id` | `str` | 订阅 ID，发送订阅消息时使用 |
| `subscribe_ts` | `int` | 订阅操作时间戳（Unix 秒） |
| `update_ts` | `int` | 状态最后更新时间戳（Unix 秒） |

便捷属性：`is_allowed`（是否允许订阅）。操作常量见 `Model.SubscribeMessageOp`。

***

## 七、论坛事件

### 7.1 `Thread`

来源装饰器：

- `@bot.on_forum_thread_create`
- `@bot.on_forum_thread_update`
- `@bot.on_forum_thread_delete`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `guild_id` | `str` | 频道 ID |
| `channel_id` | `str` | 子频道 ID |
| `author_id` | `str` | 作者 ID |
| `thread_info` | `ThreadInfo \| None` | 帖子信息结构 |

结构：`ThreadInfo`

| 字段名 | 类型 |
| --- | --- |
| `thread_id` | `str` |
| `title` | `str` |
| `content` | `str` |
| `date_time` | `str` |

### 7.2 `Post`

来源装饰器：

- `@bot.on_forum_post_create`
- `@bot.on_forum_post_delete`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `guild_id` | `str` | 频道 ID |
| `channel_id` | `str` | 子频道 ID |
| `author_id` | `str` | 作者 ID |
| `post_info` | `PostInfo \| None` | 评论信息结构 |

结构：`PostInfo`

| 字段名 | 类型 |
| --- | --- |
| `thread_id` | `str` |
| `post_id` | `str` |
| `content` | `list[RichText]` |
| `date_time` | `str` |

### 7.3 `Reply`

来源装饰器：

- `@bot.on_forum_reply_create`
- `@bot.on_forum_reply_delete`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `guild_id` | `str` | 频道 ID |
| `channel_id` | `str` | 子频道 ID |
| `author_id` | `str` | 作者 ID |
| `reply_info` | `ReplyInfo \| None` | 回复信息结构 |

结构：`ReplyInfo`

| 字段名 | 类型 |
| --- | --- |
| `thread_id` | `str` |
| `post_id` | `str` |
| `reply_id` | `str` |
| `content` | `list[RichText]` |
| `date_time` | `str` |

### 7.4 `AuditResult`

来源装饰器：

- `@bot.on_forum_publish_audit_result`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `guild_id` | `str` | 频道 ID |
| `channel_id` | `str` | 子频道 ID |
| `author_id` | `str` | 作者 ID |
| `type` | `int` | 审核类型 |
| `result` | `int` | 审核结果 |
| `err_msg` | `str` | 错误信息 |
| `thread_id` | `str \| None` | 主题 ID |
| `post_id` | `str \| None` | 评论 ID |
| `reply_id` | `str \| None` | 回复 ID |

审核类型常量：

| 常量 | 值 |
| --- | --- |
| `TYPE_PUBLISH_THREAD` | `1` |
| `TYPE_PUBLISH_POST` | `2` |
| `TYPE_PUBLISH_REPLY` | `3` |

### 7.5 `OpenForumEvent`

来源装饰器：

- `@bot.on_open_forum_thread_create`
- `@bot.on_open_forum_thread_update`
- `@bot.on_open_forum_thread_delete`
- `@bot.on_open_forum_post_create`
- `@bot.on_open_forum_post_delete`
- `@bot.on_open_forum_reply_create`
- `@bot.on_open_forum_reply_delete`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `guild_id` | `str` | 频道 ID |
| `channel_id` | `str` | 子频道 ID |
| `author_id` | `str` | 作者 ID |

### 7.6 论坛富文本结构：`RichText`

`PostInfo.content` 和 `ReplyInfo.content` 使用 `list[RichText]` 表示。

| 字段名 | 类型 |
| --- | --- |
| `type` | `int` |
| `text_info` | `TextInfo \| None` |
| `at_info` | `AtInfo \| None` |
| `url_info` | `URLInfo \| None` |
| `emoji_info` | `EmojiInfo \| None` |
| `channel_info` | `ChannelInfo \| None` |

`RichText.type` 常量：

| 常量 | 值 |
| --- | --- |
| `TYPE_TEXT` | `1` |
| `TYPE_AT` | `2` |
| `TYPE_URL` | `3` |
| `TYPE_EMOJI` | `4` |
| `TYPE_CHANNEL` | `5` |
| `TYPE_VIDEO` | `10` |
| `TYPE_IMAGE` | `11` |

结构：`TextInfo`

| 字段名 | 类型 |
| --- | --- |
| `text` | `str` |

结构：`AtInfo`

| 字段名 | 类型 |
| --- | --- |
| `type` | `int` |
| `user_info` | `AtUserInfo \| None` |
| `role_info` | `AtRoleInfo \| None` |
| `guild_info` | `AtGuildInfo \| None` |

`AtInfo.type` 常量：

| 常量 | 值 |
| --- | --- |
| `TYPE_EXPLICIT_USER` | `1` |
| `TYPE_ROLE_GROUP` | `2` |
| `TYPE_GUILD` | `3` |

结构：`AtUserInfo`

| 字段名 | 类型 |
| --- | --- |
| `id` | `str` |
| `nick` | `str` |

结构：`AtRoleInfo`

| 字段名 | 类型 |
| --- | --- |
| `role_id` | `int` |
| `name` | `str` |
| `color` | `int` |

结构：`AtGuildInfo`

| 字段名 | 类型 |
| --- | --- |
| `guild_id` | `str` |
| `guild_name` | `str` |

结构：`URLInfo`

| 字段名 | 类型 |
| --- | --- |
| `url` | `str` |
| `display_text` | `str` |

结构：`EmojiInfo`

| 字段名 | 类型 |
| --- | --- |
| `id` | `str` |
| `type` | `str` |
| `name` | `str` |
| `url` | `str` |

结构：`ChannelInfo`

| 字段名 | 类型 |
| --- | --- |
| `channel_id` | `int` |
| `channel_name` | `str` |

### 7.7 论坛正文解析：`ThreadContent`

`Thread.thread_info.content` 当前是 JSON 字符串，解析后可转换成 `Model.ThreadContent`：

```python
import json
from easybot import Model

content_data = json.loads(thread.thread_info.content)
thread_content = Model.ThreadContent.from_dict(content_data)
```

结构：`ThreadContent`

| 字段名 | 类型 |
| --- | --- |
| `paragraphs` | `list[ThreadContentParagraph]` |

结构：`ThreadContentParagraph`

| 字段名 | 类型 |
| --- | --- |
| `elems` | `list[ThreadContentElem]` |
| `props` | `ParagraphProps \| None` |

结构：`ParagraphProps`

| 字段名 | 类型 |
| --- | --- |
| `alignment` | `int` |

`alignment` 可参考 `Model.Alignment`：

| 常量 | 值 |
| --- | --- |
| `ALIGNMENT_LEFT` | `0` |
| `ALIGNMENT_MIDDLE` | `1` |
| `ALIGNMENT_RIGHT` | `2` |

结构：`ThreadContentElem`

| 字段名 | 类型 |
| --- | --- |
| `type` | `int` |
| `text` | `ThreadContentText \| None` |
| `image` | `ThreadContentImage \| None` |
| `video` | `ThreadContentVideo \| None` |
| `url` | `ThreadContentUrl \| None` |

元素类型常量：

| 常量 | 值 |
| --- | --- |
| `TYPE_TEXT` | `1` |
| `TYPE_IMAGE` | `2` |
| `TYPE_VIDEO` | `3` |
| `TYPE_URL` | `4` |

结构：`ThreadContentText`

| 字段名 | 类型 |
| --- | --- |
| `text` | `str` |
| `props` | `TextProps \| None` |

结构：`TextProps`

| 字段名 | 类型 |
| --- | --- |
| `font_bold` | `bool` |
| `italic` | `bool` |
| `underline` | `bool` |

结构：`ThreadContentUrl`

| 字段名 | 类型 |
| --- | --- |
| `url` | `str` |
| `desc` | `str` |

结构：`ThreadContentImage`

| 字段名 | 类型 |
| --- | --- |
| `third_url` | `str` |
| `width_percent` | `float` |

结构：`ThreadContentVideo`

| 字段名 | 类型 |
| --- | --- |
| `third_url` | `str` |
| `plat_video` | `ThreadContentPlatVideo \| None` |

结构：`ThreadContentPlatVideo`

| 字段名 | 类型 |
| --- | --- |
| `url` | `str` |
| `width` | `int` |
| `height` | `int` |
| `video_id` | `str` |
| `duration` | `int` |
| `cover` | `ThreadContentPlatImage \| None` |

结构：`ThreadContentPlatImage`

| 字段名 | 类型 |
| --- | --- |
| `url` | `str` |
| `width` | `int` |
| `height` | `int` |
| `image_id` | `str` |

***

## 八、音频与音视频事件

### 8.1 `AudioAction`

来源装饰器：

- `@bot.on_audio_start`
- `@bot.on_audio_finish`
- `@bot.on_audio_on_mic`
- `@bot.on_audio_off_mic`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `guild_id` | `str` | 频道 ID |
| `channel_id` | `str` | 子频道 ID |
| `audio_url` | `str` | 音频 URL |
| `text` | `str` | 音频说明 |

### 8.2 `LiveChannelMember`

来源装饰器：

- `@bot.on_audio_or_live_channel_member_enter`
- `@bot.on_audio_or_live_channel_member_exit`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `guild_id` | `str` | 频道 ID |
| `channel_id` | `str` | 子频道 ID |
| `channel_type` | `int` | 子频道类型 |
| `user_id` | `str` | 用户 ID |

***

## 九、聚合事件与生命周期

### 9.1 聚合事件

`@bot.on_all_intent_events`、`@bot.on_default_public_events`、`@bot.on_default_private_events` 会一次性订阅多个事件，因此 callback 参数应标注为 `Model.BaseModel`。

```python
@bot.on_default_public_events
async def handle(event: Model.BaseModel):
    print(event.event_type)
```

运行时，`event` 可能实际是：

- `Model.GuildMessage`
- `Model.Guild`
- `Model.Channel`
- `Model.GroupMessage`
- `Model.C2CMessage`
- `Model.GroupEvent`
- `Model.FriendEvent`
- `Model.OpenForumEvent`

### 9.2 生命周期

生命周期事件不继承 `BaseModel`，但 callback 类型固定：

| 装饰器 | callback 类型 |
| --- | --- |
| `@bot.on_startup` | `Model.StartupEvent` |
| `@bot.on_shutdown` | `Model.ShutdownEvent` |
| `@bot.on_timer(...)` | `Model.TimerEvent` |

***

## 十、装饰器与 callback 类型速查

| 装饰器 | callback 类型 |
| --- | --- |
| `@bot.on_guild_message` | `Model.GuildMessage` |
| `@bot.on_guild_full_message` | `Model.GuildMessage` |
| `@bot.on_at_group_message` | `Model.GroupMessage` |
| `@bot.on_group_message` | `Model.GroupMessage` |
| `@bot.on_c2c_message` | `Model.C2CMessage` |
| `@bot.on_direct_message` | `Model.DirectMessage` |
| `@bot.on_message_delete` | `Model.MessageDelete` |
| `@bot.on_public_message_delete` | `Model.MessageDelete` |
| `@bot.on_direct_message_delete` | `Model.MessageDelete` |
| `@bot.on_guild_create` | `Model.Guild` |
| `@bot.on_guild_update` | `Model.Guild` |
| `@bot.on_guild_delete` | `Model.Guild` |
| `@bot.on_channel_create` | `Model.Channel` |
| `@bot.on_channel_update` | `Model.Channel` |
| `@bot.on_channel_delete` | `Model.Channel` |
| `@bot.on_guild_member_add` | `Model.MemberWithGuildID` |
| `@bot.on_guild_member_update` | `Model.MemberWithGuildID` |
| `@bot.on_guild_member_remove` | `Model.MemberWithGuildID` |
| `@bot.on_group_add` | `Model.GroupEvent` |
| `@bot.on_group_delete` | `Model.GroupEvent` |
| `@bot.on_group_msg_reject` | `Model.GroupEvent` |
| `@bot.on_group_msg_receive` | `Model.GroupEvent` |
| `@bot.on_group_join_request` | `Model.GroupJoinRequestEvent` |
| `@bot.on_group_member_add` | `Model.GroupMemberEvent` |
| `@bot.on_group_member_remove` | `Model.GroupMemberEvent` |
| `@bot.on_subscribe_message_status` | `Model.SubscribeMessageStatusEvent` |
| `@bot.on_friend_add` | `Model.FriendEvent` |
| `@bot.on_friend_delete` | `Model.FriendEvent` |
| `@bot.on_c2c_msg_reject` | `Model.FriendEvent` |
| `@bot.on_c2c_msg_receive` | `Model.FriendEvent` |
| `@bot.on_message_audit_pass` | `Model.MessageAudited` |
| `@bot.on_message_audit_reject` | `Model.MessageAudited` |
| `@bot.on_reaction_add` | `Model.MessageReaction` |
| `@bot.on_reaction_remove` | `Model.MessageReaction` |
| `@bot.on_interaction` | `Model.Interaction` |
| `@bot.on_forum_thread_create` | `Model.Thread` |
| `@bot.on_forum_thread_update` | `Model.Thread` |
| `@bot.on_forum_thread_delete` | `Model.Thread` |
| `@bot.on_forum_post_create` | `Model.Post` |
| `@bot.on_forum_post_delete` | `Model.Post` |
| `@bot.on_forum_reply_create` | `Model.Reply` |
| `@bot.on_forum_reply_delete` | `Model.Reply` |
| `@bot.on_forum_publish_audit_result` | `Model.AuditResult` |
| `@bot.on_open_forum_thread_create` | `Model.OpenForumEvent` |
| `@bot.on_open_forum_thread_update` | `Model.OpenForumEvent` |
| `@bot.on_open_forum_thread_delete` | `Model.OpenForumEvent` |
| `@bot.on_open_forum_post_create` | `Model.OpenForumEvent` |
| `@bot.on_open_forum_post_delete` | `Model.OpenForumEvent` |
| `@bot.on_open_forum_reply_create` | `Model.OpenForumEvent` |
| `@bot.on_open_forum_reply_delete` | `Model.OpenForumEvent` |
| `@bot.on_audio_start` | `Model.AudioAction` |
| `@bot.on_audio_finish` | `Model.AudioAction` |
| `@bot.on_audio_on_mic` | `Model.AudioAction` |
| `@bot.on_audio_off_mic` | `Model.AudioAction` |
| `@bot.on_audio_or_live_channel_member_enter` | `Model.LiveChannelMember` |
| `@bot.on_audio_or_live_channel_member_exit` | `Model.LiveChannelMember` |
| `@bot.on_all_intent_events` | `Model.BaseModel` |
| `@bot.on_default_public_events` | `Model.BaseModel` |
| `@bot.on_default_private_events` | `Model.BaseModel` |
| `@bot.on_startup` | `Model.StartupEvent` |
| `@bot.on_shutdown` | `Model.ShutdownEvent` |
| `@bot.on_timer(...)` | `Model.TimerEvent` |

命令与预处理器可按 `valid_scenes` 速查：

| 装饰器 | `valid_scenes` | callback 类型 |
| --- | --- | --- |
| `@bot.before_command(...)` / `@bot.on_command(...)` | `CommandValidScenes.GUILD` | `Model.GuildMessage` |
| `@bot.before_command(...)` / `@bot.on_command(...)` | `CommandValidScenes.GROUP` | `Model.GroupMessage` |
| `@bot.before_command(...)` / `@bot.on_command(...)` | `CommandValidScenes.C2C` | `Model.C2CMessage` |
| `@bot.before_command(...)` / `@bot.on_command(...)` | `CommandValidScenes.DM` | `Model.DirectMessage` |
| `@bot.before_command(...)` / `@bot.on_command(...)` | 多场景组合 | 上述类型的联合类型 |
| `@Plugins.before_command(...)` / `@Plugins.on_command(...)` | 同上 | 与 `Bot` 版本一致 |

***

## 十一、其他已导出的公共类型

这一节补充一些不会直接作为事件 callback 主模型出现，但仍然属于当前 `Model` 公共导出的一部分。

### 11.1 `MessageBase`

`MessageBase` 已在"3.2 `MessageBase`"中展开。它是四种消息事件模型的共同父类，适合在说明消息共性字段时使用。

### 11.2 `Model.Message`

`Model.Message` 是四种消息模型的联合类型别名：

```python
# 等价于以下写法：
Model.Message = Model.GuildMessage | Model.GroupMessage | Model.C2CMessage | Model.DirectMessage
```

适用场景：
- **多场景命令回调**：`on_command(valid_scenes=CommandValidScenes.ALL)` 的参数类型
- **预处理器**：`before_command()` 的参数类型
- **session.wait_for()** 返回值标注
- **任何需要同时处理多种消息类型的地方**

推荐优先使用 `Model.Message` 而非手动写出四种类型的联合，代码更简洁且语义清晰。

### 11.3 `Alignment`

`Alignment` 是论坛正文构建与解析中使用的对齐枚举，常用于 `ParagraphProps.alignment`。

| 常量 | 值 |
| --- | --- |
| `ALIGNMENT_LEFT` | `0` |
| `ALIGNMENT_MIDDLE` | `1` |
| `ALIGNMENT_RIGHT` | `2` |

### 11.4 `SessionStatus`

`SessionStatus` 是会话管理器使用的状态常量类，主要用于 `SessionObject.status` 以及 `SessionManager` 的状态流转。

| 常量 | 值 | 说明 |
| --- | --- | --- |
| `ACTIVE` | `0` | 活跃状态，会按规则检查并在满足条件时自动清理 |
| `INACTIVE` | `1` | 非活跃状态，超时后进入此状态，GC 在指定时间后清理 |

### 11.5 `StreamMessageResponse`

`StreamMessageResponse` 是发送流式消息时的返回模型，适用于 `send_c2c_stream_message()`。

| 字段名 | 类型 |
| --- | --- |
| `code` | `int \| None` |
| `message` | `str \| None` |
| `id` | `str \| None` |
| `timestamp` | `str \| None` |
| `ext_info` | `dict \| None` |

### 11.6 `StreamInputMode`

`StreamInputMode` 是流式消息输入模式常量类。

| 常量 | 值 |
| --- | --- |
| `REPLACE` | `"replace"` |

### 11.7 `StreamInputState`

`StreamInputState` 是流式消息输入状态常量类。

| 常量 | 值 |
| --- | --- |
| `GENERATING` | `1` |
| `DONE` | `10` |

### 11.8 `StreamContentType`

`StreamContentType` 是流式消息内容类型常量类。

| 常量 | 值 |
| --- | --- |
| `MARKDOWN` | `"markdown"` |

***

### 11.9 大文件分片上传相关模型

#### `UploadPart`

分片信息对象，用于大文件分片上传。

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `index` | `int` | 分片索引（从 1 开始） |
| `presigned_url` | `str` | 预签名上传链接 |

#### `UploadPrepareResponse`

大文件分片上传申请响应。

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `upload_id` | `str` | 上传任务 ID |
| `block_size` | `int` | 分块大小（字节） |
| `parts` | `list[UploadPart]` | 分片列表 |
| `concurrency` | `int \| None` | 建议的并发数 |
| `retry_timeout` | `int \| None` | 重试超时时间（秒） |

#### `FileInfo`

文件信息对象，用于文件上传结果。

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `file_uuid` | `str` | 文件唯一标识 |
| `file_info` | `str` | 用于发送消息的文件信息 |
| `ttl` | `int` | 文件有效期（秒） |
| `id` | `str \| None` | 文件 ID |

***

### 11.10 群管理相关模型

> 相关接口多为内邀 / 申请制能力，无权限时返回错误码 `11253`。

#### `GroupInfo`

群基本信息（`GET /v2/groups/{group_openid}/info`）。

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `group_openid` | `str` | 群 OpenID |
| `group_name` | `str` | 群名称 |
| `group_finger_memo` | `str` | 群简介 |
| `group_class_text` | `str` | 群分类 |
| `group_tags` | `list[str]` | 群标签列表 |
| `group_member_num` | `int` | 群成员人数 |

#### `GroupBotState`

机器人在群内的状态（`GET /v2/groups/{group_openid}/bot_state`）。

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `member_openid` | `str` | 机器人的 openid |
| `joined_at` | `str` | 入群时间戳（RFC3339） |
| `allow_proactive_msg` | `bool` | 是否接收主动推送 |
| `recv_msg_setting` | `str` | 接受消息类型：`all` / `only_mention` / `mention_and_context` |
| `member_role` | `str` | 群成员角色 |

便捷属性：`is_owner`、`is_admin`、`only_mention`。

#### `BlacklistUser` / `GroupBlacklistResponse` / `GroupBlacklistOpResult`

群黑名单相关模型（`/v2/groups/{group_openid}/member_blacklist`）。

| 模型 | 字段 | 说明 |
| --- | --- | --- |
| `BlacklistUser` | `union_openid` / `member_openid` / `username` / `banned_at` / `bot` | 单个黑名单用户 |
| `GroupBlacklistResponse` | `users: list[BlacklistUser]` / `next_cursor` | 黑名单查询响应，含 `is_end` 属性 |
| `GroupBlacklistOpResult` | `fail_openids: list[str]` | 黑名单操作失败列表 |

#### `BatchRemoveMembersResult`

群成员批量移除结果（`POST /v2/groups/{group_openid}/batch_remove_members`）。

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `remove_members_result` | `str` | 成功时返回 `success` |
| `add_to_member_blacklist_fail_openids` | `list[str]` | 拉黑失败的 openid |

便捷属性：`is_success`。

#### `GroupRestrictChatSetting` 及禁言规则

群禁言状态（`GET /v2/groups/{group_openid}/restrict_chat_setting`）。

| 模型 | 字段 | 说明 |
| --- | --- | --- |
| `GroupRestrictChatSetting` | `global_rule: GlobalMuteRule \| None` / `members: list[MemberMuteState]` | 群级规则 + 禁言中的成员 |
| `GlobalMuteRule` | `mode` / `schedule_rules` / `recurring_rules` | `mode` 为 `none` / `always` / `schedule`；含 `is_enabled` 属性 |
| `MuteScheduleRule` | `task_id` / `start_at` / `end_at` / `enabled` | 定时禁言规则 |
| `MuteRecurringRule` | `task_id` / `weekdays` / `start_time` / `end_time` / `enabled` | 周期禁言规则（`weekdays` 取 1~7） |
| `MemberMuteState` | `member_openid` / `mute_expire_at` / `username` / `union_openid` | 成员禁言状态 |

相关常量：`Model.GroupRestrictChatMode`（`NONE` / `ALWAYS` / `SCHEDULE`）、`Model.GroupMuteOp`（`ADD` / `UPDATE` / `DEL`）。

#### `JoinRequest` / `JoinRequestListResponse`

入群申请（`GET /v2/groups/{group_openid}/join_request_list`）。

| 模型 | 字段 | 说明 |
| --- | --- | --- |
| `JoinRequest` | `join_request_id` / `risk_tips` / `top_tips` / `union_openid` / `member_openid` / `username` / `apply_at` / `apply_source` / `invited_by` / `bot` / `verify_info` | 单条入群申请，含 `is_invited` 属性 |
| `JoinRequestListResponse` | `requests: list[JoinRequest]` / `next_cursor` | 列表响应，含 `is_end` 属性 |

> 接口响应字段名为 `list`，为避免与内置类型冲突，SDK 映射为 `requests`。

相关常量：`Model.JoinRequestApprovalOp`（`APPROVE` / `DECLINE`）、`Model.JoinRequestApplySource`（`SELF_APPLY` / `INVITED`）。

#### `JoinApprovalStrategy` 及其响应模型

入群自动审批策略（`/v2/groups/join_approval_strategy` 系列）。

| 模型 | 字段 | 说明 |
| --- | --- | --- |
| `JoinApprovalStrategy` | `strategy_id` / `group_openids` / `group_ids` / `whitelist_user_count` / `is_enable` / `expire_at` / `created_at` / `updated_at` / `remark` | 策略详情，含 `enabled` 属性 |
| `JoinApprovalStrategyListResponse` | `strategies` / `next_cursor` | 列表响应，含 `is_end` 属性 |
| `JoinApprovalStrategyCreated` | `strategy_id` / `is_enable` / `expire_at` | 创建响应 |
| `JoinApprovalStrategyUpdated` | `is_enable` / `expire_at` | 修改响应 |
| `WhitelistUsersResponse` | `strategy_id` / `whitelist_user_count` / `updated_at` | 白名单操作响应 |

相关常量：`Model.JoinApprovalStrategyEnable`（`ON` / `OFF`）、`Model.JoinApprovalStrategyOp`（`ADD` / `DEL`）。

***

### 11.11 自定义菜单与指令面板模型

#### `Menu` / `MenuItem` / `SubMenuItem` / `MenuSwitch`

自定义菜单（`GET` / `PUT /v2/menu`）。

| 模型 | 字段 | 说明 |
| --- | --- | --- |
| `Menu` | `items: list[MenuItem]` | 菜单项列表，最多 10 个；提供 `to_dict()` 生成请求体 |
| `MenuItem` | `name` / `type` / `sub_menu_items` / `send_message` / `link` / `switch` | `type` 可选 `switch` / `send_message` / `link` / `menu` |
| `SubMenuItem` | `name` / `type` / `send_message` / `link` | 二级菜单，最多 5 个且不支持再嵌套 |
| `MenuSwitch` | `switch_id` / `default` | 开关配置 |

响应模型：`MenuResponse`（`version` / `menu`）、`MenuVersionResponse`（`version`）。
常量：`Model.MenuItemType`。

#### `Panel` / `PanelItem` / `PanelRecord`

指令面板（`/v2/panels` 系列）。

| 模型 | 字段 | 说明 |
| --- | --- | --- |
| `Panel` | `items: list[PanelItem]` / `remark` / `version` | 面板配置，最多 20 个元素；提供 `to_dict()` |
| `PanelItem` | `name` / `desc` / `type` / `only_admin` / `link` | `type` 可选 `command` / `link` |
| `PanelRecord` | `panel_id` / `scope` / `target_type` / `panel` / `created_at` / `updated_at` / `version` / `user_openids` / `group_openids` | 面板记录，含 `is_global` 属性 |

响应模型：`PanelsResponse`（`records` / `next_cursor` / `is_end`）、`PanelCreateResponse`（`panel_id`）、`PanelVersionResponse`（`version`）。

常量：`Model.PanelScope`（`C2C` / `GROUP` / `CHANNEL` / `DM`）、`Model.PanelTargetType`（`ALL` / `SPECIFIC`）、`Model.PanelItemType`（`COMMAND` / `LINK`）、`Model.PanelTargetOp`（`ADD` / `DEL`）。

***

## 十二、使用建议

### 12.1 优先按 callback 来源找模型

如果你是在写事件回调，最好的查阅方式不是先从 `Model` 总表找类名，而是先确认：

- 当前写的是哪个装饰器
- 这个装饰器会把什么模型传进来
- 这个模型是否属于消息模型分支

### 12.2 单事件优先标注具体类型

```python
@bot.on_group_message
async def handle(msg: Model.GroupMessage):
    print(msg.group_openid)
```

不推荐在单事件装饰器里直接写 `Model.BaseModel`。

### 12.3 聚合事件才适合 `BaseModel`

```python
@bot.on_all_intent_events
async def handle(event: Model.BaseModel):
    print(event.event_type)
```

### 12.4 发送消息内容使用 `MessagesModel`

```python
from easybot import MessagesModel

@bot.on_command(command="hi")
async def hi(msg: Model.GuildMessage):
    await msg.reply(MessagesModel.MessageMarkdown(content="# 你好"))
```

***

## 十三、下一步

- [Messages Model](./05_Messages_Model.md) — 查看消息构建器
- [API 参考](./04_API参考.md) — 查看 API 返回值与调用方式
- [插件与权限](./07_插件与权限.md) — 查看插件系统与命令注册
