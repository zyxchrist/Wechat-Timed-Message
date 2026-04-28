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

# 配置
RSS_URL = "http://www.people.com.cn/rss/politics.xml"
PUSHPLUS_API_URL = "http://www.pushplus.plus/send"
NEWS_COUNT = 10  # 你想要获取的头条新闻条数（可改为3、5、10等）

pp_token = os.getenv('PPTOKEN')

print("=== 开始抓取人民日报 RSS 多条新闻 ===")
if not pp_token:
    print("❌ 错误：未获取到 PPTOKEN，请检查 Secrets 设置")
    sys.exit(1)

def get_rss_news(limit=5):
    """获取 RSS 前 limit 条新闻，返回列表，每个元素是 (标题, 链接)"""
    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries:
            print("❌ RSS 订阅中没有条目")
            return []
        
        news_list = []
        for i, entry in enumerate(feed.entries[:limit], 1):
            title = entry.title
            link = entry.link
            news_list.append((title, link))
            print(f"  第{i}条: {title}")
        
        print(f"✅ 成功获取 {len(news_list)} 条新闻")
        return news_list
    except Exception as e:
        print(f"❌ 抓取异常：{e}")
        return []

def format_news_message(news_list):
    """将新闻列表格式化成一条消息文本"""
    if not news_list:
        return "今日未获取到新闻，请稍后检查。"
    
    lines = []
    for i, (title, link) in enumerate(news_list, 1):
        lines.append(f"{i}. {title}\n   {link}")
    return "\n\n".join(lines)

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
    news = get_rss_news(NEWS_COUNT)
    if news:
        content = format_news_message(news)
        send_to_wechat(f"📰 人民日报今日头条（共{NEWS_COUNT}条）", content)
    else:
        send_to_wechat("⚠️ 抓取失败", "未能从人民日报 RSS 获取新闻，请检查网络或 RSS 地址")
