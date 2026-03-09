import os
import requests

WEBHOOK = os.getenv("DINGTALK_WEBHOOK")
print(f"Webhook: {WEBHOOK}")  # 确认打印出来是你配置的 URL

data = {
    "msgtype": "text",
    "text": {"content": "固件测试消息，确认钉钉机器人能收到"}
}

resp = requests.post(WEBHOOK, json=data, timeout=10)
print(resp.status_code, resp.text)