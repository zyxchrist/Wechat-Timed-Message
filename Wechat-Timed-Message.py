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

# ===== 新华网 RSS 地址（要闻综合）=====
RSS_URL = "http://www.xinhuanet.com/rss/news.xml"
# 备选：如果你想要其他频道，可以换成下面任意一个（去掉行首的#）
# RSS_URL = "http://www.xinhuanet.com/rss/politics.xml"   # 政治
# RSS_URL = "http://www.xinhuanet.com/rss/world.xml"      # 国际
# RSS_URL = "http://www.xinhuanet.com/rss/mil.xml"        # 军事
# RSS_URL = "http://www.xinhuanet.com/rss/finance.xml"    # 财经
# RSS_URL = "http://www.xinhuanet.com/rss/sports.xml"     # 体育

PUSHPLUS_API_URL = "http://www.pushplus.plus/send"
NEWS_COUNT = 10   # 你想获取的新闻条数

pp_token = os.getenv('PPTOKEN')

print("=== 开始抓取新华网 RSS 新闻 ===")
if not pp_token:
    print("❌ 错误：未获取到 PPTOKEN")
    sys.exit(1)

def clean_html(raw_html):
    """移除HTML标签，提取纯文本"""
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
            # 新华网的 RSS 通常有 summary 或 description
            summary = entry.get('summary', '')
            if not summary:
                summary = entry.get('description', '暂无简介')
            summary_clean = clean_html(summary)
            # 限制摘要长度，避免消息过长
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
    """将新闻列表格式化为带标题和简介的文本"""
    if not news_list:
        return "今日未获取到新闻。"
    lines = []
    for i, (title, summary) in enumerate(news_list, 1):
        lines.append(f"{i}. {title}")
        lines.append(f"   {summary}")
        lines.append("")  # 空行分隔
    return "\n".join(lines).strip()

def send_to_wechat(title, content):
    if len(content) > 1900:   # 微信单条消息限制约2000字符，预留一点
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
        send_to_wechat(f"📰 新华网今日要闻（共{NEWS_COUNT}条）", content)
    else:
        send_to_wechat("⚠️ 抓取失败", "未能从新华网 RSS 获取新闻，请检查地址")
