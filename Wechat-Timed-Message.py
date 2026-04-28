import os
import re
import requests
from datetime import datetime

# 从环境变量中读取我们在 Secrets 里设置的网址
url = os.getenv('URL')

def get_people_daily_headline():
    try:
        # 模拟浏览器访问，防止被拦截
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        
        # 在网页源码中抓取第一个 <a> 标签里的链接和文字
        # 人民日报首页的第一个 <a> 通常就是头条新闻
        match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', resp.text)
        if match:
            link = match.group(1)
            title = match.group(2).strip()
            # 如果链接是相对路径（比如 /abc.html），补全成完整网址
            if link.startswith('/'):
                link = 'https://www.people.com.cn' + link
            return title, link
        else:
            return None, None
    except Exception as e:
        print(f"抓取失败: {e}")
        return None, None

def main():
    title, link = get_people_daily_headline()
    
    if title and link:
        msg_title = "📰 人民日报今日头条"
        msg_content = f"{title}\n{link}"
    else:
        msg_title = "⚠️ 抓取失败"
        msg_content = "未能获取人民日报头条，请检查网址或网络。"
    
    # 把消息标题和内容存到环境变量，供后面的推送脚本使用
    os.environ['TITLE'] = msg_title
    os.environ['MSG'] = msg_content

if __name__ == "__main__":
    main()
