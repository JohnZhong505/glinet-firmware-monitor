import requests
import re
import json
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup

WEBHOOK = os.getenv("DINGTALK_WEBHOOK")

# 所有型号网页列表
URLS = [
    "https://dl.gl-inet.com/router/mt3000/beta",
    "https://dl.gl-inet.com/router/mt3000/stable",
    "https://dl.gl-inet.com/router/mt6000/beta",
    "https://dl.gl-inet.com/router/mt6000/stable",
    "https://dl.gl-inet.com/router/mt2500/beta",
    "https://dl.gl-inet.com/router/x3000/beta",
    "https://dl.gl-inet.com/router/axt1800/beta",
    "https://dl.gl-inet.com/router/axt1800/stable"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

VERSIONS_FILE = "versions.json"

# 加载上次记录
def load_versions():
    if not os.path.exists(VERSIONS_FILE):
        return {}
    with open(VERSIONS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    return data

# 保存最新版本
def save_versions(data):
    with open(VERSIONS_FILE,"w", encoding="utf-8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)

# 获取网页内容
def get_page(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.text

# 获取最新版本号
def get_latest_version(url):
    html = get_page(url)
    files = re.findall(r'glinet.*?\.bin', html)
    versions = re.findall(r"\d+\.\d+\.\d+", str(files))
    if not versions:
        return None
    return sorted(versions, key=lambda x: [int(i) for i in x.split('.')])[-1]

# 获取 Release Note
def get_release_note(url, version):
    html = get_page(url)
    soup = BeautifulSoup(html, "html.parser")
    note = ""
    links = soup.find_all("a")
    for a in links:
        if version in a.text:
            href = a.get("href")
            if href:
                page2 = get_page(url + href)
                soup2 = BeautifulSoup(page2, "html.parser")
                pre = soup2.find("pre")
                if pre:
                    note = pre.get_text(strip=True)
                break
    return note if note else "无 Release Note 内容"

# 发送钉钉
def send_dingtalk(msg):
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "GL.iNet 固件更新",
            "text": msg
        }
    }
    requests.post(WEBHOOK,json=data)

# 主逻辑
def main():
    versions = load_versions()
    new_updates = []

    for url in URLS:
        # 从 URL 提取型号和渠道
        parts = url.strip("/").split("/")
        model = parts[-2]
        channel = parts[-1]

        latest = get_latest_version(url)
        if not latest:
            continue

        key = f"{model}_{channel}"
        old = versions.get(key)
        if old != latest:
            note = get_release_note(url, latest)
            new_updates.append((model, channel, old, latest, note))
            versions[key] = latest

    save_versions(versions)

    if new_updates:
        msg = "### GL.iNet 固件更新\n\n"
        for model, channel, old, new, note in new_updates:
            msg += f"**设备**: {model}\n**渠道**: {channel}\n**旧版本**: {old}\n**新版本**: {new}\n**Release Note**:\n{note}\n\n"
        send_dingtalk(msg)
    else:
        # 周五下午 17:00 (北京时间)
        now = datetime.now()
        if now.weekday() == 4 and now.hour >= 17:
            msg = f"### GL.iNet 固件监控\n\n本周没有发现新的固件更新\n监控系统运行正常\n时间: {now.strftime('%Y-%m-%d')}"
            send_dingtalk(msg)

if __name__ == "__main__":
    main()