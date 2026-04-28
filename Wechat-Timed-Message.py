import os
import requests
import sys
import subprocess

# 自动安装 feedparser
try:
    import feedparser
except ImportError:
    print("正在自动安装 feedparser...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "feedparser"])
    import feedparser

# ===== 使用 RSSHub 聚合源（稳定可靠）=====
RSS_URL = "https://rsshub.app/news/all"

PUSHPLUS_API_URL = "http://www.pushplus.plus/send"
NEWS_COUNT = 10

pp_token = os.getenv('PPTOKEN')

print("=== 开始抓取 RSSHub 聚合新闻 ===")
if not pp_token:
    print("❌ 错误：未获取到 PPTOKEN")
    sys.exit(1)

def clean_html(raw_html):
    import re
    clean = re.compile(r'<[^>]+>').sub('', raw_html)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def get_rss_news(limit=10):
    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries:
            print("❌ RSS 订阅中没有条目")
            return []
        
        news_list = []
        for i, entry in enumerate(feed.entries[:limit], 1):
            title = entry.title
            summary = entry.get('summary', '')
            if not summary:
                summary = entry.get('description', '暂无简介')
            summary_clean = clean_html(summary)
            if len(summary_clean) > 200:
                summary_clean = summary_clean[:200] + '…'
            news_list.append((title, summary_clean))
            print(f"  第{i}条: {title[:30]}...")
        print(f"✅ 成功获取 {len(news_list)} 条新闻")
        return news_list
    except Exception as e:
        print(f"❌ 抓取异常：{e}")
        return []

def format_news_message(news_list):
    if not news_list:
        return "今日未获取到新闻。"
    lines = []
    for i, (title, summary) in enumerate(news_list, 1):
        lines.append(f"{i}. {title}")
        lines.append(f"   {summary}")
        lines.append("")
    return "\n".join(lines).strip()

def send_to_wechat(title, content):
    if len(content) > 1900:
        content = content[:1900] + "…\n(内容过长，已截断)"
    print(f"准备发送消息：{title}")
    payload = {"token": pp_token, "title": title, "content": content}
    try:
        resp = requests.post(PUSHPLUS_API_URL, json=payload, timeout=10)
        result = resp.json()
        print(f"PushPlus 返回码：{result.get('code')}")
        if result.get('code') == 200:
            print("✅ 消息已推送")
        else:
            print(f"❌ 推送失败：{result.get('msg')}")
    except Exception as e:
        print(f"❌ 请求异常：{e}")

if __name__ == "__main__":
    news = get_rss_news(NEWS_COUNT)
    if news:
        content = format_news_message(news)
        send_to_wechat(f"📰 今日热点新闻（共{NEWS_COUNT}条）", content)
    else:
        send_to_wechat("⚠️ 抓取失败", "未能从 RSS 获取新闻，请检查地址")
