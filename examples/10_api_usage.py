#!/usr/bin/env python3
"""
EasyBot SDK 示例 10：API 使用方法

展示 EasyBot 提供的完整 QQ 官方 API 封装：
- 发送消息（频道、群聊、单聊、私信）
- 频道管理（获取信息、子频道、成员）
- 消息管理（获取、撤回）
- 身份组管理
- 禁言管理
- 互动事件处理
- 富媒体上传
- 群管理（群信息、成员、黑名单、禁言、入群申请与审批）
- 自定义菜单与指令面板
- 群成员变动与订阅消息事件

注意：
- 频道消息支持 image/file_image 参数直接发送图片
- 群聊/单聊需要使用 upload_media API 上传后发送

运行前请将 app_id 和 app_secret 替换为你的机器人凭证
"""

from easybot import Bot, MessagesModel, Model


def main() -> None:
    bot: Bot = Bot(
        app_id="your_app_id",
        app_secret="your_app_secret",
    )

    # ==================== 10.1 频道消息 API ====================
    @bot.on_guild_message
    async def handle_guild(msg: Model.GuildMessage) -> None:
        """频道消息处理及 API 调用示例"""

        if msg.treated_msg == "发送消息":
            # 发送频道消息
            result = await msg.reply("Hello from API!")
            bot.logger.info(f"消息发送成功，ID: {result.id}")

        # ----- 发送带图片的消息（仅频道支持 image/file_image） -----
        elif msg.treated_msg == "发送图片":
            result = await msg.reply(
                "看这张图",
                file_image="./images/photo.png",
            )
            bot.logger.info(f"图片消息发送成功，ID: {result.id}")

        elif msg.treated_msg == "发送markdown":
            # 发送 Markdown 消息
            await msg.reply(
                MessagesModel.MessageMarkdown(content="# API 发送的 Markdown")
            )

        elif msg.treated_msg == "获取消息":
            # 获取指定消息
            try:
                message = await bot.api.get_guild_message(
                    channel_id=msg.channel_id, message_id=msg.id
                )
                await msg.reply(f"消息内容：{message.content}")
            except Exception as e:
                bot.logger.error(f"获取消息失败: {e}")

        elif msg.treated_msg == "撤回消息":
            # 撤回消息
            try:
                await bot.api.recall_guild_message(
                    channel_id=msg.channel_id,
                    message_id=msg.id,
                    hidetip=False,  # 是否隐藏提示小灰条
                )
                bot.logger.info("消息已撤回")
            except Exception as e:
                bot.logger.error(f"撤回消息失败: {e}")

    # ==================== 10.2 群聊相关 API ====================
    @bot.on_group_message
    async def handle_group(msg: Model.GroupMessage) -> None:
        """群聊 API 调用示例"""

        if msg.treated_msg == "发送群消息":
            # 发送群聊消息
            await msg.reply("Hello Group!")

        # ----- 群聊发送图片（必须使用 upload_media） -----
        elif msg.treated_msg == "发送图片":
            try:
                # 步骤1：上传图片
                upload_result = await bot.api.upload_media(
                    file_type=1,  # 1=图片
                    file_data="./images/group_image.png",
                    group_openid=msg.group_openid,
                )

                # 步骤2：发送引用图片的消息
                await msg.reply(
                    "群聊图片",
                    media_file_info=upload_result.file_info,
                )
            except Exception as e:
                bot.logger.error(f"发送图片失败: {e}")
                await msg.reply("❌ 图片发送失败")

        elif msg.treated_msg == "发送embed":
            # 发送 Embed 消息
            await msg.reply(
                MessagesModel.MessageEmbed(
                    title="群公告", content=["公告内容1", "公告内容2"]
                )
            )

        # ----- 获取群成员列表（需申请内邀权限，无权限返回 11253） -----
        elif msg.treated_msg == "群成员列表":
            try:
                # 方式一：单页获取（每次最多 30 条）
                resp = await bot.api.get_group_members(msg.group_openid)
                for member in resp.members:
                    bot.logger.info(
                        f"{member.member_openid} / {member.username} / "
                        f"{member.member_role} / 机器人={member.bot}"
                    )

                # 方式二：自动翻页获取全量成员
                members = await bot.api.get_all_group_members(msg.group_openid)
                admins = [m for m in members if m.is_admin]

                await msg.reply(
                    f"👥 群成员共 {len(members)} 人\n"
                    f"管理员以上：{', '.join(m.username for m in admins) or '无'}"
                )
            except Exception as e:
                bot.logger.error(f"获取群成员列表失败: {e}")
                await msg.reply("❌ 获取群成员失败（可能未开通接口权限）")

    # ==================== 10.3 单聊相关 API ====================
    @bot.on_c2c_message
    async def handle_c2c(msg: Model.C2CMessage) -> None:
        """单聊 API 调用示例"""

        if msg.treated_msg == "发送私信":
            # 发送单聊消息
            await msg.reply("Hello!")

        # ----- 单聊发送图片（必须使用 upload_media） -----
        elif msg.treated_msg == "发送图片":
            try:
                # 步骤1：上传图片
                upload_result = await bot.api.upload_media(
                    file_type=1,  # 1=图片
                    file_data="./images/c2c_image.png",
                    user_openid=msg.author.user_openid,
                )

                # 步骤2：发送引用图片的消息
                await msg.reply(
                    "私信图片",
                    media_file_info=upload_result.file_info,
                )
            except Exception as e:
                bot.logger.error(f"发送图片失败: {e}")
                await msg.reply("❌ 图片发送失败")

    # ==================== 10.4 频道管理 API ====================
    @bot.on_guild_message
    async def handle_guild_management(msg: Model.GuildMessage) -> None:
        """频道管理 API 示例"""

        if msg.treated_msg == "频道信息":
            # 获取频道信息
            try:
                guild = await bot.api.get_guild(msg.guild_id)
                await msg.reply(
                    f"📋 频道信息：\n"
                    f"- 名称：{guild.name}\n"
                    f"- 拥有者：{guild.owner_id}\n"
                    f"- 成员数：{guild.member_count}"
                )
            except Exception as e:
                bot.logger.error(f"获取频道信息失败: {e}")

        elif msg.treated_msg == "子频道列表":
            # 获取子频道列表
            try:
                channels = await bot.api.get_guild_channels(msg.guild_id)
                channel_list = "\n".join(
                    [
                        f"- {ch.name} (ID: {ch.id}, 类型: {ch.type})"
                        for ch in channels[:10]  # 只显示前10个
                    ]
                )
                await msg.reply(f"📋 子频道列表：\n{channel_list}")
            except Exception as e:
                bot.logger.error(f"获取子频道列表失败: {e}")

        elif msg.treated_msg == "成员列表":
            # 获取成员列表
            try:
                members = await bot.api.get_guild_members(msg.guild_id, limit=20)
                member_list = "\n".join([f"- {m.user.username}" for m in members])
                await msg.reply(f"📋 成员列表（前20）：\n{member_list}")
            except Exception as e:
                bot.logger.error(f"获取成员列表失败: {e}")

    # ==================== 10.5 身份组管理 API ====================
    @bot.on_guild_message
    async def handle_role_management(msg: Model.GuildMessage) -> None:
        """身份组管理 API 示例"""

        if msg.treated_msg == "身份组列表":
            # 获取身份组列表
            try:
                roles_response = await bot.api.get_guild_roles(msg.guild_id)
                roles = roles_response.roles
                role_list = "\n".join(
                    [
                        f"- {role.name} (ID: {role.id}, 颜色: {role.color})"
                        for role in roles
                    ]
                )
                await msg.reply(f"📋 身份组列表：\n{role_list}")
            except Exception as e:
                bot.logger.error(f"获取身份组列表失败: {e}")

    # ==================== 10.6 禁言管理 API ====================
    @bot.on_guild_message
    async def handle_moderation(msg: Model.GuildMessage) -> None:
        """禁言管理 API 示例"""

        if msg.treated_msg == "全员禁言":
            # 全员禁言
            try:
                await bot.api.mute_guild(
                    guild_id=msg.guild_id, mute_seconds=3600  # 禁言1小时
                )
                await msg.reply("✅ 已开启全员禁言（1小时）")
            except Exception as e:
                bot.logger.error(f"全员禁言失败: {e}")

        elif msg.treated_msg == "解除禁言":
            # 取消全员禁言
            try:
                await bot.api.cancel_mute_all(msg.guild_id)
                await msg.reply("✅ 已解除全员禁言")
            except Exception as e:
                bot.logger.error(f"解除禁言失败: {e}")

    # ==================== 10.7 互动事件处理 ====================
    @bot.on_interaction
    async def handle_interaction(msg: Model.Interaction) -> None:
        """互动按钮点击事件处理"""
        bot.logger.info(f"收到互动事件: {msg.data}")

        try:
            # 回应互动事件（必须回应，否则QQ会提示操作失败）
            await bot.api.respond_interaction(
                interaction_id=msg.id,
                code=0,  # 0=成功, 1=失败, 2=频繁, 3=重复, 4=无权限, 5=仅管理员
            )
            bot.logger.info("互动事件已回应")
        except Exception as e:
            bot.logger.error(f"回应互动事件失败: {e}")

    # ==================== 10.8 其他 API ====================
    @bot.on_guild_message
    async def handle_other_apis(msg: Model.GuildMessage) -> None:
        """其他 API 示例"""

        if msg.treated_msg == "机器人信息":
            # 获取机器人信息
            try:
                me = await bot.api.get_me()
                await msg.reply(
                    f"🤖 机器人信息：\n"
                    f"- ID：{me.id}\n"
                    f"- 名称：{me.username}\n"
                    f"- 头像：{me.avatar}"
                )
            except Exception as e:
                bot.logger.error(f"获取机器人信息失败: {e}")

        elif msg.treated_msg == "在线人数":
            # 获取子频道在线人数
            try:
                online = await bot.api.get_channel_online_nums(msg.channel_id)
                await msg.reply(f"👥 当前在线人数：{online.online_nums}")
            except Exception as e:
                bot.logger.error(f"获取在线人数失败: {e}")

    # ==================== 10.9 群管理 API（需申请接口权限） ====================
    @bot.on_group_message
    async def handle_group_management(msg: Model.GroupMessage) -> None:
        """群管理 API 示例

        注意：群管理相关接口多为内邀 / 申请制能力，无权限时返回错误码 11253。
        """

        if msg.treated_msg == "群信息":
            try:
                info = await bot.api.get_group_info(msg.group_openid)
                state = await bot.api.get_group_bot_state(msg.group_openid)
                await msg.reply(
                    f"📋 {info.group_name}\n"
                    f"- 成员数：{info.group_member_num}\n"
                    f"- 标签：{'、'.join(info.group_tags) or '无'}\n"
                    f"- 机器人角色：{state.member_role}\n"
                    f"- 接收消息：{state.recv_msg_setting}"
                )
            except Exception as e:
                bot.logger.error(f"获取群信息失败: {e}")

        elif msg.treated_msg == "迁移前统计":
            # 批量拉取全部成员（自动翻页）
            try:
                members = await bot.api.get_all_group_members(msg.group_openid)
                owners = [m for m in members if m.is_admin]
                await msg.reply(
                    f"👥 共 {len(members)} 人\n"
                    f"管理员以上：{'、'.join(m.username for m in owners) or '无'}"
                )
            except Exception as e:
                bot.logger.error(f"获取群成员失败: {e}")

        elif msg.treated_msg == "入群申请":
            try:
                result = await bot.api.get_group_join_requests(
                    msg.group_openid, limit=20
                )
                for req in result.requests:
                    bot.logger.info(
                        f"申请ID={req.join_request_id} {req.username} "
                        f"来源={req.apply_source} 邀请人={req.invited_by}"
                    )
                await msg.reply(f"📨 待处理申请 {len(result.requests)} 条")
            except Exception as e:
                bot.logger.error(f"拉取入群申请失败: {e}")

        elif msg.treated_msg == "禁言状态":
            try:
                setting = await bot.api.get_group_restrict_chat_setting(
                    msg.group_openid
                )
                mode = setting.global_rule.mode if setting.global_rule else "unknown"
                await msg.reply(
                    f"🔇 全员禁言模式：{mode}\n"
                    f"禁言中成员：{len(setting.members)} 人"
                )
            except Exception as e:
                bot.logger.error(f"查询禁言状态失败: {e}")

    # ==================== 10.10 自定义菜单与指令面板 API ====================
    @bot.on_c2c_message
    async def handle_menu_panel(msg: Model.C2CMessage) -> None:
        """自定义菜单与指令面板示例"""

        if msg.treated_msg == "设置菜单":
            try:
                # 覆盖式设置全局自定义菜单（最多 10 个菜单项）
                result = await bot.api.set_menu(
                    {
                        "items": [
                            {
                                "type": "send_message",
                                "name": "帮助",
                                "send_message": "/help",
                            },
                            {
                                "type": "link",
                                "name": "官网",
                                "link": "https://example.com",
                            },
                            {
                                "type": "menu",
                                "name": "更多",
                                "sub_menu_items": [
                                    {
                                        "type": "send_message",
                                        "name": "设置",
                                        "send_message": "/settings",
                                    }
                                ],
                            },
                            {
                                "type": "switch",
                                "name": "联网",
                                "switch": {"switch_id": "search", "default": False},
                            },
                        ]
                    }
                )
                bot.logger.info(f"菜单已更新，版本号：{result.version}")

                # 也可以先用 Model.Panel / Model.Menu 构建对象再传入
                current = await bot.api.get_menu()
                await msg.reply(f"✅ 菜单已更新（版本 {current.version}）")
            except Exception as e:
                bot.logger.error(f"设置菜单失败: {e}")

        elif msg.treated_msg == "创建面板":
            try:
                created = await bot.api.create_panel(
                    scope=Model.PanelScope.C2C,
                    target_type=Model.PanelTargetType.ALL,
                    panel={
                        "items": [
                            {
                                "type": Model.PanelItemType.COMMAND,
                                "name": "查询天气",
                                "desc": "查询当前天气",
                            },
                            {
                                "type": Model.PanelItemType.LINK,
                                "name": "更多服务",
                                "link": "https://example.com",
                            },
                        ],
                        "remark": "C2C 面板",
                    },
                )
                await msg.reply(f"✅ 面板已创建：{created.panel_id}")
            except Exception as e:
                bot.logger.error(f"创建面板失败: {e}")

        elif msg.treated_msg == "面板列表":
            try:
                panels = await bot.api.get_panels(Model.PanelScope.C2C, limit=20)
                lines = [
                    f"- {p.panel_id}（{'全局' if p.is_global else '指定对象'}）"
                    for p in panels.records
                ]
                await msg.reply("📋 面板列表：\n" + ("\n".join(lines) or "暂无"))
            except Exception as e:
                bot.logger.error(f"查询面板失败: {e}")

    # ==================== 10.11 群成员变动事件 ====================
    @bot.on_group_join_request
    async def handle_join_request(event: Model.GroupJoinRequestEvent) -> None:
        """用户申请加群事件（需机器人是群管理员）"""
        bot.logger.info(
            f"{event.username} 申请入群，来源={event.apply_source}，"
            f"验证方式={event.verify_info.method if event.verify_info else '无'}"
        )
        try:
            await bot.api.approve_join_request(
                event.group_openid, event.member_openid, event.join_request_id
            )
        except Exception as e:
            bot.logger.error(f"审批入群申请失败: {e}")

    @bot.on_group_member_add
    async def handle_member_add(event: Model.GroupMemberEvent) -> None:
        """群成员加入事件"""
        bot.logger.info(f"新成员加入：{event.member_openid}（群 {event.group_openid}）")

    @bot.on_group_member_remove
    async def handle_member_remove(event: Model.GroupMemberEvent) -> None:
        """群成员退出事件"""
        bot.logger.info(f"成员退出：{event.member_openid}（群 {event.group_openid}）")

    @bot.on_subscribe_message_status
    async def handle_subscribe(event: Model.SubscribeMessageStatusEvent) -> None:
        """订阅消息授权状态变更事件"""
        for item in event.result:
            bot.logger.info(
                f"模板 {item.template_id} {'允许' if item.is_allowed else '拒绝'}订阅"
            )

    bot.start()


if __name__ == "__main__":
    main()
