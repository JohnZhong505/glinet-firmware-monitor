import requests
import re
import json
import os
from datetime import datetime

BASE_URL = "https://dl.gl-inet.com/router/"
WEBHOOK = os.getenv("DINGTALK_WEBHOOK")

headers = {
    "User-Agent": "Mozilla/5.0"
}

def get_models():
    r = requests.get(BASE_URL, headers=headers)
    models = re.findall(r'href="([a-z0-9-]+)/"', r.text)
    return list(set(models))

def get_channels(model):
    url = f"{BASE_URL}{model}/"
    r = requests.get(url, headers=headers)
    channels = re.findall(r'href="(beta|stable)/"', r.text)
    return list(set(channels))

def get_latest_version(model, channel):
    url = f"{BASE_URL}{model}/{channel}/"
    r = requests.get(url, headers=headers)

    files = re.findall(r'glinet.*?\.bin', r.text)
    versions = re.findall(r"\d+\.\d+\.\d+", str(files))

    if not versions:
        return None

    return sorted(versions)[-1]

def load_versions():
    if not os.path.exists("versions.json"):
        return {}
    with open("versions.json") as f:
        return json.load(f)

def save_versions(data):
    with open("versions.json","w") as f:
        json.dump(data,f,indent=2)

def send_dingtalk(msg):

    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "GL.iNet Firmware Update",
            "text": msg
        }
    }

    requests.post(WEBHOOK,json=data)

def main():

    versions = load_versions()
    new_updates = []

    models = get_models()

    for model in models:

        channels = get_channels(model)

        for channel in channels:

            latest = get_latest_version(model,channel)

            if not latest:
                continue

            key = f"{model}_{channel}"

            old = versions.get(key)

            if old != latest:

                new_updates.append((model,channel,old,latest))

                versions[key] = latest

    save_versions(versions)

    if new_updates:

        msg = "### GL.iNet 固件更新\n\n"

        for model,channel,old,new in new_updates:

            msg += f"""
**设备**: {model}  
**渠道**: {channel}  
**旧版本**: {old}  
**新版本**: {new}  

"""

        send_dingtalk(msg)

    else:

        today = datetime.now()

        if today.weekday() == 4 and today.hour >= 9:

            msg = f"""
### GL.iNet 固件监控

本周没有发现新的固件更新  

监控系统运行正常  
时间: {today.strftime("%Y-%m-%d")}
"""

            send_dingtalk(msg)

if __name__ == "__main__":
    main()