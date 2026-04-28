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

# 配置
RSS_URL = "http://www.people.com.cn/rss/politics.xml"
PUSHPLUS_API_URL = "http://www.pushplus.plus/send"
NEWS_COUNT = 10  # 你想要获取的条数（可改为5、8、10等）

pp_token = os.getenv('PPTOKEN')

print("=== 开始抓取人民日报 RSS 多条新闻（含简介）===")
if not pp_token:
    print("❌ 错误：未获取到 PPTOKEN")
    sys.exit(1)

def clean_html(raw_html):
    """去除字符串中的HTML标签，提取纯文本"""
    import re
    # 移除 <...> 标签
    clean = re.compile(r'<[^>]+>').sub('', raw_html)
    # 移除多余空白字符
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def get_rss_news(limit=10):
    """获取前 limit 条新闻，返回列表 [(标题, 简介), ...]"""
    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries:
            print("❌ RSS 订阅中没有条目")
            return []
        
        news_list = []
        for i, entry in enumerate(feed.entries[:limit], 1):
            title = entry.title
            # 获取摘要，如果不存在则使用描述，最后用空字符串
            summary = entry.get('summary', '')
            if not summary:
                summary = entry.get('description', '暂无简介')
            # 去除HTML标签，保留纯文本
            summary_clean = clean_html(summary)
            # 限制摘要长度（可选，微信消息有2000字符限制，10条摘要不会超）
            if len(summary_clean) > 150:
                summary_clean = summary_clean[:150] + '…'
            news_list.append((title, summary_clean))
            print(f"  第{i}条: {title[:30]}...")
        print(f"✅ 成功获取 {len(news_list)} 条新闻")
        return news_list
    except Exception as e:
        print(f"❌ 抓取异常：{e}")
        return []

def format_news_message(news_list):
    """格式化成消息文本：标题 + 简介（无链接）"""
    if not news_list:
        return "今日未获取到新闻。"
    
    lines = []
    for i, (title, summary) in enumerate(news_list, 1):
        lines.append(f"{i}. {title}")
        lines.append(f"   {summary}")
        lines.append("")  # 空行分隔
    return "\n".join(lines).strip()

def send_to_wechat(title, content):
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
        send_to_wechat(f"📰 人民日报今日头条（共{NEWS_COUNT}条）", content)
    else:
        send_to_wechat("⚠️ 抓取失败", "未能获取新闻，请检查RSS")
