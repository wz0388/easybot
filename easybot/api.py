#!/usr/bin/env python3
"""
EasyBot SDK API 模块

提供所有官方 API 的封装，包括：
- 频道相关 API
- 子频道相关 API
- 消息相关 API
- 群聊相关 API
- 私信相关 API
- 成员管理 API
- 身份组管理 API
- 权限管理 API
- 其他 API
"""

import asyncio
import base64
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

import aiohttp

from ._internal import HTTPClient
from .builders import MessagesModel
from .exceptions import APIError
from .models import Model

if TYPE_CHECKING:
    from .bot import Bot


class API:
    """
    API 调用封装类

    所有 API 方法都支持自动重试和错误日志。
    返回值均为对应的响应模型对象，方便开发者使用。
    """

    def __init__(self, bot: "Bot"):
        """
        初始化 API

        Args:
            bot: Bot 实例
        """
        self._bot: "Bot" = bot
        self._http: HTTPClient | None = None
        self._logger = bot.logger.with_module("api")

    async def _get_http(self) -> HTTPClient:
        """获取 HTTP 客户端"""
        if self._http is None:
            self._http = HTTPClient(self._bot)
            self._logger.debug("HTTP 客户端已创建")
        return self._http

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._http:
            await self._http.close()
            self._logger.debug("HTTP 客户端已关闭")

    async def get_guild(self, guild_id: str) -> Model.Guild:
        """
        获取频道详情

        Args:
            guild_id: 频道 ID

        Returns:
            Model.Guild: 频道对象
        """
        http = await self._get_http()
        data = await http.get(f"/guilds/{guild_id}")
        return Model.Guild.from_dict(data)

    async def get_guild_list(
        self,
        before: str | None = None,
        after: str | None = None,
        limit: int = 100,
    ) -> list[Model.Guild]:
        """
        获取机器人所在频道列表

        Args:
            before: 读此 guild id 之前的数据
            after: 读此 guild id 之后的数据
            limit: 每次拉取数量，默认 100，最大 100

        Returns:
            list[Model.Guild]: 频道对象列表
        """
        http = await self._get_http()
        params = {"limit": limit}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        data = await http.get("/users/@me/guilds", params=params)
        return [Model.Guild.from_dict(g) for g in data]

    async def get_guild_channels(self, guild_id: str) -> list[Model.Channel]:
        """
        获取频道子频道列表

        Args:
            guild_id: 频道 ID

        Returns:
            list[Model.Channel]: 子频道对象列表
        """
        http = await self._get_http()
        data = await http.get(f"/guilds/{guild_id}/channels")
        return [Model.Channel.from_dict(c) for c in data]

    async def get_me(self) -> Model.Author:
        """
        获取当前用户（机器人）信息

        Returns:
            Model.Author: 用户对象
        """
        http = await self._get_http()
        data = await http.get("/users/@me")
        return Model.Author.from_dict(data)

    async def get_channel(self, channel_id: str) -> Model.Channel:
        """
        获取子频道详情

        Args:
            channel_id: 子频道 ID

        Returns:
            Model.Channel: 子频道对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}")
        return Model.Channel.from_dict(data)

    async def create_channel(
        self,
        guild_id: str,
        name: str,
        channel_type: int,
        position: int,
        parent_id: str | None = None,
        sub_type: int = 0,
        private_type: int = 0,
        private_user_ids: list[str] | None = None,
        speak_permission: int = 0,
        application_id: str | None = None,
    ) -> Model.Channel:
        """
        创建子频道

        Args:
            guild_id: 频道 ID
            name: 子频道名称
            channel_type: 子频道类型
            position: 排序值
            parent_id: 所属分组 ID
            sub_type: 子频道子类型
            private_type: 子频道私密类型
            private_user_ids: 子频道私密成员 ID 列表
            speak_permission: 子频道发言权限
            application_id: 应用类型子频道 AppID

        Returns:
            Model.Channel: 创建的子频道对象
        """
        http = await self._get_http()
        payload = {
            "name": name,
            "type": channel_type,
            "position": position,
            "sub_type": sub_type,
            "private_type": private_type,
            "speak_permission": speak_permission,
        }
        if parent_id:
            payload["parent_id"] = parent_id
        if private_user_ids:
            payload["private_user_ids"] = private_user_ids
        if application_id:
            payload["application_id"] = application_id
        data = await http.post(f"/guilds/{guild_id}/channels", json=payload)
        return Model.Channel.from_dict(data)

    async def update_channel(
        self,
        channel_id: str,
        name: str | None = None,
        position: int | None = None,
        parent_id: str | None = None,
        private_type: int | None = None,
        speak_permission: int | None = None,
    ) -> Model.Channel:
        """
        修改子频道

        Args:
            channel_id: 子频道 ID
            name: 子频道名称
            position: 排序值
            parent_id: 所属分组 ID
            private_type: 子频道私密类型
            speak_permission: 子频道发言权限

        Returns:
            Model.Channel: 修改后的子频道对象
        """
        http = await self._get_http()
        payload = {}
        if name is not None:
            payload["name"] = name
        if position is not None:
            payload["position"] = position
        if parent_id is not None:
            payload["parent_id"] = parent_id
        if private_type is not None:
            payload["private_type"] = private_type
        if speak_permission is not None:
            payload["speak_permission"] = speak_permission
        data = await http.patch(f"/channels/{channel_id}", json=payload)
        return Model.Channel.from_dict(data)

    async def delete_channel(self, channel_id: str) -> bool:
        """
        删除子频道

        Args:
            channel_id: 子频道 ID

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/channels/{channel_id}")
        return True

    async def _send_message(
        self,
        endpoint: str,
        content: (
            str
            | MessagesModel.Message
            | MessagesModel.MessageEmbed
            | MessagesModel.MessageArk23
            | MessagesModel.MessageArk24
            | MessagesModel.MessageArk37
            | MessagesModel.MessageMarkdown
            | None
        ) = None,
        image: str | None = None,
        file_image: bytes | BinaryIO | str | None = None,
        media_file_info: str | None = None,
        msg_id: str | None = None,
        event_id: str | None = None,
        msg_type: int | None = None,
        msg_seq: int | None = None,
        is_wakeup: bool = False,
        message_reference_id: str | None = None,
        ignore_message_reference_error: bool = False,
        force_verify_image_resource: bool = False,
        response_model: type = Model.GuildMessage,
        **kwargs,
    ) -> Any:
        """
        通用消息发送方法

        Args:
            endpoint: API 端点
            content: 消息内容，可以是文本或消息对象
            image: 图片 URL（普通消息）
            file_image: 图片数据，支持 bytes、BinaryIO 或文件路径（普通消息）
            media_file_info: 富媒体文件信息（群聊/单聊 v2）
            msg_id: 要回复的消息 ID（被动消息）
            event_id: 要回复的事件 ID（被动消息）
            msg_type: 消息类型（群聊/单聊 v2 需要）
            msg_seq: 回复消息的序号（群聊/单聊需要）
            is_wakeup: 是否发送互动召回消息（仅 QQ 单聊 v2）
            message_reference_id: 引用消息 ID
            ignore_message_reference_error: 是否忽略引用消息错误
            force_verify_image_resource: 是否强制校验图片资源（仅群聊/单聊 v2）。
                开启后当图片资源转存失败时会中断消息发送并返回失败，默认关闭
            response_model: 响应模型类
            **kwargs: 其他参数

        Returns:
            响应模型实例
        """
        http = await self._get_http()
        structured_message_types = (
            MessagesModel.MessageEmbed,
            MessagesModel.MessageArk23,
            MessagesModel.MessageArk24,
            MessagesModel.MessageArk37,
            MessagesModel.MessageMarkdown,
        )
        is_group_or_c2c_v2 = endpoint.startswith("/v2/groups/") or endpoint.startswith(
            "/v2/users/"
        )
        is_c2c_v2 = endpoint.startswith("/v2/users/")
        if content is not None and not isinstance(
            content, (str, MessagesModel.Message, *structured_message_types)
        ):
            content = str(content)

        is_message_object = isinstance(content, MessagesModel.Message)
        is_structured_content = isinstance(content, structured_message_types)

        if is_message_object or is_structured_content:
            if (
                image is not None
                or file_image is not None
                or media_file_info is not None
            ):
                raise ValueError(
                    "消息构建器对象不能与 image、file_image、media_file_info 同时传入"
                )
            payload = content.build()
        else:
            if (
                content is None
                and image is None
                and file_image is None
                and media_file_info is None
            ):
                raise ValueError(
                    "content、image、file_image 和 media_file_info 至少需要提供一个"
                )

            if (image or file_image) and media_file_info:
                raise ValueError("image/file_image 与 media_file_info 不可同时存在")

            content = MessagesModel.Message(
                content=content,
                image=image,
                file_image=file_image,
                media_file_info=media_file_info,
            )
            payload = content.build()

        if message_reference_id:
            payload["message_reference"] = {
                "message_id": message_reference_id,
                "ignore_get_message_error": ignore_message_reference_error,
            }

        if is_wakeup:
            payload["is_wakeup"] = True

        if is_group_or_c2c_v2:
            if "image" in payload or "file_image" in payload:
                raise ValueError(
                    "群聊/单聊 v2 消息不支持 image/file_image，请先 upload_media 再传 media_file_info"
                )
            if msg_type is None:
                msg_type = getattr(content, "msg_type", None)
            if force_verify_image_resource:
                payload["force_verify_image_resource"] = True
            if payload.get("is_wakeup"):
                if not is_c2c_v2:
                    raise ValueError("is_wakeup 仅支持 QQ 单聊 v2 消息")
                if msg_id or event_id:
                    raise ValueError("is_wakeup 与 msg_id、event_id 互斥")
        else:
            if "media" in payload:
                raise ValueError(
                    "频道消息/频道私信不支持 media_file_info，请使用 image 或 file_image"
                )
            if payload.get("is_wakeup"):
                raise ValueError("is_wakeup 仅支持 QQ 单聊 v2 消息")
            if force_verify_image_resource:
                raise ValueError(
                    "force_verify_image_resource 仅支持群聊/单聊 v2 消息"
                )

        if msg_id:
            payload["msg_id"] = msg_id
        if event_id:
            payload["event_id"] = event_id
        if msg_type is not None:
            payload["msg_type"] = msg_type
        if msg_seq is not None:
            payload["msg_seq"] = msg_seq

        payload.update(kwargs)

        self._logger.debug(
            f"发送消息: endpoint={endpoint}, type={type(content).__name__}"
        )

        if "file_image" in payload:
            file_data = payload.pop("file_image")
            data = aiohttp.FormData()
            for key, value in payload.items():
                if value is not None:
                    if isinstance(value, dict):
                        data.add_field(key, json.dumps(value))
                    else:
                        data.add_field(key, str(value))
            data.add_field("file_image", file_data, filename="image.png")
            result = await http.post(endpoint, data=data)
        else:
            result = await http.post(endpoint, json=payload)

        response = response_model.from_dict(result)
        self._logger.debug(
            f"消息已发送: endpoint={endpoint}, msg_id={getattr(response, 'id', 'unknown')}"
        )
        return response

    async def send_guild_message(
        self,
        channel_id: str,
        content: (
            str
            | MessagesModel.Message
            | MessagesModel.MessageEmbed
            | MessagesModel.MessageArk23
            | MessagesModel.MessageArk24
            | MessagesModel.MessageArk37
            | MessagesModel.MessageMarkdown
            | None
        ) = None,
        image: str | None = None,
        file_image: bytes | BinaryIO | str | None = None,
        msg_id: str | None = None,
        event_id: str | None = None,
        message_reference_id: str | None = None,
        ignore_message_reference_error: bool = False,
    ) -> Model.GuildMessage:
        """
        发送频道消息

        支持两种方式：
        1. 传入消息对象：content=MessagesModel.MessageEmbed(title="标题", content=["行1"])
        2. 传入文本和参数：content="文本", image="https://..."

        Args:
            channel_id: 子频道 ID
            content: 消息内容，可以是文本、普通消息构建器或结构化消息对象
            image: 图片 URL（普通消息）
            file_image: 图片数据，支持 bytes、BinaryIO 或文件路径（普通消息）
            msg_id: 要回复的消息 ID（被动消息）
            event_id: 要回复的事件 ID（被动消息）
            message_reference_id: 引用消息 ID
            ignore_message_reference_error: 是否忽略引用消息错误

        Returns:
            Model.GuildMessage: 发送的消息对象

        使用示例：
            # 方式一：消息对象
            await api.send_guild_message(channel_id, MessagesModel.MessageEmbed(title="标题"))
            await api.send_guild_message(channel_id, MessagesModel.MessageMarkdown(content="# 标题"))

            # 方式二：文本+参数
            await api.send_guild_message(channel_id, "Hello")
            await api.send_guild_message(channel_id, "图片", image="https://...")
            await api.send_guild_message(channel_id, "图片", file_image="./image.png")

            # 引用回复
            await api.send_guild_message(channel_id, "回复内容", message_reference_id="引用的消息ID")
        """
        endpoint = f"/channels/{channel_id}/messages"
        return await self._send_message(
            endpoint,
            content=content,
            image=image,
            file_image=file_image,
            msg_id=msg_id,
            event_id=event_id,
            message_reference_id=message_reference_id,
            ignore_message_reference_error=ignore_message_reference_error,
            response_model=Model.GuildMessage,
        )

    async def get_guild_message(
        self,
        channel_id: str,
        message_id: str,
    ) -> Model.GuildMessage:
        """
        获取指定消息

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID

        Returns:
            Model.GuildMessage: 消息对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/messages/{message_id}")
        return Model.GuildMessage.from_dict(data)

    async def recall_guild_message(
        self,
        channel_id: str,
        message_id: str,
        hidetip: bool = False,
    ) -> bool:
        """
        撤回频道消息

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID
            hidetip: 是否隐藏提示小灰条

        Returns:
            bool: 是否撤回成功
        """
        http = await self._get_http()
        endpoint = f"/channels/{channel_id}/messages/{message_id}"
        params = {"hidetip": str(hidetip).lower()}
        await http.delete(endpoint, params=params)
        return True

    async def patch_guild_message(
        self,
        channel_id: str,
        patch_msg_id: str,
        content: str | MessagesModel.MessageMarkdown | None = None,
        msg_id: str | None = None,
        event_id: str | None = None,
    ) -> Model.GuildMessage:
        """
        修改频道 markdown 消息

        需要先申请权限才能使用此接口。
        仅支持修改 Markdown 和 Keyboard 内容。

        Args:
            channel_id: 子频道 ID
            patch_msg_id: 需要修改的消息 ID
            content: 消息内容
                      - str: 纯 Markdown 文本
                      - MessagesModel.MessageMarkdown: Markdown + Keyboard
            msg_id: 要回复的消息的 ID（被动消息）
            event_id: 要回复的事件 ID（被动消息）

        Returns:
            Model.GuildMessage: 修改后的消息对象

        使用示例：
            # 使用 Markdown 字符串修改
            await api.patch_guild_message(channel_id, msg_id, content="# 更新后的标题")

            # 使用 Markdown 消息对象修改
            md = MessagesModel.MessageMarkdown(content="# 更新后的标题")
            await api.patch_guild_message(channel_id, msg_id, content=md)

            # 使用带 Keyboard 的 Markdown 修改
            md = MessagesModel.MessageMarkdown(
                content="# 标题",
                keyboard_content={"rows": [{"buttons": [...]}]}
            )
            await api.patch_guild_message(channel_id, msg_id, content=md)
        """
        http = await self._get_http()
        endpoint = f"/channels/{channel_id}/messages/{patch_msg_id}"

        payload = {}
        if msg_id:
            payload["msg_id"] = msg_id
        if event_id:
            payload["event_id"] = event_id

        if content is not None:
            if isinstance(content, str):
                content = MessagesModel.MessageMarkdown(content=content)
            built = content.build()
            for key in ("markdown", "keyboard"):
                if key in built and built[key]:
                    payload[key] = built[key]

        data = await http.patch(endpoint, json=payload)
        return Model.GuildMessage.from_dict(data)

    async def send_group_message(
        self,
        group_openid: str,
        content: (
            str
            | MessagesModel.Message
            | MessagesModel.MessageEmbed
            | MessagesModel.MessageArk23
            | MessagesModel.MessageArk24
            | MessagesModel.MessageArk37
            | MessagesModel.MessageMarkdown
            | None
        ) = None,
        media_file_info: str | None = None,
        event_id: str | None = None,
        msg_id: str | None = None,
        msg_type: int | None = None,
        msg_seq: int | None = None,
        message_reference_id: str | None = None,
        ignore_message_reference_error: bool = False,
        force_verify_image_resource: bool = False,
    ) -> Model.GroupSendMessageResponse:
        """
        发送群聊消息

        支持两种方式：
        1. 传入消息对象：content=MessagesModel.MessageMarkdown(content="# 标题")
        2. 传入文本：content="Hello"

        Args:
            group_openid: 群 openid
            content: 消息内容，可以是文本、普通消息构建器或结构化消息对象
            media_file_info: 富媒体文件信息（群聊 v2）
            event_id: 前置收到的事件 ID（被动消息）
            msg_id: 要回复的消息 ID（被动消息）
            msg_type: 消息类型，默认按内容自动推断
            msg_seq: 回复消息的序号，与 msg_id 联合使用避免重复发送
            message_reference_id: 引用消息 ID
            ignore_message_reference_error: 是否忽略引用消息错误
            force_verify_image_resource: 是否强制校验图片资源。开启后当图片资源转存失败时
                会中断消息发送并返回失败，默认关闭

        Returns:
            Model.GroupSendMessageResponse: 发送的消息响应

        使用示例：
            # 文本消息
            await api.send_group_message(group_openid, "Hello")

            # 富媒体消息
            await api.send_group_message(
                group_openid,
                content="图片",
                media_file_info="file_info_string",
            )

            # Markdown 消息
            await api.send_group_message(group_openid, MessagesModel.MessageMarkdown(content="# 标题"))

            # Embed 消息
            await api.send_group_message(group_openid, MessagesModel.MessageEmbed(title="标题"))

            # 引用回复
            await api.send_group_message(group_openid, "回复内容", message_reference_id="引用的消息ID")
        """
        endpoint = f"/v2/groups/{group_openid}/messages"
        return await self._send_message(
            endpoint,
            content=content,
            media_file_info=media_file_info,
            msg_id=msg_id,
            event_id=event_id,
            msg_type=msg_type,
            msg_seq=msg_seq,
            message_reference_id=message_reference_id,
            ignore_message_reference_error=ignore_message_reference_error,
            force_verify_image_resource=force_verify_image_resource,
            response_model=Model.GroupSendMessageResponse,
        )

    async def recall_group_message(
        self,
        group_openid: str,
        message_id: str,
    ) -> bool:
        """
        撤回群聊消息

        Args:
            group_openid: 群 openid
            message_id: 消息 ID

        Returns:
            bool: 是否撤回成功
        """
        http = await self._get_http()
        endpoint = f"/v2/groups/{group_openid}/messages/{message_id}"
        await http.delete(endpoint)
        return True

    async def send_c2c_message(
        self,
        openid: str,
        content: (
            str
            | MessagesModel.Message
            | MessagesModel.MessageEmbed
            | MessagesModel.MessageArk23
            | MessagesModel.MessageArk24
            | MessagesModel.MessageArk37
            | MessagesModel.MessageMarkdown
            | None
        ) = None,
        media_file_info: str | None = None,
        event_id: str | None = None,
        msg_id: str | None = None,
        msg_type: int | None = None,
        msg_seq: int | None = None,
        is_wakeup: bool = False,
        message_reference_id: str | None = None,
        ignore_message_reference_error: bool = False,
        force_verify_image_resource: bool = False,
    ) -> Model.C2CSendMessageResponse:
        """
        发送单聊消息

        支持两种方式：
        1. 传入消息对象：content=MessagesModel.MessageMarkdown(content="# 标题")
        2. 传入文本：content="Hello"

        Args:
            openid: 用户 openid
            content: 消息内容，可以是文本、普通消息构建器或结构化消息对象
            media_file_info: 富媒体文件信息（QQ 单聊 v2）
            event_id: 前置收到的事件 ID（被动消息）
            msg_id: 要回复的消息 ID（被动消息）
            msg_type: 消息类型，默认按内容自动推断
            msg_seq: 回复消息的序号，与 msg_id 联合使用避免重复发送
            is_wakeup: 是否发送互动召回消息
            message_reference_id: 引用消息 ID
            ignore_message_reference_error: 是否忽略引用消息错误
            force_verify_image_resource: 是否强制校验图片资源。开启后当图片资源转存失败时
                会中断消息发送并返回失败，默认关闭

        Returns:
            Model.C2CSendMessageResponse: 发送的消息响应

        使用示例：
            # 文本消息
            await api.send_c2c_message(openid, "Hello")

            # 富媒体消息
            await api.send_c2c_message(
                openid,
                content="图片",
                media_file_info="file_info_string",
            )

            # Markdown 消息
            await api.send_c2c_message(openid, MessagesModel.MessageMarkdown(content="# 标题"))

            # Embed 消息
            await api.send_c2c_message(openid, MessagesModel.MessageEmbed(title="标题"))

            # 引用回复
            await api.send_c2c_message(openid, "回复内容", message_reference_id="引用的消息ID")
        """
        endpoint = f"/v2/users/{openid}/messages"
        return await self._send_message(
            endpoint,
            content=content,
            media_file_info=media_file_info,
            msg_id=msg_id,
            event_id=event_id,
            msg_type=msg_type,
            msg_seq=msg_seq,
            is_wakeup=is_wakeup,
            message_reference_id=message_reference_id,
            ignore_message_reference_error=ignore_message_reference_error,
            force_verify_image_resource=force_verify_image_resource,
            response_model=Model.C2CSendMessageResponse,
        )

    async def recall_c2c_message(
        self,
        openid: str,
        message_id: str,
    ) -> bool:
        """
        撤回单聊消息

        Args:
            openid: 用户 openid
            message_id: 消息 ID

        Returns:
            bool: 是否撤回成功
        """
        http = await self._get_http()
        endpoint = f"/v2/users/{openid}/messages/{message_id}"
        await http.delete(endpoint)
        return True

    async def create_dms(
        self,
        recipient_id: str,
        source_guild_id: str,
    ) -> Model.DMS:
        """
        创建私信会话

        Args:
            recipient_id: 接收者 ID
            source_guild_id: 源频道 ID

        Returns:
            Model.DMS: 私信会话对象
        """
        http = await self._get_http()
        payload = {"recipient_id": recipient_id, "source_guild_id": source_guild_id}
        data = await http.post("/users/@me/dms", json=payload)
        return Model.DMS.from_dict(data)

    async def send_direct_message(
        self,
        guild_id: str,
        content: (
            str
            | MessagesModel.Message
            | MessagesModel.MessageEmbed
            | MessagesModel.MessageArk23
            | MessagesModel.MessageArk24
            | MessagesModel.MessageArk37
            | MessagesModel.MessageMarkdown
            | None
        ) = None,
        image: str | None = None,
        file_image: bytes | BinaryIO | str | None = None,
        msg_id: str | None = None,
        event_id: str | None = None,
        message_reference_id: str | None = None,
        ignore_message_reference_error: bool = False,
    ) -> Model.GuildMessage:
        """
        发送频道私信消息

        支持两种方式：
        1. 传入消息对象：content=MessagesModel.MessageEmbed(title="标题")
        2. 传入文本和参数：content="文本", image="https://..."

        Args:
            guild_id: 私信频道 ID
            content: 消息内容，可以是文本、普通消息构建器或结构化消息对象
            image: 图片 URL（普通消息）
            file_image: 图片数据，支持 bytes、BinaryIO 或文件路径（普通消息）
            msg_id: 要回复的消息 ID（被动消息）
            event_id: 要回复的事件 ID（被动消息）
            message_reference_id: 引用消息 ID
            ignore_message_reference_error: 是否忽略引用消息错误

        Returns:
            Model.GuildMessage: 发送的消息对象

        使用示例：
            # 方式一：消息对象
            await api.send_direct_message(guild_id, MessagesModel.MessageEmbed(title="标题"))

            # 方式二：文本+参数
            await api.send_direct_message(guild_id, "Hello")
            await api.send_direct_message(guild_id, "图片", image="https://...")

            # 引用回复
            await api.send_direct_message(guild_id, "回复内容", message_reference_id="引用的消息ID")
        """
        endpoint = f"/dms/{guild_id}/messages"
        return await self._send_message(
            endpoint,
            content=content,
            image=image,
            file_image=file_image,
            msg_id=msg_id,
            event_id=event_id,
            message_reference_id=message_reference_id,
            ignore_message_reference_error=ignore_message_reference_error,
            response_model=Model.GuildMessage,
        )

    async def recall_direct_message(
        self,
        guild_id: str,
        message_id: str,
        hidetip: bool = False,
    ) -> bool:
        """
        撤回频道私信消息

        Args:
            guild_id: 私信频道 ID
            message_id: 消息 ID
            hidetip: 是否隐藏提示小灰条

        Returns:
            bool: 是否撤回成功
        """
        http = await self._get_http()
        endpoint = f"/dms/{guild_id}/messages/{message_id}"
        params = {"hidetip": str(hidetip).lower()}
        await http.delete(endpoint, params=params)
        return True

    async def get_guild_members(
        self,
        guild_id: str,
        after: str = "0",
        limit: int = 100,
    ) -> list[Model.Member]:
        """
        获取频道成员列表

        Args:
            guild_id: 频道 ID
            after: 上一次回包中最后一个 member 的 user id
            limit: 分页大小，默认 100，最大 1000

        Returns:
            list[Model.Member]: 成员对象列表
        """
        http = await self._get_http()
        params = {"after": after, "limit": limit}
        data = await http.get(f"/guilds/{guild_id}/members", params=params)
        return [Model.Member.from_dict(m) for m in data]

    async def get_guild_member(
        self,
        guild_id: str,
        user_id: str,
    ) -> Model.Member:
        """
        获取频道成员详情

        Args:
            guild_id: 频道 ID
            user_id: 用户 ID

        Returns:
            Model.Member: 成员对象
        """
        http = await self._get_http()
        data = await http.get(f"/guilds/{guild_id}/members/{user_id}")
        return Model.Member.from_dict(data)

    async def delete_guild_member(
        self,
        guild_id: str,
        user_id: str,
        add_blacklist: bool = False,
        delete_history_msg_days: int = 0,
    ) -> bool:
        """
        删除频道成员

        Args:
            guild_id: 频道 ID
            user_id: 用户 ID
            add_blacklist: 是否同时添加到黑名单
            delete_history_msg_days: 撤回消息天数（3, 7, 15, 30, -1 全部）

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        payload = {
            "add_blacklist": add_blacklist,
            "delete_history_msg_days": delete_history_msg_days,
        }
        await http.delete(f"/guilds/{guild_id}/members/{user_id}", json=payload)
        return True

    async def get_group_members(
        self,
        group_openid: str,
        cursor: str | None = None,
    ) -> Model.GroupMembersResponse:
        """
        获取群成员列表

        接口: GET /v2/groups/{group_openid}/members
        每次最多返回 30 条，支持分页。

        注意:
            该能力当前处于内邀接入阶段，仅白名单机器人可用；
            无权限时返回错误码 11253（应用无接口访问权限）。

        Args:
            group_openid: 群 OpenID
            cursor: 分页游标，首次请求可不传或传空串；后续传上一次响应的 next_cursor

        Returns:
            Model.GroupMembersResponse: 包含 members（成员列表）与 next_cursor（下一页游标）的响应

        使用示例：
            # 首次获取
            resp = await api.get_group_members("3E5D8A1F7B2C9E4D6A0F1B3C5D7E9F2A")
            for member in resp.members:
                print(member.member_openid, member.username, member.member_role)

            # 翻页（next_cursor 为空串表示已到末页）
            if not resp.is_end:
                nxt = await api.get_group_members(group_openid, cursor=resp.next_cursor)
        """
        http = await self._get_http()
        params = {"cursor": cursor or ""}
        data = await http.get(f"/v2/groups/{group_openid}/members", params=params)
        return Model.GroupMembersResponse.from_dict(data)

    async def get_all_group_members(
        self,
        group_openid: str,
        max_count: int | None = None,
    ) -> list[Model.GroupMember]:
        """
        获取群成员全量列表（自动翻页）

        封装 get_group_members，按 next_cursor 持续拉取直到末页。

        Args:
            group_openid: 群 OpenID
            max_count: 最多拉取人数，None 表示不限制

        Returns:
            list[Model.GroupMember]: 群成员列表

        使用示例：
            members = await api.get_all_group_members(group_openid)
            admins = [m for m in members if m.is_admin]
        """
        http = await self._get_http()
        members: list[Model.GroupMember] = []
        cursor: str | None = None
        seen_cursors: set[str] = set()
        page = 0

        while True:
            params = {"cursor": cursor or ""}
            data = await http.get(
                f"/v2/groups/{group_openid}/members", params=params
            )
            response = Model.GroupMembersResponse.from_dict(data)
            if response is None:
                break

            members.extend(response.members)
            page += 1

            self._logger.debug(
                f"获取群成员列表: group_openid={group_openid}, page={page}, "
                f"累计={len(members)}, next_cursor={response.next_cursor or '(空)'}"
            )

            if max_count is not None and len(members) >= max_count:
                return members[:max_count]

            if response.is_end:
                break

            # 防止游标异常导致死循环
            if response.next_cursor in seen_cursors:
                self._logger.warning(
                    f"群成员列表游标重复，终止翻页: group_openid={group_openid}, "
                    f"cursor={response.next_cursor}"
                )
                break

            seen_cursors.add(response.next_cursor)
            cursor = response.next_cursor

        return members

    # ==================== 群管理 API ====================

    async def get_group_info(self, group_openid: str) -> Model.GroupInfo:
        """
        获取群基本信息

        接口: GET /v2/groups/{group_openid}/info

        注意:
            需申请接口权限，无权限时返回错误码 11253。

        Args:
            group_openid: 群 OpenID

        Returns:
            Model.GroupInfo: 群基本信息（名称、简介、分类、标签、成员数）

        使用示例：
            info = await api.get_group_info(group_openid)
            print(info.group_name, info.group_member_num)
        """
        http = await self._get_http()
        data = await http.get(f"/v2/groups/{group_openid}/info")
        return Model.GroupInfo.from_dict(data)

    async def get_group_bot_state(self, group_openid: str) -> Model.GroupBotState:
        """
        获取机器人群内状态

        接口: GET /v2/groups/{group_openid}/bot_state

        Args:
            group_openid: 群 OpenID

        Returns:
            Model.GroupBotState: 机器人自身在该群的状态（角色、入群时间、消息接收设置等）
        """
        http = await self._get_http()
        data = await http.get(f"/v2/groups/{group_openid}/bot_state")
        return Model.GroupBotState.from_dict(data)

    async def get_group_member(
        self,
        group_openid: str,
        member_openid: str,
    ) -> Model.GroupMember:
        """
        获取群成员信息

        接口: GET /v2/groups/{group_openid}/members/{member_openid}

        Args:
            group_openid: 群 OpenID
            member_openid: 成员 OpenID

        Returns:
            Model.GroupMember: 群成员详情
        """
        http = await self._get_http()
        data = await http.get(
            f"/v2/groups/{group_openid}/members/{member_openid}"
        )
        return Model.GroupMember.from_dict(data)

    async def batch_remove_group_members(
        self,
        group_openid: str,
        member_openids: list[str],
        add_to_member_blacklist: bool = False,
    ) -> Model.BatchRemoveMembersResult:
        """
        群成员批量移除

        接口: POST /v2/groups/{group_openid}/batch_remove_members

        Args:
            group_openid: 群 OpenID
            member_openids: 需要移除的成员 openid 列表，单次最多 20 个
            add_to_member_blacklist: 是否同时加入群黑名单，默认 False

        Returns:
            Model.BatchRemoveMembersResult: 移除结果，含拉黑失败的 openid 列表

        使用示例：
            result = await api.batch_remove_group_members(group_openid, ["openid1"])
            if result.is_success:
                print("移除成功")
        """
        if not member_openids:
            raise ValueError("member_openids 不能为空")
        if len(member_openids) > 20:
            raise ValueError("member_openids 单次最多 20 个")

        http = await self._get_http()
        payload = {
            "member_openids": member_openids,
            "add_to_member_blacklist": add_to_member_blacklist,
        }
        data = await http.post(
            f"/v2/groups/{group_openid}/batch_remove_members", json=payload
        )
        return Model.BatchRemoveMembersResult.from_dict(data)

    async def get_group_member_blacklist(
        self,
        group_openid: str,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Model.GroupBlacklistResponse:
        """
        群黑名单查询

        接口: GET /v2/groups/{group_openid}/member_blacklist

        Args:
            group_openid: 群 OpenID
            cursor: 分页游标，首次不传或传空串
            limit: 单页数量，默认 20，最大 100

        Returns:
            Model.GroupBlacklistResponse: 黑名单用户列表与下一页游标
        """
        http = await self._get_http()
        params: dict[str, Any] = {"cursor": cursor or ""}
        if limit is not None:
            params["limit"] = limit
        data = await http.get(
            f"/v2/groups/{group_openid}/member_blacklist", params=params
        )
        return Model.GroupBlacklistResponse.from_dict(data)

    async def operate_group_member_blacklist(
        self,
        group_openid: str,
        op: str,
        member_openids: list[str],
    ) -> Model.GroupBlacklistOpResult:
        """
        群黑名单操作（批量加入 / 移出）

        接口: POST /v2/groups/{group_openid}/member_blacklist

        Args:
            group_openid: 群 OpenID
            op: 操作类型，``add`` 加入黑名单、``del`` 移出黑名单
                （可用 Model.GroupBlacklistOp）
            member_openids: 目标成员 openid 列表，单次最多 20 个

        Returns:
            Model.GroupBlacklistOpResult: 操作结果，含失败的 openid 列表

        注意:
            目标成员仍在群中时无法加入黑名单。
        """
        if op not in (Model.GroupBlacklistOp.ADD, Model.GroupBlacklistOp.DEL):
            raise ValueError("op 仅支持 add / del")
        if not member_openids:
            raise ValueError("member_openids 不能为空")
        if len(member_openids) > 20:
            raise ValueError("member_openids 单次最多 20 个")

        http = await self._get_http()
        payload = {"op": op, "member_openids": member_openids}
        data = await http.post(
            f"/v2/groups/{group_openid}/member_blacklist", json=payload
        )
        return Model.GroupBlacklistOpResult.from_dict(data)

    async def add_group_member_blacklist(
        self,
        group_openid: str,
        member_openids: list[str],
    ) -> Model.GroupBlacklistOpResult:
        """批量加入群黑名单（operate_group_member_blacklist 的便捷封装）"""
        return await self.operate_group_member_blacklist(
            group_openid, Model.GroupBlacklistOp.ADD, member_openids
        )

    async def remove_group_member_blacklist(
        self,
        group_openid: str,
        member_openids: list[str],
    ) -> Model.GroupBlacklistOpResult:
        """批量移出群黑名单（operate_group_member_blacklist 的便捷封装）"""
        return await self.operate_group_member_blacklist(
            group_openid, Model.GroupBlacklistOp.DEL, member_openids
        )

    async def get_group_restrict_chat_setting(
        self,
        group_openid: str,
    ) -> Model.GroupRestrictChatSetting:
        """
        查询群禁言状态

        接口: GET /v2/groups/{group_openid}/restrict_chat_setting

        Args:
            group_openid: 群 OpenID

        Returns:
            Model.GroupRestrictChatSetting: 群级禁言规则与当前禁言中的成员列表

        使用示例：
            setting = await api.get_group_restrict_chat_setting(group_openid)
            if setting.global_rule and setting.global_rule.is_enabled:
                print("全员禁言中:", setting.global_rule.mode)
        """
        http = await self._get_http()
        data = await http.get(f"/v2/groups/{group_openid}/restrict_chat_setting")
        return Model.GroupRestrictChatSetting.from_dict(data)

    async def set_group_member_mute(
        self,
        group_openid: str,
        members: list[dict],
    ) -> bool:
        """
        设置群成员禁言

        接口: POST /v2/groups/{group_openid}/restrict_chat_setting

        Args:
            group_openid: 群 OpenID
            members: 禁言配置列表，单次最多 20 个，每项为字典：
                - ``op``: 必填，``add`` 增加禁言 / ``update`` 更新到期时间 / ``del`` 解除禁言
                - ``member_openid``: 必填，被禁言成员 openid
                - ``mute_expire_at``: 禁言到期时间（RFC3339）；``op=del`` 可传空串立即解除

        Returns:
            bool: 是否设置成功

        注意:
            增加/更新时只能操作普通成员，不能操作群主、管理员、机器人。

        使用示例：
            await api.set_group_member_mute(
                group_openid,
                [{
                    "op": "add",
                    "member_openid": "xxx",
                    "mute_expire_at": "2026-08-05T11:23:05+08:00",
                }],
            )
        """
        if not members:
            raise ValueError("members 不能为空")
        if len(members) > 20:
            raise ValueError("members 单次最多 20 个")

        http = await self._get_http()
        await http.post(
            f"/v2/groups/{group_openid}/restrict_chat_setting",
            json={"members": members},
        )
        return True

    async def mute_group_members(
        self,
        group_openid: str,
        member_openids: list[str],
        mute_expire_at: str,
    ) -> bool:
        """
        批量禁言群成员（set_group_member_mute 的便捷封装）

        Args:
            group_openid: 群 OpenID
            member_openids: 被禁言成员 openid 列表，最多 20 个
            mute_expire_at: 禁言到期时间（RFC3339 格式）
        """
        if len(member_openids) > 20:
            raise ValueError("member_openids 单次最多 20 个")
        return await self.set_group_member_mute(
            group_openid,
            [
                {
                    "op": Model.GroupMuteOp.ADD,
                    "member_openid": openid,
                    "mute_expire_at": mute_expire_at,
                }
                for openid in member_openids
            ],
        )

    async def unmute_group_members(
        self,
        group_openid: str,
        member_openids: list[str],
    ) -> bool:
        """
        批量解除群成员禁言（set_group_member_mute 的便捷封装）

        Args:
            group_openid: 群 OpenID
            member_openids: 成员 openid 列表，最多 20 个
        """
        if len(member_openids) > 20:
            raise ValueError("member_openids 单次最多 20 个")
        return await self.set_group_member_mute(
            group_openid,
            [
                {
                    "op": Model.GroupMuteOp.DEL,
                    "member_openid": openid,
                    "mute_expire_at": "",
                }
                for openid in member_openids
            ],
        )

    async def get_group_join_requests(
        self,
        group_openid: str,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Model.JoinRequestListResponse:
        """
        入群申请列表拉取

        接口: GET /v2/groups/{group_openid}/join_request_list

        Args:
            group_openid: 群 OpenID
            cursor: 分页游标，首次不传或传空串
            limit: 单页数量，默认 20，最大 50

        Returns:
            Model.JoinRequestListResponse: 入群申请列表（字段映射为 ``requests``）
        """
        http = await self._get_http()
        params: dict[str, Any] = {"cursor": cursor or ""}
        if limit is not None:
            params["limit"] = limit
        data = await http.get(
            f"/v2/groups/{group_openid}/join_request_list", params=params
        )
        return Model.JoinRequestListResponse.from_dict(data)

    async def approval_join_request(
        self,
        group_openid: str,
        member_openid: str,
        op: str,
        join_request_id: str | None = None,
        reject_reason: str | None = None,
        add_to_member_blacklist: bool = False,
    ) -> bool:
        """
        入群申请审批

        接口: POST /v2/groups/{group_openid}/approval_join_request/{member_openid}

        Args:
            group_openid: 群 OpenID
            member_openid: 申请人 openid
            op: 审批动作，``approve`` 通过 / ``decline`` 拒绝
                （可用 Model.JoinRequestApprovalOp）
            join_request_id: 申请 ID（来自入群申请列表或 GROUP_JOIN_REQUEST 事件）
            reject_reason: 拒绝理由，``op=decline`` 时可填
            add_to_member_blacklist: 是否同时加入群黑名单，默认 False

        Returns:
            bool: 是否审批成功
        """
        if op not in (
            Model.JoinRequestApprovalOp.APPROVE,
            Model.JoinRequestApprovalOp.DECLINE,
        ):
            raise ValueError("op 仅支持 approve / decline")

        payload: dict[str, Any] = {"op": op}
        if join_request_id:
            payload["join_request_id"] = join_request_id
        if reject_reason:
            payload["reject_reason"] = reject_reason
        if add_to_member_blacklist:
            payload["add_to_member_blacklist"] = True

        http = await self._get_http()
        await http.post(
            f"/v2/groups/{group_openid}/approval_join_request/{member_openid}",
            json=payload,
        )
        return True

    async def approve_join_request(
        self,
        group_openid: str,
        member_openid: str,
        join_request_id: str | None = None,
    ) -> bool:
        """通过入群申请（approval_join_request 的便捷封装）"""
        return await self.approval_join_request(
            group_openid,
            member_openid,
            Model.JoinRequestApprovalOp.APPROVE,
            join_request_id=join_request_id,
        )

    async def decline_join_request(
        self,
        group_openid: str,
        member_openid: str,
        join_request_id: str | None = None,
        reject_reason: str | None = None,
        add_to_member_blacklist: bool = False,
    ) -> bool:
        """拒绝入群申请（approval_join_request 的便捷封装）"""
        return await self.approval_join_request(
            group_openid,
            member_openid,
            Model.JoinRequestApprovalOp.DECLINE,
            join_request_id=join_request_id,
            reject_reason=reject_reason,
            add_to_member_blacklist=add_to_member_blacklist,
        )

    async def get_join_approval_strategies(
        self,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Model.JoinApprovalStrategyListResponse:
        """
        查询入群自动审批策略列表

        接口: GET /v2/groups/join_approval_strategy

        Args:
            cursor: 分页游标，首次不传或传空串
            limit: 单页数量，默认 20，最大 50

        Returns:
            Model.JoinApprovalStrategyListResponse: 生效中的策略列表
        """
        http = await self._get_http()
        params: dict[str, Any] = {"cursor": cursor or ""}
        if limit is not None:
            params["limit"] = limit
        data = await http.get("/v2/groups/join_approval_strategy", params=params)
        return Model.JoinApprovalStrategyListResponse.from_dict(data)

    async def create_join_approval_strategy(
        self,
        group_openids: list[str] | None = None,
        group_ids: list[str] | None = None,
        is_enable: str = Model.JoinApprovalStrategyEnable.ON,
        expire_at: str | None = None,
        remark: str | None = None,
    ) -> Model.JoinApprovalStrategyCreated:
        """
        创建入群自动审批策略

        接口: POST /v2/groups/join_approval_strategy

        Args:
            group_openids: 关联的群 openid 列表，最多 100 个；与 group_ids 互斥
            group_ids: 关联的 QQ 群号列表，最多 100 个；与 group_openids 互斥
            is_enable: 是否启用，``on`` / ``off``，默认 ``on``
            expire_at: 过期时间（RFC3339），不传默认一年过期
            remark: 策略备注，最多 255 个汉字

        Returns:
            Model.JoinApprovalStrategyCreated: 含策略 ID、启用状态与过期时间

        注意:
            group_openids 与 group_ids 必须二选一。
        """
        if bool(group_openids) == bool(group_ids):
            raise ValueError("group_openids 与 group_ids 必须二选一")

        payload: dict[str, Any] = {"is_enable": is_enable}
        if group_openids:
            payload["group_openids"] = group_openids
        if group_ids:
            payload["group_ids"] = group_ids
        if expire_at:
            payload["expire_at"] = expire_at
        if remark:
            payload["remark"] = remark

        http = await self._get_http()
        data = await http.post("/v2/groups/join_approval_strategy", json=payload)
        return Model.JoinApprovalStrategyCreated.from_dict(data)

    async def update_join_approval_strategy(
        self,
        strategy_id: str,
        is_enable: str | None = None,
        expire_at: str | None = None,
        group_action: dict | None = None,
        remark: str | None = None,
    ) -> Model.JoinApprovalStrategyUpdated:
        """
        修改入群自动审批策略

        接口: PATCH /v2/groups/join_approval_strategy/{strategy_id}

        Args:
            strategy_id: 策略 ID
            is_enable: 是否启用，``on`` / ``off``
            expire_at: 过期时间（RFC3339）
            group_action: 关联群增删操作，形如
                ``{"op": "add", "group_openids": [...]}`` 或
                ``{"op": "del", "group_ids": [...]}``；
                群标识形式须与创建时一致
            remark: 策略备注

        Returns:
            Model.JoinApprovalStrategyUpdated: 修改后的启用状态与过期时间
        """
        payload: dict[str, Any] = {}
        if is_enable:
            payload["is_enable"] = is_enable
        if expire_at:
            payload["expire_at"] = expire_at
        if group_action:
            payload["group_action"] = group_action
        if remark:
            payload["remark"] = remark

        if not payload:
            raise ValueError("至少需要提供一个待修改字段")

        http = await self._get_http()
        data = await http.patch(
            f"/v2/groups/join_approval_strategy/{strategy_id}", json=payload
        )
        return Model.JoinApprovalStrategyUpdated.from_dict(data)

    async def delete_join_approval_strategy(self, strategy_id: str) -> bool:
        """
        删除入群自动审批策略

        接口: DELETE /v2/groups/join_approval_strategy/{strategy_id}

        Args:
            strategy_id: 策略 ID

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/v2/groups/join_approval_strategy/{strategy_id}")
        return True

    async def execute_join_approval_strategy(self, strategy_id: str) -> bool:
        """
        执行入群自动审批策略

        接口: POST /v2/groups/join_approval_strategy/{strategy_id}/execute

        Args:
            strategy_id: 策略 ID

        Returns:
            bool: 是否执行成功
        """
        http = await self._get_http()
        await http.post(f"/v2/groups/join_approval_strategy/{strategy_id}/execute")
        return True

    async def update_join_approval_strategy_whitelist(
        self,
        strategy_id: str,
        op: str,
        whitelist_users: list[str],
    ) -> Model.WhitelistUsersResponse:
        """
        修改入群自动审批策略的白名单号码

        接口: POST /v2/groups/join_approval_strategy/{strategy_id}/whitelist_users

        Args:
            strategy_id: 策略 ID
            op: 操作类型，``add`` 新增 / ``del`` 删除
                （可用 Model.JoinApprovalStrategyOp）
            whitelist_users: QQ 号码列表（字符串），单次最多 10000 个

        Returns:
            Model.WhitelistUsersResponse: 操作后白名单数量与更新时间
        """
        if op not in (
            Model.JoinApprovalStrategyOp.ADD,
            Model.JoinApprovalStrategyOp.DEL,
        ):
            raise ValueError("op 仅支持 add / del")
        if not whitelist_users:
            raise ValueError("whitelist_users 不能为空")

        http = await self._get_http()
        data = await http.post(
            f"/v2/groups/join_approval_strategy/{strategy_id}/whitelist_users",
            json={"op": op, "whitelist_users": [str(u) for u in whitelist_users]},
        )
        return Model.WhitelistUsersResponse.from_dict(data)

    # ==================== 自定义菜单与指令面板 API ====================

    async def get_menu(self) -> Model.MenuResponse:
        """
        查询全局自定义菜单

        接口: GET /v2/menu

        自定义菜单展示在机器人单聊窗口底部，设置后对所有用户生效。

        Returns:
            Model.MenuResponse: 含菜单版本号与当前生效的菜单配置（未设置过时 menu 为 None）
        """
        http = await self._get_http()
        data = await http.get("/v2/menu")
        return Model.MenuResponse.from_dict(data)

    async def set_menu(self, menu: "Model.Menu | dict") -> Model.MenuVersionResponse:
        """
        修改全局自定义菜单

        接口: PUT /v2/menu

        注意:
            会覆盖原有的完整菜单配置；菜单项最多 10 个，
            ``type=menu`` 的二级菜单最多 5 个且不支持再嵌套。
            链接必须以 ``https://`` 开头。

        Args:
            menu: Model.Menu 实例或其字典形式，形如 ``{"items": [...]}``

        Returns:
            Model.MenuVersionResponse: 本次修改后的菜单版本号

        使用示例：
            await api.set_menu({
                "items": [
                    {"type": "send_message", "name": "帮助", "send_message": "/help"},
                    {"type": "link", "name": "官网", "link": "https://example.com"},
                ]
            })
        """
        if isinstance(menu, Model.Menu):
            payload = menu.to_dict()
        else:
            payload = dict(menu)

        http = await self._get_http()
        data = await http.put("/v2/menu", json={"menu": payload})
        return Model.MenuVersionResponse.from_dict(data)

    async def get_panels(
        self,
        scope: str,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Model.PanelsResponse:
        """
        查询指令面板列表

        接口: GET /v2/panels

        Args:
            scope: 生效场景，``c2c`` / ``group`` / ``channel`` / ``dm``
                （可用 Model.PanelScope）
            cursor: 分页游标，首次不传或传空串
            limit: 每页条数，默认 20，最大 50

        Returns:
            Model.PanelsResponse: 面板记录列表（按设置时间倒序）
        """
        if scope not in (
            Model.PanelScope.C2C,
            Model.PanelScope.GROUP,
            Model.PanelScope.CHANNEL,
            Model.PanelScope.DM,
        ):
            raise ValueError("scope 仅支持 c2c / group / channel / dm")

        http = await self._get_http()
        params: dict[str, Any] = {"scope": scope, "cursor": cursor or ""}
        if limit is not None:
            params["limit"] = limit
        data = await http.get("/v2/panels", params=params)
        return Model.PanelsResponse.from_dict(data)

    async def create_panel(
        self,
        scope: str,
        panel: "Model.Panel | dict",
        target_type: str = Model.PanelTargetType.ALL,
        user_openids: list[str] | None = None,
        group_openids: list[str] | None = None,
    ) -> Model.PanelCreateResponse:
        """
        创建指令面板

        接口: POST /v2/panels

        Args:
            scope: 生效场景，``c2c`` / ``group`` / ``channel`` / ``dm``
            panel: Model.Panel 实例或其字典形式
            target_type: 作用范围，``all`` 全局 / ``specific`` 指定对象；
                ``channel`` 与 ``dm`` 场景仅支持 ``all``
            user_openids: 用户 openid 列表，仅 c2c + specific 时有效，最多 20 个
            group_openids: 群 openid 列表，仅 group + specific 时有效，最多 20 个

        Returns:
            Model.PanelCreateResponse: 新创建的面板 ID
        """
        if scope not in (
            Model.PanelScope.C2C,
            Model.PanelScope.GROUP,
            Model.PanelScope.CHANNEL,
            Model.PanelScope.DM,
        ):
            raise ValueError("scope 仅支持 c2c / group / channel / dm")
        if target_type not in (
            Model.PanelTargetType.ALL,
            Model.PanelTargetType.SPECIFIC,
        ):
            raise ValueError("target_type 仅支持 all / specific")
        if target_type == Model.PanelTargetType.SPECIFIC and scope not in (
            Model.PanelScope.C2C,
            Model.PanelScope.GROUP,
        ):
            raise ValueError("channel / dm 场景仅支持 target_type=all")

        payload: dict[str, Any] = {
            "scope": scope,
            "target_type": target_type,
            "panel": panel.to_dict() if isinstance(panel, Model.Panel) else dict(panel),
        }
        if user_openids:
            payload["user_openids"] = user_openids
        if group_openids:
            payload["group_openids"] = group_openids

        http = await self._get_http()
        data = await http.post("/v2/panels", json=payload)
        return Model.PanelCreateResponse.from_dict(data)

    async def get_panel(self, panel_id: str) -> Model.PanelRecord:
        """
        查询指令面板详情

        接口: GET /v2/panels/{panel_id}

        Args:
            panel_id: 面板 ID

        Returns:
            Model.PanelRecord: 面板详情，specific 面板会返回关联的用户/群 openid 列表
        """
        http = await self._get_http()
        data = await http.get(f"/v2/panels/{panel_id}")
        return Model.PanelRecord.from_dict(data)

    async def update_panel(
        self,
        panel_id: str,
        panel: "Model.Panel | dict",
    ) -> Model.PanelVersionResponse:
        """
        修改指令面板

        接口: PUT /v2/panels/{panel_id}

        注意:
            会覆盖原有的面板元素列表和备注，不影响已关联的用户/群列表。

        Args:
            panel_id: 面板 ID
            panel: Model.Panel 实例或其字典形式

        Returns:
            Model.PanelVersionResponse: 修改后的面板版本号
        """
        payload = panel.to_dict() if isinstance(panel, Model.Panel) else dict(panel)
        http = await self._get_http()
        data = await http.put(f"/v2/panels/{panel_id}", json={"panel": payload})
        return Model.PanelVersionResponse.from_dict(data)

    async def delete_panel(self, panel_id: str) -> bool:
        """
        删除指令面板

        接口: DELETE /v2/panels/{panel_id}

        Args:
            panel_id: 面板 ID

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/v2/panels/{panel_id}")
        return True

    async def update_panel_target(
        self,
        panel_id: str,
        op: str,
        user_openids: list[str] | None = None,
        group_openids: list[str] | None = None,
    ) -> bool:
        """
        修改指令面板关联对象

        接口: PUT /v2/panels/{panel_id}/target

        Args:
            panel_id: 面板 ID
            op: 操作类型，``add`` 添加关联 / ``del`` 移除关联
                （可用 Model.PanelTargetOp）
            user_openids: 用户 openid 列表，仅 c2c 场景有效，最多 20 个
            group_openids: 群 openid 列表，仅 group 场景有效，最多 20 个

        Returns:
            bool: 是否修改成功

        注意:
            target_type=all 的全局面板不支持此操作。
        """
        if op not in (Model.PanelTargetOp.ADD, Model.PanelTargetOp.DEL):
            raise ValueError("op 仅支持 add / del")
        if not user_openids and not group_openids:
            raise ValueError("user_openids 与 group_openids 至少提供一个")

        payload: dict[str, Any] = {"op": op}
        if user_openids:
            payload["user_openids"] = user_openids
        if group_openids:
            payload["group_openids"] = group_openids

        http = await self._get_http()
        await http.put(f"/v2/panels/{panel_id}/target", json=payload)
        return True

    async def get_channel_online_nums(
        self, channel_id: str
    ) -> Model.OnlineNumsResponse:
        """
        获取子频道在线成员数

        Args:
            channel_id: 子频道 ID

        Returns:
            Model.OnlineNumsResponse: 在线成员数响应
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/online_nums")
        return Model.OnlineNumsResponse.from_dict(data)

    async def get_guild_roles(self, guild_id: str) -> Model.GuildRolesResponse:
        """
        获取频道身份组列表

        Args:
            guild_id: 频道 ID

        Returns:
            Model.GuildRolesResponse: 包含 roles 列表和 role_num_limit 的响应
        """
        http = await self._get_http()
        data = await http.get(f"/guilds/{guild_id}/roles")
        return Model.GuildRolesResponse.from_dict(data)

    async def create_guild_role(
        self,
        guild_id: str,
        name: str = "新的身份组",
        color: int = 0,
        hoist: int = 0,
    ) -> Model.CreateRoleResponse:
        """
        创建频道身份组

        Args:
            guild_id: 频道 ID
            name: 身份组名称
            color: 颜色值
            hoist: 是否在成员列表中单独展示

        Returns:
            Model.CreateRoleResponse: 包含 role_id 和 role 的响应
        """
        http = await self._get_http()
        payload = {"name": name, "color": color, "hoist": hoist}
        data = await http.post(f"/guilds/{guild_id}/roles", json=payload)
        return Model.CreateRoleResponse.from_dict(data)

    async def update_guild_role(
        self,
        guild_id: str,
        role_id: str,
        name: str | None = None,
        color: int | None = None,
        hoist: int | None = None,
    ) -> Model.CreateRoleResponse:
        """
        修改频道身份组

        Args:
            guild_id: 频道 ID
            role_id: 身份组 ID
            name: 身份组名称
            color: 颜色值
            hoist: 是否在成员列表中单独展示

        Returns:
            Model.CreateRoleResponse: 包含 role_id 和 role 的响应
        """
        http = await self._get_http()
        payload = {}
        if name is not None:
            payload["name"] = name
        if color is not None:
            payload["color"] = color
        if hoist is not None:
            payload["hoist"] = hoist
        data = await http.patch(f"/guilds/{guild_id}/roles/{role_id}", json=payload)
        return Model.CreateRoleResponse.from_dict(data)

    async def delete_guild_role(
        self,
        guild_id: str,
        role_id: str,
    ) -> bool:
        """
        删除频道身份组

        Args:
            guild_id: 频道 ID
            role_id: 身份组 ID

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/guilds/{guild_id}/roles/{role_id}")
        return True

    async def add_guild_member_role(
        self,
        guild_id: str,
        user_id: str,
        role_id: str,
        channel_id: str | None = None,
    ) -> bool:
        """
        添加成员到身份组

        Args:
            guild_id: 频道 ID
            user_id: 用户 ID
            role_id: 身份组 ID
            channel_id: 子频道 ID（当身份组为子频道管理员时需要）

        Returns:
            bool: 是否添加成功
        """
        http = await self._get_http()
        endpoint = f"/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
        payload = {}
        if channel_id:
            payload["channel"] = {"id": channel_id}
        await http.put(endpoint, json=payload)
        return True

    async def remove_guild_member_role(
        self,
        guild_id: str,
        user_id: str,
        role_id: str,
        channel_id: str | None = None,
    ) -> bool:
        """
        从身份组移除成员

        Args:
            guild_id: 频道 ID
            user_id: 用户 ID
            role_id: 身份组 ID
            channel_id: 子频道 ID（当身份组为子频道管理员时需要）

        Returns:
            bool: 是否移除成功
        """
        http = await self._get_http()
        endpoint = f"/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
        payload = {}
        if channel_id:
            payload["channel"] = {"id": channel_id}
        await http.delete(endpoint, json=payload)
        return True

    async def get_guild_role_members(
        self,
        guild_id: str,
        role_id: str,
        start_index: str = "0",
        limit: int = 20,
    ) -> Model.RoleMembersResponse:
        """
        获取频道身份组成员列表

        Args:
            guild_id: 频道 ID
            role_id: 身份组 ID
            start_index: 分页起始位置
            limit: 分页大小

        Returns:
            Model.RoleMembersResponse: 包含 data 和 next 的响应
        """
        http = await self._get_http()
        params = {"start_index": start_index, "limit": limit}
        data = await http.get(
            f"/guilds/{guild_id}/roles/{role_id}/members", params=params
        )
        return Model.RoleMembersResponse.from_dict(data)

    async def mute_guild(
        self,
        guild_id: str,
        mute_seconds: int | None = None,
        mute_end_timestamp: int | None = None,
    ) -> bool:
        """
        频道全员禁言

        Args:
            guild_id: 频道 ID
            mute_seconds: 禁言秒数
            mute_end_timestamp: 禁言结束时间戳

        Returns:
            bool: 是否禁言成功
        """
        http = await self._get_http()
        payload = {}
        if mute_seconds is not None:
            payload["mute_seconds"] = str(mute_seconds)
        if mute_end_timestamp is not None:
            payload["mute_end_timestamp"] = str(mute_end_timestamp)
        await http.patch(f"/guilds/{guild_id}/mute", json=payload)
        return True

    async def mute_guild_member(
        self,
        guild_id: str,
        user_id: str,
        mute_seconds: int | None = None,
        mute_end_timestamp: int | None = None,
    ) -> bool:
        """
        频道指定成员禁言

        Args:
            guild_id: 频道 ID
            user_id: 用户 ID
            mute_seconds: 禁言秒数
            mute_end_timestamp: 禁言结束时间戳

        Returns:
            bool: 是否禁言成功
        """
        http = await self._get_http()
        payload = {}
        if mute_seconds is not None:
            payload["mute_seconds"] = str(mute_seconds)
        if mute_end_timestamp is not None:
            payload["mute_end_timestamp"] = str(mute_end_timestamp)
        await http.patch(f"/guilds/{guild_id}/members/{user_id}/mute", json=payload)
        return True

    async def mute_guild_members(
        self,
        guild_id: str,
        user_ids: list[str],
        mute_seconds: int | None = None,
        mute_end_timestamp: int | None = None,
    ) -> Model.MuteBatchResponse:
        """
        频道批量成员禁言

        Args:
            guild_id: 频道 ID
            user_ids: 用户 ID 列表
            mute_seconds: 禁言秒数
            mute_end_timestamp: 禁言结束时间戳

        Returns:
            Model.MuteBatchResponse: 设置成功的用户 ID 列表响应
        """
        http = await self._get_http()
        payload = {"user_ids": user_ids}
        if mute_seconds is not None:
            payload["mute_seconds"] = str(mute_seconds)
        if mute_end_timestamp is not None:
            payload["mute_end_timestamp"] = str(mute_end_timestamp)
        data = await http.patch(f"/guilds/{guild_id}/mute", json=payload)
        return Model.MuteBatchResponse.from_dict(data)

    async def cancel_mute_all(self, guild_id: str) -> bool:
        """
        取消频道全员禁言

        Args:
            guild_id: 频道 ID

        Returns:
            bool: 是否操作成功
        """
        http = await self._get_http()
        payload = {"mute_end_timestamp": "0", "mute_seconds": "0"}
        await http.patch(f"/guilds/{guild_id}/mute", json=payload)
        return True

    async def cancel_mute_multi_member(
        self, guild_id: str, user_ids: list[str]
    ) -> Model.MuteBatchResponse:
        """
        取消频道批量成员禁言

        Args:
            guild_id: 频道 ID
            user_ids: 用户 ID 列表

        Returns:
            Model.MuteBatchResponse: 设置成功的用户 ID 列表响应
        """
        http = await self._get_http()
        payload = {"mute_end_timestamp": "0", "mute_seconds": "0", "user_ids": user_ids}
        data = await http.patch(f"/guilds/{guild_id}/mute", json=payload)
        return Model.MuteBatchResponse.from_dict(data)

    async def get_channel_user_permissions(
        self,
        channel_id: str,
        user_id: str,
    ) -> Model.ChannelPermissions:
        """
        获取子频道用户权限

        Args:
            channel_id: 子频道 ID
            user_id: 用户 ID

        Returns:
            Model.ChannelPermissions: 子频道权限对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/members/{user_id}/permissions")
        return Model.ChannelPermissions.from_dict(data)

    async def get_channel_role_permissions(
        self,
        channel_id: str,
        role_id: str,
    ) -> Model.ChannelPermissions:
        """
        获取子频道身份组权限

        Args:
            channel_id: 子频道 ID
            role_id: 身份组 ID

        Returns:
            Model.ChannelPermissions: 子频道权限对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/roles/{role_id}/permissions")
        return Model.ChannelPermissions.from_dict(data)

    async def update_channel_user_permissions(
        self,
        channel_id: str,
        user_id: str,
        add: str | None = None,
        remove: str | None = None,
    ) -> bool:
        """
        修改子频道用户权限

        Args:
            channel_id: 子频道 ID
            user_id: 用户 ID
            add: 赋予的权限
            remove: 删除的权限

        Returns:
            bool: 是否修改成功
        """
        http = await self._get_http()
        payload = {}
        if add is not None:
            payload["add"] = add
        if remove is not None:
            payload["remove"] = remove
        await http.put(
            f"/channels/{channel_id}/members/{user_id}/permissions", json=payload
        )
        return True

    async def update_channel_role_permissions(
        self,
        channel_id: str,
        role_id: str,
        add: str | None = None,
        remove: str | None = None,
    ) -> bool:
        """
        修改子频道身份组权限

        Args:
            channel_id: 子频道 ID
            role_id: 身份组 ID
            add: 赋予的权限
            remove: 删除的权限

        Returns:
            bool: 是否修改成功
        """
        http = await self._get_http()
        payload = {}
        if add is not None:
            payload["add"] = add
        if remove is not None:
            payload["remove"] = remove
        await http.put(
            f"/channels/{channel_id}/roles/{role_id}/permissions", json=payload
        )
        return True

    async def get_guild_api_permissions(
        self, guild_id: str
    ) -> Model.APIPermissionListResponse:
        """
        获取机器人在频道可用权限列表

        Args:
            guild_id: 频道 ID

        Returns:
            Model.APIPermissionListResponse: 包含 apis 列表的响应
        """
        http = await self._get_http()
        data = await http.get(f"/guilds/{guild_id}/api_permission")
        return Model.APIPermissionListResponse.from_dict(data)

    async def demand_guild_api_permission(
        self,
        guild_id: str,
        channel_id: str,
        api_path: str,
        api_method: str,
        desc: str,
    ) -> Model.APIPermissionDemand:
        """
        发送机器人在频道接口权限的授权链接

        Args:
            guild_id: 频道 ID
            channel_id: 授权链接发送的子频道 ID
            api_path: API 接口名
            api_method: 请求方法
            desc: 机器人申请权限后可使用功能的描述

        Returns:
            Model.APIPermissionDemand: API权限需求对象
        """
        http = await self._get_http()
        payload = {
            "channel_id": channel_id,
            "api_identify": {"path": api_path, "method": api_method},
            "desc": desc,
        }
        data = await http.post(
            f"/guilds/{guild_id}/api_permission/demand", json=payload
        )
        return Model.APIPermissionDemand.from_dict(data)

    async def create_announces(
        self,
        guild_id: str,
        message_id: str | None = None,
        channel_id: str | None = None,
        announces_type: int = 0,
        recommend_channels: list[dict] | None = None,
    ) -> Model.Announces:
        """
        创建频道公告

        Args:
            guild_id: 频道 ID
            message_id: 消息 ID
            channel_id: 子频道 ID
            announces_type: 公告类别（0 成员公告，1 欢迎公告）
            recommend_channels: 推荐子频道列表

        Returns:
            Model.Announces: 公告对象
        """
        http = await self._get_http()
        payload = {"announces_type": announces_type}
        if message_id:
            payload["message_id"] = message_id
        if channel_id:
            payload["channel_id"] = channel_id
        if recommend_channels:
            payload["recommend_channels"] = recommend_channels
        data = await http.post(f"/guilds/{guild_id}/announces", json=payload)
        return Model.Announces.from_dict(data)

    async def delete_announces(
        self,
        guild_id: str,
        message_id: str = "all",
    ) -> bool:
        """
        删除频道公告

        Args:
            guild_id: 频道 ID
            message_id: 消息 ID，传 "all" 删除全部

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/guilds/{guild_id}/announces/{message_id}")
        return True

    async def get_schedules(
        self,
        channel_id: str,
        since: str | None = None,
    ) -> list[Model.Schedule]:
        """
        获取频道日程列表

        Args:
            channel_id: 子频道 ID
            since: 起始时间戳（ms）

        Returns:
            list[Model.Schedule]: 日程对象列表
        """
        http = await self._get_http()
        params = {}
        if since:
            params["since"] = since
        data = await http.get(f"/channels/{channel_id}/schedules", params=params)
        return [Model.Schedule.from_dict(s) for s in data]

    async def get_schedule(
        self,
        channel_id: str,
        schedule_id: str,
    ) -> Model.Schedule:
        """
        获取日程详情

        Args:
            channel_id: 子频道 ID
            schedule_id: 日程 ID

        Returns:
            Model.Schedule: 日程对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/schedules/{schedule_id}")
        return Model.Schedule.from_dict(data)

    async def create_schedule(
        self,
        channel_id: str,
        name: str,
        start_timestamp: str,
        end_timestamp: str,
        jump_channel_id: str | None = None,
        remind_type: str = "0",
        description: str | None = None,
    ) -> Model.Schedule:
        """
        创建日程

        Args:
            channel_id: 子频道 ID
            name: 日程名称
            start_timestamp: 开始时间戳（ms）
            end_timestamp: 结束时间戳（ms）
            jump_channel_id: 开始时跳转到的子频道 ID
            remind_type: 提醒类型（0 无提醒，1 开始时提醒，2 5分钟前，3 15分钟前，4 30分钟前，5 60分钟前）
            description: 日程描述

        Returns:
            Model.Schedule: 日程对象
        """
        http = await self._get_http()
        payload = {
            "name": name,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "remind_type": remind_type,
        }
        if jump_channel_id:
            payload["jump_channel_id"] = jump_channel_id
        if description:
            payload["description"] = description
        data = await http.post(f"/channels/{channel_id}/schedules", json=payload)
        return Model.Schedule.from_dict(data)

    async def update_schedule(
        self,
        channel_id: str,
        schedule_id: str,
        name: str | None = None,
        start_timestamp: str | None = None,
        end_timestamp: str | None = None,
        jump_channel_id: str | None = None,
        remind_type: str | None = None,
        description: str | None = None,
    ) -> Model.Schedule:
        """
        修改日程

        Args:
            channel_id: 子频道 ID
            schedule_id: 日程 ID
            name: 日程名称
            start_timestamp: 开始时间戳（ms）
            end_timestamp: 结束时间戳（ms）
            jump_channel_id: 开始时跳转到的子频道 ID
            remind_type: 提醒类型（0 无提醒，1 开始时提醒，2 5分钟前，3 15分钟前，4 30分钟前，5 60分钟前）
            description: 日程描述

        Returns:
            Model.Schedule: 日程对象
        """
        http = await self._get_http()
        payload = {}
        if name is not None:
            payload["name"] = name
        if start_timestamp is not None:
            payload["start_timestamp"] = start_timestamp
        if end_timestamp is not None:
            payload["end_timestamp"] = end_timestamp
        if jump_channel_id is not None:
            payload["jump_channel_id"] = jump_channel_id
        if remind_type is not None:
            payload["remind_type"] = remind_type
        if description is not None:
            payload["description"] = description
        data = await http.patch(
            f"/channels/{channel_id}/schedules/{schedule_id}", json=payload
        )
        return Model.Schedule.from_dict(data)

    async def delete_schedule(
        self,
        channel_id: str,
        schedule_id: str,
    ) -> bool:
        """
        删除日程

        Args:
            channel_id: 子频道 ID
            schedule_id: 日程 ID

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/channels/{channel_id}/schedules/{schedule_id}")
        return True

    async def get_pins(self, channel_id: str) -> Model.PinsMessage:
        """
        获取精华消息

        Args:
            channel_id: 子频道 ID

        Returns:
            Model.PinsMessage: 精华消息对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/pins")
        return Model.PinsMessage.from_dict(data)

    async def add_pin(
        self,
        channel_id: str,
        message_id: str,
    ) -> Model.PinsMessage:
        """
        添加精华消息

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID

        Returns:
            Model.PinsMessage: 精华消息对象
        """
        http = await self._get_http()
        data = await http.put(f"/channels/{channel_id}/pins/{message_id}")
        return Model.PinsMessage.from_dict(data)

    async def delete_pin(
        self,
        channel_id: str,
        message_id: str,
    ) -> bool:
        """
        删除精华消息

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/channels/{channel_id}/pins/{message_id}")
        return True

    async def get_reaction_users(
        self,
        channel_id: str,
        message_id: str,
        emoji_type: int,
        emoji_id: str,
        cookie: str | None = None,
        limit: int = 20,
    ) -> Model.ReactionUsers:
        """
        获取表情表态用户列表

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID
            emoji_type: 表情类型
            emoji_id: 表情 ID
            cookie: 分页 cookie
            limit: 每页数量

        Returns:
            Model.ReactionUsers: 表情表态用户列表
        """
        http = await self._get_http()
        params = {"type": emoji_type, "id": emoji_id, "limit": limit}
        if cookie:
            params["cookie"] = cookie
        data = await http.get(
            f"/channels/{channel_id}/messages/{message_id}/reactions", params=params
        )
        return Model.ReactionUsers.from_dict(data)

    async def create_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji_type: int,
        emoji_id: str,
    ) -> bool:
        """
        机器人发表表情表态

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID
            emoji_type: 表情类型（1 系统表情，2 emoji表情）
            emoji_id: 表情 ID

        Returns:
            bool: 是否操作成功
        """
        http = await self._get_http()
        await http.put(
            f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji_type}/{emoji_id}"
        )
        return True

    async def delete_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji_type: int,
        emoji_id: str,
    ) -> bool:
        """
        删除机器人发表的表情表态

        Args:
            channel_id: 子频道 ID
            message_id: 消息 ID
            emoji_type: 表情类型（1 系统表情，2 emoji表情）
            emoji_id: 表情 ID

        Returns:
            bool: 是否操作成功
        """
        http = await self._get_http()
        await http.delete(
            f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji_type}/{emoji_id}"
        )
        return True

    async def audio_control(
        self,
        channel_id: str,
        audio_url: str | None = None,
        text: str | None = None,
        status: int = 0,
    ) -> bool:
        """
        音频控制

        Args:
            channel_id: 子频道 ID
            audio_url: 音频 URL
            text: 状态文本
            status: 播放状态（0 开始、1 暂停、2 继续、3 停止）

        Returns:
            bool: 是否操作成功
        """
        http = await self._get_http()
        payload = {"status": status}
        if audio_url:
            payload["audio_url"] = audio_url
        if text:
            payload["text"] = text
        await http.post(f"/channels/{channel_id}/audio", json=payload)
        return True

    async def mic_up(self, channel_id: str) -> bool:
        """
        机器人上麦

        Args:
            channel_id: 子频道 ID

        Returns:
            bool: 是否上麦成功
        """
        http = await self._get_http()
        await http.put(f"/channels/{channel_id}/mic")
        return True

    async def mic_down(self, channel_id: str) -> bool:
        """
        机器人下麦

        Args:
            channel_id: 子频道 ID

        Returns:
            bool: 是否下麦成功
        """
        http = await self._get_http()
        await http.delete(f"/channels/{channel_id}/mic")
        return True

    async def get_thread(
        self,
        channel_id: str,
        thread_id: str,
    ) -> Model.ThreadDetail:
        """
        获取帖子详情

        Args:
            channel_id: 子频道 ID
            thread_id: 帖子 ID

        Returns:
            Model.ThreadDetail: 帖子详情对象
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/threads/{thread_id}")
        return Model.ThreadDetail.from_dict(data)

    async def get_threads(
        self,
        channel_id: str,
    ) -> Model.ThreadListResult:
        """
        获取帖子列表

        Args:
            channel_id: 子频道 ID（须为论坛子频道 type=10007）

        Returns:
            Model.ThreadListResult: 帖子列表结果，包含 threads 和 is_finish
        """
        http = await self._get_http()
        data = await http.get(f"/channels/{channel_id}/threads")
        return Model.ThreadListResult.from_dict(data)

    async def create_thread(
        self,
        channel_id: str,
        title: str,
        content: str | Model.ThreadContent,
        format: int | None = None,
    ) -> Model.CreateThreadResponse:
        """
        发表帖子

        Args:
            channel_id: 子频道 ID（须为论坛子频道 type=10007）
            title: 帖子标题
            content: 帖子内容，支持字符串或 ThreadContent 对象
                     - 字符串: 需配合 format 参数指定格式
                     - ThreadContent: 自动使用 JSON 格式(format=4)
            format: 帖子格式（1=纯文本, 2=HTML, 3=Markdown, 4=JSON）
                    当 content 为字符串时默认为 3，为 ThreadContent 时自动设为 4

        Returns:
            Model.CreateThreadResponse: 创建帖子响应，包含 task_id 和 create_time

        使用示例:
            # Markdown 格式发帖
            await api.create_thread(channel_id, "标题", "正文内容")

            # JSON 格式发帖（使用构建器）
            content = (Builders.ThreadContentBuilder()
                .add_text_paragraph("第一段文字")
                .add_image_paragraph("https://example.com/image.png")
                .add_text_paragraph("第二段文字", bold=True)
                .build())
            await api.create_thread(channel_id, "标题", content)
        """
        http = await self._get_http()

        if isinstance(content, Model.ThreadContent):
            content_str = json.dumps(content.to_dict(), ensure_ascii=False)
            format_value = 4
        else:
            content_str = content
            format_value = format if format is not None else 3

        payload = {"title": title, "content": content_str, "format": format_value}
        data = await http.put(f"/channels/{channel_id}/threads", json=payload)
        return Model.CreateThreadResponse.from_dict(data)

    async def delete_thread(
        self,
        channel_id: str,
        thread_id: str,
    ) -> bool:
        """
        删除帖子

        Args:
            channel_id: 子频道 ID
            thread_id: 帖子 ID

        Returns:
            bool: 是否删除成功
        """
        http = await self._get_http()
        await http.delete(f"/channels/{channel_id}/threads/{thread_id}")
        return True

    async def create_thread_comment(
        self,
        channel_id: str,
        thread_id: str,
        thread_author: str,
        content: str,
        thread_create_time: str | None = None,
        image: str | None = None,
    ) -> Model.CreateCommentResponse:
        """
        发表评论

        Args:
            channel_id: 子频道 ID
            thread_id: 帖子 ID
            thread_author: 帖子作者 ID
            content: 评论内容
            thread_create_time: 帖子创建时间
            image: 图片链接

        Returns:
            Model.CreateCommentResponse: 创建评论响应，包含 task_id 和 create_time
        """
        http = await self._get_http()
        payload = {
            "thread_author": thread_author,
            "content": content,
        }
        if thread_create_time:
            payload["thread_create_time"] = thread_create_time
        if image:
            payload["image"] = image
        data = await http.post(
            f"/channels/{channel_id}/threads/{thread_id}/comment", json=payload
        )
        return Model.CreateCommentResponse.from_dict(data)

    async def get_gateway(self) -> Model.GatewayResponse:
        """
        获取通用 WSS 接入点

        Returns:
            Model.GatewayResponse: 包含 url 的响应
        """
        http = await self._get_http()
        data = await http.get("/gateway")
        return Model.GatewayResponse.from_dict(data)

    async def get_gateway_bot(self) -> Model.GatewayBotResponse:
        """
        获取带分片 WSS 接入点

        Returns:
            Model.GatewayBotResponse: 包含 url、shards 和 session_start_limit 的响应
        """
        http = await self._get_http()
        data = await http.get("/gateway/bot")
        return Model.GatewayBotResponse.from_dict(data)

    async def get_guild_message_setting(self, guild_id: str) -> Model.MessageSetting:
        """
        获取频道消息频率设置

        Args:
            guild_id: 频道 ID

        Returns:
            Model.MessageSetting: 消息频率设置对象
        """
        http = await self._get_http()
        data = await http.get(f"/guilds/{guild_id}/message/setting")
        return Model.MessageSetting.from_dict(data)

    async def respond_interaction(
        self,
        interaction_id: str,
        code: int = 0,
    ) -> bool:
        """
        回应互动按钮点击事件

        由于 websocket 推送事件是单向的，开发者收到事件之后，
        需要进行一次"回应"，告知QQ后台事件已经收到。

        Args:
            interaction_id: 互动事件 ID
            code: 回应码
                - 0: 成功
                - 1: 操作失败
                - 2: 操作频繁
                - 3: 重复操作
                - 4: 没有权限
                - 5: 仅管理员操作

        Returns:
            bool: 是否回应成功
        """
        http = await self._get_http()
        payload = {"code": code}
        await http.put(f"/interactions/{interaction_id}", json=payload)
        return True

    async def generate_url_link(
        self,
        callback_data: str | None = None,
    ) -> Model.UrlLinkResponse:
        """
        获取机器人资料页分享链接

        开发者可传入参数，用作追踪该链接后续被用户添加使用机器人的来源归因。

        Args:
            callback_data: 添加好友时会回传该参数给到开发者（最长32字符）

        Returns:
            Model.UrlLinkResponse: 包含 url 字段的响应
        """
        http = await self._get_http()
        payload = {}
        if callback_data:
            payload["callback_data"] = callback_data
        data = await http.post("/v2/generate_url_link", json=payload)
        return Model.UrlLinkResponse.from_dict(data)

    async def upload_media(
        self,
        file_type: int,
        url: str | None = None,
        file_data: bytes | str | None = None,
        srv_send_msg: bool = False,
        user_openid: str | None = None,
        group_openid: str | None = None,
        file_name: str | None = None,
    ) -> Model.FileInfo:
        """
        上传富媒体文件（QQ单聊和QQ群聊通用）

        Args:
            file_type: 媒体类型（1 图片、2 视频、3 语音、4 文件）
            url: 媒体资源 URL
            file_data: 文件数据，支持三种方式：
                       - bytes: 二进制数据
                       - str: 本地文件路径
            srv_send_msg: 是否直接发送消息到目标端，设置为 True 会直接发送消息且占用主动消息频次
            user_openid: 用户 openid（单聊时使用，与 group_openid 二选一）
            group_openid: 群 openid（群聊时使用，与 user_openid 二选一）
            file_name: 文件名（包含扩展名），当 file_type=4（文件）时必填

        Returns:
            Model.FileInfo: 包含 file_uuid、file_info、ttl 字段的响应

        使用示例：
            # 上传图片
            result = await api.upload_media(
                file_type=1,
                file_data="./image.png",
                user_openid="xxx"
            )

            # 上传文件（file_type=4 时必须指定 file_name）
            result = await api.upload_media(
                file_type=4,
                file_data="./document.pdf",
                file_name="document.pdf",  # 必填
                group_openid="group_xxx"
            )

            # 方式二：二进制数据
            with open("image.png", "rb") as f:
                result = await api.upload_media(
                    file_type=1,
                    file_data=f.read(),
                    user_openid="xxx"
                )

            # 方式三：URL
            result = await api.upload_media(
                file_type=1,
                url="https://example.com/image.png",
                user_openid="xxx"
            )

        注意:
            url 和 file_data 必须提供其中之一
            user_openid 和 group_openid 必须提供其中之一，不能同时提供
            当 file_type=4（文件类型）时，file_name 为必填项
        """
        if not url and not file_data:
            raise ValueError("url 和 file_data 必须提供其中之一")

        if user_openid and group_openid:
            raise ValueError("user_openid 和 group_openid 不能同时提供")

        if not user_openid and not group_openid:
            raise ValueError("user_openid 和 group_openid 必须提供其中之一")

        if file_type == 4 and not file_name:
            raise ValueError("file_type=4（文件类型）时，file_name 为必填项")

        http = await self._get_http()
        payload = {"file_type": file_type, "srv_send_msg": srv_send_msg}

        if file_name:
            # 当 file_type=4（文件）时，file_name 必须包含扩展名
            payload["file_name"] = file_name

        payload["url"] = url if url else ""
        if file_data:
            if isinstance(file_data, str):
                path = Path(file_data)
                if not path.exists():
                    raise FileNotFoundError(f"文件不存在: {file_data}")
                file_data = path.read_bytes()
            payload["file_data"] = base64.b64encode(file_data).decode("utf-8")

        if user_openid:
            data = await http.post(f"/v2/users/{user_openid}/files", json=payload)
        else:
            data = await http.post(f"/v2/groups/{group_openid}/files", json=payload)
        return Model.FileInfo.from_dict(data)

    async def send_c2c_stream_message(
        self,
        openid: str,
        content_raw: str,
        event_id: str,
        msg_id: str,
        msg_seq: int,
        index: int,
        input_mode: str = "replace",
        input_state: int = 1,
        content_type: str = "markdown",
        stream_msg_id: str | None = None,
    ) -> Model.StreamMessageResponse:
        """
        发送流式消息（C2C 私聊）

        流式协议：
        - 首次调用时不传 stream_msg_id，由平台返回
        - 后续分片携带 stream_msg_id 和递增 msg_seq
        - input_state=1 表示生成中，10 表示生成结束（终结状态）

        Args:
            openid: 用户 openid
            content_raw: markdown 内容
            event_id: 事件 ID
            msg_id: 原始消息 ID
            msg_seq: 递增序号
            index: 同一条流式会话内的发送索引，从 0 开始，每次发送前递增
            input_mode: 输入模式，默认 "replace"（每次发送的 content_raw 替换整条消息内容）
            input_state: 输入状态，1=正文生成中，10=正文生成结束（终结状态）
            content_type: 内容类型，默认 "markdown"
            stream_msg_id: 流式消息 ID，首次发送后返回，后续分片需携带

        Returns:
            Model.StreamMessageResponse: 流式消息响应

        使用示例：
            # 首次发送（开始流式消息）
            resp = await api.send_c2c_stream_message(
                openid="xxx",
                content_raw="正在生成...",
                event_id="event_xxx",
                msg_id="msg_xxx",
                msg_seq=0,
                index=0,
                input_state=Model.StreamInputState.GENERATING,
            )
            stream_msg_id = resp.id  # 保存后续使用

            # 后续分片
            await api.send_c2c_stream_message(
                openid="xxx",
                content_raw="内容更新...",
                event_id="event_xxx",
                msg_id="msg_xxx",
                msg_seq=1,
                index=1,
                stream_msg_id=stream_msg_id,
                input_state=Model.StreamInputState.GENERATING,
            )

            # 结束流式消息
            await api.send_c2c_stream_message(
                openid="xxx",
                content_raw="最终内容",
                event_id="event_xxx",
                msg_id="msg_xxx",
                msg_seq=2,
                index=2,
                stream_msg_id=stream_msg_id,
                input_state=Model.StreamInputState.DONE,
            )
        """
        http = await self._get_http()
        endpoint = f"/v2/users/{openid}/stream_messages"

        payload = {
            "input_mode": input_mode,
            "input_state": input_state,
            "content_type": content_type,
            "content_raw": content_raw,
            "event_id": event_id,
            "msg_id": msg_id,
            "msg_seq": msg_seq,
            "index": index,
        }

        if stream_msg_id:
            payload["stream_msg_id"] = stream_msg_id

        self._logger.debug(
            f"发送流式消息: openid={openid}, msg_seq={msg_seq}, index={index}, "
            f"input_state={input_state}"
        )

        data = await http.post(endpoint, json=payload)
        response = Model.StreamMessageResponse.from_dict(data)

        self._logger.debug(
            f"流式消息已发送: msg_seq={msg_seq}, "
            f"stream_msg_id={getattr(response, 'id', 'unknown')}"
        )

        return response

    async def upload_prepare(
        self,
        file_type: int,
        file_name: str,
        file_size: int,
        md5: str,
        sha1: str,
        md5_10m: str,
        user_openid: str | None = None,
        group_openid: str | None = None,
    ) -> Model.UploadPrepareResponse:
        """
        申请大文件分片上传（自动识别单聊/群聊）

        Args:
            file_type: 媒体类型（1 图片、2 视频、3 语音、4 文件）
            file_name: 文件名（包含扩展名）
            file_size: 文件大小（字节）
            md5: 文件完整 MD5（十六进制）
            sha1: 文件完整 SHA1（十六进制）
            md5_10m: 文件前 10002432 字节的 MD5（十六进制）；文件不足该大小时为整文件 MD5
            user_openid: 用户 openid（单聊时使用，与 group_openid 二选一）
            group_openid: 群 openid（群聊时使用，与 user_openid 二选一）

        Returns:
            Model.UploadPrepareResponse: 包含 upload_id、block_size 和 parts 的响应

        使用示例：
            import hashlib

            # 读取文件计算哈希
            with open("large_file.mp4", "rb") as f:
                file_data = f.read()
                file_md5 = hashlib.md5(file_data).hexdigest()
                file_sha1 = hashlib.sha1(file_data).hexdigest()
                md5_10m = hashlib.md5(file_data[:10002432]).hexdigest() if len(file_data) >= 10002432 else file_md5

            # 单聊场景
            result = await api.upload_prepare(
                file_type=2,  # 视频
                file_name="large_file.mp4",
                file_size=len(file_data),
                md5=file_md5,
                sha1=file_sha1,
                md5_10m=md5_10m,
                user_openid="user_xxx",
            )

            # 群聊场景
            result = await api.upload_prepare(
                file_type=2,
                file_name="large_file.mp4",
                file_size=len(file_data),
                md5=file_md5,
                sha1=file_sha1,
                md5_10m=md5_10m,
                group_openid="group_xxx",
            )
        """
        if user_openid and group_openid:
            raise ValueError("user_openid 和 group_openid 不能同时提供")

        if not user_openid and not group_openid:
            raise ValueError("user_openid 和 group_openid 必须提供其中之一")

        http = await self._get_http()

        if user_openid:
            endpoint = f"/v2/users/{user_openid}/upload_prepare"
            target_id = user_openid
            target_type = "单聊"
        else:
            endpoint = f"/v2/groups/{group_openid}/upload_prepare"
            target_id = group_openid
            target_type = "群聊"

        payload = {
            "file_type": file_type,
            "file_name": file_name,
            "file_size": file_size,
            "md5": md5,
            "sha1": sha1,
            "md5_10m": md5_10m,
        }

        self._logger.debug(
            f"申请大文件分片上传: target_type={target_type}, target_id={target_id}, "
            f"file_name={file_name}, file_size={file_size}, file_type={file_type}"
        )

        data = await http.post(endpoint, json=payload)
        response = Model.UploadPrepareResponse.from_dict(data)

        self._logger.debug(
            f"分片上传申请成功: upload_id={response.upload_id}, "
            f"block_size={response.block_size}, parts_count={len(response.parts)}"
        )

        return response

    async def upload_part(
        self,
        presigned_url: str,
        part_data: bytes,
        upload_id: str,
        part_index: int,
        user_openid: str | None = None,
        group_openid: str | None = None,
        retry_timeout: int | None = None,
    ) -> bool:
        """
        上传单个分片（自动识别单聊/群聊）

        这是一个高级封装方法，自动完成：
        1. 计算分片 MD5
        2. PUT 到预签名 URL（对象存储）
        3. 通知平台分片完成

        Args:
            presigned_url: 预签名上传链接（来自 upload_prepare 返回的 parts）
            part_data: 分片数据（字节）
            upload_id: 上传任务 ID（来自 upload_prepare）
            part_index: 分片索引（从 1 开始）
            user_openid: 用户 openid（单聊时使用，与 group_openid 二选一）
            group_openid: 群 openid（群聊时使用，与 user_openid 二选一）
            retry_timeout: 重试超时时间（秒），当返回错误码 40093001 时持续重试

        Returns:
            bool: 是否上传成功

        使用示例：
            # 读取分片数据
            with open("large_file.mp4", "rb") as f:
                f.seek(offset)
                chunk_data = f.read(block_size)

            # 单聊场景 - 一行代码完成分片上传
            await api.upload_part(
                presigned_url=presigned_url,
                part_data=chunk_data,
                upload_id=upload_id,
                part_index=1,
                user_openid="user_xxx",
            )

            # 群聊场景
            await api.upload_part(
                presigned_url=presigned_url,
                part_data=chunk_data,
                upload_id=upload_id,
                part_index=1,
                group_openid="group_xxx",
            )
        """
        # 1. 计算分片 MD5
        chunk_md5 = hashlib.md5(part_data).hexdigest()

        self._logger.debug(
            f"开始上传分片: part_index={part_index}, size={len(part_data)}, md5={chunk_md5}"
        )

        # 2. PUT 到预签名 URL
        # 对象存储需要正确的 Content-Type，二进制数据使用 application/octet-stream
        headers = {"Content-Type": "application/octet-stream"}
        async with aiohttp.ClientSession(trust_env=False) as session:
            async with session.put(
                presigned_url, headers=headers, data=part_data
            ) as resp:
                resp.raise_for_status()

        self._logger.debug(f"分片已上传到对象存储: part_index={part_index}")

        # 3. 通知平台分片完成
        return await self.upload_part_finish(
            upload_id=upload_id,
            part_index=part_index,
            block_size=len(part_data),
            md5=chunk_md5,
            user_openid=user_openid,
            group_openid=group_openid,
            retry_timeout=retry_timeout,
        )

    async def upload_part_finish(
        self,
        upload_id: str,
        part_index: int,
        block_size: int,
        md5: str,
        user_openid: str | None = None,
        group_openid: str | None = None,
        retry_timeout: int | None = None,
    ) -> bool:
        """
        完成分片上传（自动识别单聊/群聊）

        每个分片上传到对象存储后，需要调用此接口通知平台。

        Args:
            upload_id: 上传任务 ID（来自 upload_prepare）
            part_index: 分片索引（从 1 开始）
            block_size: 本分片大小（字节）
            md5: 本分片数据的 MD5（十六进制）
            user_openid: 用户 openid（单聊时使用，与 group_openid 二选一）
            group_openid: 群 openid（群聊时使用，与 user_openid 二选一）
            retry_timeout: 重试超时时间（秒），当返回错误码 40093001 时持续重试

        Returns:
            bool: 是否完成成功

        Raises:
            APIError: 当返回错误码 40093001 时需要持续重试

        使用示例：
            # 上传分片到对象存储
            chunk_data = file_data[offset:offset + block_size]
            chunk_md5 = hashlib.md5(chunk_data).hexdigest()

            # PUT 到预签名 URL
            async with aiohttp.ClientSession() as session:
                async with session.put(presigned_url, data=chunk_data) as resp:
                    resp.raise_for_status()

            # 单聊场景
            await api.upload_part_finish(
                upload_id=upload_id,
                part_index=part_index,
                block_size=len(chunk_data),
                md5=chunk_md5,
                user_openid="user_xxx",
            )

            # 群聊场景
            await api.upload_part_finish(
                upload_id=upload_id,
                part_index=part_index,
                block_size=len(chunk_data),
                md5=chunk_md5,
                group_openid="group_xxx",
            )
        """
        if user_openid and group_openid:
            raise ValueError("user_openid 和 group_openid 不能同时提供")

        if not user_openid and not group_openid:
            raise ValueError("user_openid 和 group_openid 必须提供其中之一")

        http = await self._get_http()

        if user_openid:
            endpoint = f"/v2/users/{user_openid}/upload_part_finish"
            target_type = "单聊"
        else:
            endpoint = f"/v2/groups/{group_openid}/upload_part_finish"
            target_type = "群聊"

        payload = {
            "upload_id": upload_id,
            "part_index": part_index,
            "block_size": block_size,
            "md5": md5,
        }

        max_retries = retry_timeout if retry_timeout else 60
        retry_count = 0

        while retry_count < max_retries:
            try:
                await http.post(endpoint, json=payload)
                self._logger.debug(
                    f"分片完成通知成功: target_type={target_type}, upload_id={upload_id}, "
                    f"part_index={part_index}"
                )
                return True
            except APIError as e:
                if e.code == 40093001:
                    retry_count += 1
                    self._logger.warning(
                        f"分片上传处理中，等待重试: upload_id={upload_id}, "
                        f"part_index={part_index}, retry={retry_count}/{max_retries}"
                    )
                    await asyncio.sleep(1)
                else:
                    raise
            except Exception:
                raise

        raise Exception(f"分片上传超时: upload_id={upload_id}, part_index={part_index}")

    async def upload_complete(
        self,
        upload_id: str,
        user_openid: str | None = None,
        group_openid: str | None = None,
    ) -> Model.FileInfo:
        """
        完成大文件上传（自动识别单聊/群聊）

        所有分片上传完成后，调用此接口获取 file_info。

        Args:
            upload_id: 上传任务 ID（来自 upload_prepare）
            user_openid: 用户 openid（单聊时使用，与 group_openid 二选一）
            group_openid: 群 openid（群聊时使用，与 user_openid 二选一）

        Returns:
            Model.FileInfo: 包含 file_uuid、file_info、ttl 字段的响应

        使用示例：
            # 单聊场景
            result = await api.upload_complete(
                upload_id=upload_id,
                user_openid="user_xxx",
            )

            # 使用 file_info 发送消息
            await api.send_c2c_message(
                openid="user_xxx",
                content="文件已上传",
                media_file_info=result.file_info,
            )

            # 群聊场景
            result = await api.upload_complete(
                upload_id=upload_id,
                group_openid="group_xxx",
            )

            # 使用 file_info 发送消息
            await api.send_group_message(
                group_openid="group_xxx",
                content="文件已上传",
                media_file_info=result.file_info,
            )
        """
        if user_openid and group_openid:
            raise ValueError("user_openid 和 group_openid 不能同时提供")

        if not user_openid and not group_openid:
            raise ValueError("user_openid 和 group_openid 必须提供其中之一")

        http = await self._get_http()

        if user_openid:
            endpoint = f"/v2/users/{user_openid}/files"
            target_id = user_openid
            target_type = "单聊"
        else:
            endpoint = f"/v2/groups/{group_openid}/files"
            target_id = group_openid
            target_type = "群聊"

        payload = {"upload_id": upload_id}

        self._logger.debug(
            f"完成大文件上传: target_type={target_type}, target_id={target_id}, "
            f"upload_id={upload_id}"
        )

        data = await http.post(endpoint, json=payload)
        response = Model.FileInfo.from_dict(data)

        self._logger.debug(
            f"大文件上传完成: upload_id={upload_id}, "
            f"file_uuid={response.file_uuid}, ttl={response.ttl}"
        )

        return response

    async def upload_large_file(
        self,
        file_path: str,
        file_type: int,
        user_openid: str | None = None,
        group_openid: str | None = None,
        concurrency: int | None = None,
    ) -> Model.FileInfo:
        """
        上传大文件（自动分片）

        这是一个高级封装方法，自动处理整个分片上传流程：
        1. 计算文件哈希值
        2. 申请上传
        3. 并行上传分片到对象存储
        4. 通知平台分片完成
        5. 完成上传

        Args:
            file_path: 本地文件路径
            file_type: 媒体类型（1 图片、2 视频、3 语音、4 文件）
            user_openid: 用户 openid（单聊时使用，与 group_openid 二选一）
            group_openid: 群 openid（群聊时使用，与 user_openid 二选一）
            concurrency: 并发上传数，不指定时使用 API 返回的建议值

        Returns:
            Model.FileInfo: 包含 file_uuid、file_info、ttl 字段的响应

        使用示例：
            # 上传大文件到单聊
            result = await api.upload_large_file(
                file_path="./large_video.mp4",
                file_type=2,  # 视频
                user_openid="user_xxx",
            )

            # 使用 file_info 发送消息
            await api.send_c2c_message(
                openid="user_xxx",
                content="大文件已上传",
                media_file_info=result.file_info,
            )

            # 上传大文件到群聊
            result = await api.upload_large_file(
                file_path="./document.pdf",
                file_type=4,  # 文件
                group_openid="group_xxx",
            )

        注意:
            - user_openid 和 group_openid 必须提供其中之一，不能同时提供
            - 建议对大文件（>10MB）使用此方法，小文件可使用 upload_media
        """
        if user_openid and group_openid:
            raise ValueError("user_openid 和 group_openid 不能同时提供")

        if not user_openid and not group_openid:
            raise ValueError("user_openid 和 group_openid 必须提供其中之一")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_name = path.name
        file_size = path.stat().st_size

        self._logger.info(
            f"开始上传大文件: file_name={file_name}, file_size={file_size}, "
            f"file_type={file_type}"
        )

        # 1. 计算文件哈希值
        self._logger.debug("计算文件哈希值...")

        file_md5 = hashlib.md5()
        file_sha1 = hashlib.sha1()
        md5_10m = hashlib.md5()
        md5_10m_size = 10002432
        md5_10m_calculated = False

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                file_md5.update(chunk)
                file_sha1.update(chunk)
                if not md5_10m_calculated:
                    md5_10m.update(chunk)
                    if f.tell() >= md5_10m_size:
                        md5_10m_calculated = True

        file_md5_hex = file_md5.hexdigest()
        file_sha1_hex = file_sha1.hexdigest()
        md5_10m_hex = md5_10m.hexdigest()

        self._logger.debug(
            f"文件哈希计算完成: md5={file_md5_hex}, sha1={file_sha1_hex}"
        )

        # 2. 申请上传
        prepare_response = await self.upload_prepare(
            file_type=file_type,
            file_name=file_name,
            file_size=file_size,
            md5=file_md5_hex,
            sha1=file_sha1_hex,
            md5_10m=md5_10m_hex,
            user_openid=user_openid,
            group_openid=group_openid,
        )

        upload_id = prepare_response.upload_id
        block_size = prepare_response.block_size
        parts = prepare_response.parts
        max_concurrency = concurrency or prepare_response.concurrency or 3
        retry_timeout = prepare_response.retry_timeout

        self._logger.info(
            f"分片上传申请成功: upload_id={upload_id}, "
            f"block_size={block_size}, parts_count={len(parts)}, "
            f"concurrency={max_concurrency}"
        )

        # 3. 并行上传分片
        async def upload_single_part(part: Model.UploadPart) -> bool:
            """上传单个分片"""
            part_index = part.index
            presigned_url = part.presigned_url

            # 读取分片数据
            offset = (part_index - 1) * block_size
            with open(file_path, "rb") as f:
                f.seek(offset)
                chunk_data = f.read(block_size)

            # 使用封装好的 upload_part 方法
            return await self.upload_part(
                presigned_url=presigned_url,
                part_data=chunk_data,
                upload_id=upload_id,
                part_index=part_index,
                user_openid=user_openid,
                group_openid=group_openid,
                retry_timeout=retry_timeout,
            )

        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(max_concurrency)

        async def upload_part_with_semaphore(part: Model.UploadPart) -> bool:
            """带信号量控制的分片上传"""
            async with semaphore:
                self._logger.debug(
                    f"开始上传分片: part_index={part.index}/{len(parts)}"
                )
                result = await upload_single_part(part)
                self._logger.debug(
                    f"分片上传完成: part_index={part.index}/{len(parts)}"
                )
                return result

        # 并行上传所有分片
        self._logger.info(
            f"开始并行上传分片: parts_count={len(parts)}, "
            f"concurrency={max_concurrency}"
        )

        upload_tasks = [upload_part_with_semaphore(part) for part in parts]
        await asyncio.gather(*upload_tasks)

        self._logger.info("所有分片上传完成")

        # 4. 完成上传
        result = await self.upload_complete(
            upload_id=upload_id,
            user_openid=user_openid,
            group_openid=group_openid,
        )

        self._logger.info(
            f"大文件上传完成: file_uuid={result.file_uuid}, ttl={result.ttl}"
        )

        return result
