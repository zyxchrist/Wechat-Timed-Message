import os
import requests
import sys
import subprocess
import ssl

# 自动安装 feedparser
try:
    import feedparser
except ImportError:
    print("正在自动安装 feedparser...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "feedparser"])
    import feedparser

# ===== 使用你指定的聚合热门源 =====
RSS_URL = "https://news.aolifu.org/c/hottest"

# 可选：如果你以后需要切换其他源，直接改上面这一行即可
# 例如：RSS_URL = "https://hot.uihash.com"
# 或者：RSS_URL = "https://rsshub.app/news/all"

PUSHPLUS_API_URL = "http://www.pushplus.plus/send"
NEWS_COUNT = 10   # 获取新闻条数

pp_token = os.getenv('PPTOKEN')

print("=== 开始抓取聚合热门新闻 (news.aolifu.org) ===")
if not pp_token:
    print("❌ 错误：未获取到 PPTOKEN")
    sys.exit(1)

# 故障排查：禁用SSL证书验证（解决某些站点的证书问题）
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

def clean_html(raw_html):
    """移除HTML标签，提取纯文本"""
    import re
    clean = re.compile(r'<[^>]+>').sub('', raw_html)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def get_rss_news(limit=10):
    try:
        # 故障排查：模拟浏览器 User-Agent，防止被屏蔽
        feed = feedparser.parse(RSS_URL, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        if not feed.entries:
            print("❌ RSS 订阅中没有条目")
            return []
        
        news_list = []
        for i, entry in enumerate(feed.entries[:limit], 1):
            title = entry.title
            # 获取摘要
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
    # 微信单条消息字符限制，预留空间
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
        send_to_wechat("⚠️ 抓取失败", f"未能从 {RSS_URL} 获取新闻，请检查地址或网络。")
