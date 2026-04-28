import os
import re
import requests
import sys

PUSHPLUS_API_URL = "http://www.pushplus.plus/send"

url = os.getenv('URL')
pp_token = os.getenv('PPTOKEN')

print("=== 开始执行脚本 ===")
print(f"URL: {url}")
print(f"PPTOKEN: {'已获取到 (长度 ' + str(len(pp_token)) + ')' if pp_token else '未获取到！'}")

if not pp_token:
    print("❌ 错误: 环境变量 PPTOKEN 未正确获取！")
    sys.exit(1)

def get_people_daily_headline():
    print(f"\n正在抓取: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        html = resp.text
        print(f"✅ 获取 HTML 成功，长度 {len(html)} 字符")

        # 调试：打印前 2000 个字符，看页面大致结构
        print("=== HTML 前 2000 字符 ===")
        print(html[:2000])
        print("=== 结束 ===\n")

        # 策略1：寻找常见头条区域的 <a> 标签（例如包含 'h1' 或特定 class）
        # 人民日报头条通常位于 <div id="pCDom"> 或 <div class="news"> 内
        # 我们尝试多个正则模式，按优先级匹配
        patterns = [
            # 模式1：匹配 <a href="..." target="_blank"> 且标签内直接包含文字（可能是头条）
            r'<a[^>]*href="([^"]+)"[^>]*target="_blank"[^>]*>([^<]+)</a>',
            # 模式2：匹配任何 <a> 标签，但排除常见的导航链接（如 "首页"、"English"）
            r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
        ]
        
        title, link = None, None
        for pattern in patterns:
            matches = re.findall(pattern, html)
            if matches:
                # 过滤掉太短或无意义的标题（比如 "1"、"图"）
                for match_link, match_title in matches:
                    clean_title = re.sub(r'<[^>]+>', '', match_title).strip()
                    # 排除明显不是新闻的链接
                    if len(clean_title) > 4 and not clean_title.startswith('http') and '首页' not in clean_title and 'English' not in clean_title:
                        link = match_link
                        title = clean_title
                        print(f"✅ 匹配到候选：标题='{title}', 链接='{link}'")
                        break
                if title:
                    break
        
        if title and link:
            # 处理相对路径
            if link.startswith('/'):
                link = 'https://www.people.com.cn' + link
            elif link.startswith('./'):
                link = 'https://www.people.com.cn' + link[1:]
            elif not link.startswith('http'):
                link = 'https://www.people.com.cn/' + link
            return title, link
        else:
            print("⚠️ 没有匹配到任何符合条件的新闻链接")
            return None, None

    except Exception as e:
        print(f"❌ 抓取异常: {e}")
        return None, None

def send_to_wechat(title, content):
    print(f"\n准备发送 -> 标题: {title}")
    payload = {
        "token": pp_token,
        "title": title,
        "content": content
    }
    try:
        response = requests.post(PUSHPLUS_API_URL, json=payload, timeout=10)
        result = response.json()
        print(f"📤 PushPlus 返回: code={result.get('code')}, msg={result.get('msg')}")
        if result.get('code') == 200:
            print("✅ 消息已推送到微信")
        else:
            print(f"❌ 推送失败: {result.get('msg')}")
    except Exception as e:
        print(f"❌ 请求 PushPlus 异常: {e}")

if __name__ == "__main__":
    headline_title, headline_link = get_people_daily_headline()
    
    if headline_title and headline_link:
        msg_title = "📰 人民日报今日头条"
        msg_content = f"{headline_title}\n{headline_link}"
        print(f"\n🎉 成功抓取：{msg_content}")
        send_to_wechat(msg_title, msg_content)
    else:
        print("\n⚠️ 最终抓取失败，发送提醒消息")
        send_to_wechat("⚠️ 抓取失败", f"未能从 {url} 获取头条新闻。\n请查看 GitHub Actions 日志中的 HTML 片段。")
