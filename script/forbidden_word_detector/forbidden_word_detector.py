import json
import logging
import asyncio
import websockets
import re

# 配置
ws_url = "ws://127.0.0.1:3001"  # napcatQQ 的 WebSocket API 地址
token = None  # 如果需要认证，请填写认证 token
forbidden_words_file = "forbidden_words.txt"  # 违禁词文件路径
warning_message = "警告：请不要发送违禁词！"
enabled_groups = [728077087, 236562801, 781550983]  # 需要开启检测功能的群聊群号
owner = 2769731875  # 机器人管理员 QQ 号

logging.basicConfig(level=logging.DEBUG)


def load_forbidden_words(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        patterns = [line.strip() for line in file if line.strip()]
    return patterns


async def connect_to_bot():
    logging.info("Connecting to bot...")
    async with websockets.connect(ws_url) as websocket:
        logging.info("Connected to bot.")
        # 发送认证信息，如果需要的话
        await authenticate(websocket)

        async for message in websocket:
            logging.debug(f"Received message: {message}")
            await handle_message(websocket, message)


async def authenticate(websocket):
    if token:
        auth_message = {"action": "authenticate", "params": {"token": token}}
        await websocket.send(json.dumps(auth_message))
        logging.info("Sent authentication message.")
    else:
        logging.info("No token provided, skipping authentication.")


async def handle_message(websocket, message):
    msg = json.loads(message)

    # 检查消息类型和内容
    if msg.get("post_type") == "message" and msg.get("message_type") == "group":
        logging.debug(f"Handling group message: {msg}")
        user_id = msg["user_id"]
        group_id = msg["group_id"]
        message_id = msg["message_id"]
        raw_message = msg.get("raw_message", "")

        # 检查群号是否在启用列表中
        if group_id in enabled_groups:
            logging.debug(f"Group {group_id} is enabled for forbidden word detection.")
            # 检测违禁词
            if any(re.search(pattern, raw_message) for pattern in forbidden_patterns):
                logging.debug(f"Forbidden word detected in message: {raw_message}")

                await set_group_ban(websocket, group_id, user_id, 60 * 5)

                # 撤回消息
                await delete_message(websocket, message_id)

                warning_message = f"警告：群 {group_id} 的用户 {user_id} 发送的消息包含违禁词！请注意言行！"

                # 发送警告消息
                await send_message(websocket, group_id, warning_message)
        else:
            logging.debug(
                f"Group {group_id} is not enabled for forbidden word detection."
            )


async def set_group_ban(websocket, group_id, user_id, duration):
    ban_msg = {
        "action": "set_group_ban",
        "params": {"group_id": group_id, "user_id": user_id, "duration": duration},
    }
    await websocket.send(json.dumps(ban_msg))
    logging.info(f"User {user_id} banned from group {group_id} for {duration} seconds.")


async def delete_message(websocket, message_id):
    delete_msg = {
        "action": "delete_msg",
        "params": {"message_id": message_id},
    }
    await websocket.send(json.dumps(delete_msg))
    logging.info(f"Message {message_id} deleted.")


async def send_message(websocket, group_id, content):
    message = {
        "action": "send_group_msg",
        "params": {"group_id": group_id, "message": content},
    }
    await websocket.send(json.dumps(message))
    logging.info(f"Message sent to group {group_id}: {content}")


# 主函数
if __name__ == "__main__":
    forbidden_patterns = load_forbidden_words(forbidden_words_file)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect_to_bot())
