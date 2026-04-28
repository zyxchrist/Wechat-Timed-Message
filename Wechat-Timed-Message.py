import os
import requests
import sys
import subprocess

# 自动安装 feedparser（如果没有的话）
try:
    import feedparser
except ImportError:
    print("正在自动安装 feedparser...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "feedparser"])
    import feedparser

# 直接使用人民日报官方 RSS 地址，不需要环境变量
RSS_URL = "http://www.people.com.cn/rss/politics.xml"
PUSHPLUS_API_URL = "http://www.pushplus.plus/send"

pp_token = os.getenv('PPTOKEN')

print("=== 开始抓取人民日报 RSS 头条 ===")
if not pp_token:
    print("❌ 错误：未获取到 PPTOKEN，请检查 Secrets 设置")
    sys.exit(1)

def get_rss_headline():
    try:
        feed = feedparser.parse(RSS_URL)
        if feed.entries:
            first = feed.entries[0]
            title = first.title
            link = first.link
            print(f"✅ 抓取成功：{title}")
            return title, link
        else:
            print("❌ RSS 订阅中没有条目")
            return None, None
    except Exception as e:
        print(f"❌ 抓取异常：{e}")
        return None, None

def send_to_wechat(title, content):
    print(f"准备发送消息：{title}")
    payload = {
        "token": pp_token,
        "title": title,
        "content": content
    }
    try:
        resp = requests.post(PUSHPLUS_API_URL, json=payload, timeout=10)
        result = resp.json()
        print(f"PushPlus 返回码：{result.get('code')}")
        if result.get('code') == 200:
            print("✅ 消息已成功推送到微信")
        else:
            print(f"❌ 推送失败：{result.get('msg')}")
    except Exception as e:
        print(f"❌ 请求异常：{e}")

if __name__ == "__main__":
    title, link = get_rss_headline()
    if title and link:
        send_to_wechat("📰 人民日报今日头条", f"{title}\n{link}")
    else:
        send_to_wechat("⚠️ 抓取失败", "未能从人民日报 RSS 获取头条，请检查网络或 RSS 地址")
