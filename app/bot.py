# bot.py

import logging
import asyncio
import websockets
from config import *


from datetime import datetime
from dingtalk import dingtalk


from handler_events import handle_message

from api import send_group_msg


async def connect_to_bot():
    logging.info("正在连接到机器人...")
    logging.info(f"连接地址: {ws_url}")

    # 如果 token 不为 None，则添加到请求头
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        async with websockets.connect(ws_url, extra_headers=headers) as websocket:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logging.info(f"已连接到机器人。当前时间: {current_time}")
            await send_group_msg(
                websocket, report_group_id, f"机器人已连接。当前时间: {current_time}"
            )
            async for message in websocket:
                # 处理ws消息
                asyncio.create_task(handle_message(websocket, message))
    else:
        async with websockets.connect(ws_url) as websocket:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logging.info(f"已连接到机器人。当前时间: {current_time}")
            await send_group_msg(
                websocket, report_group_id, f"机器人已连接。当前时间: {current_time}"
            )
            async for message in websocket:
                # 处理ws消息
                asyncio.create_task(handle_message(websocket, message))


if __name__ == "__main__":
    asyncio.run(connect_to_bot())
