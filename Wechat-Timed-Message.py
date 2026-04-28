import os
import re
import requests
import sys

# 定义PushPlus的API地址
PUSHPLUS_API_URL = "http://www.pushplus.plus/send"

# 从环境变量中读取配置
url = os.getenv('URL')
pp_token = os.getenv('PPTOKEN')

# --- 1. 调试输出：检查环境变量是否传进来了 ---
print("=== 开始执行脚本 ===")
print(f"URL: {url}")  # 最好不要打印，确保打印包含敏感信息
print(f"PPTOKEN: {'已获取到，长度' + str(len(pp_token)) if pp_token else '未获取到！'}")
# 如果未获取到PPTOKEN，直接报错退出，避免无效调用
if not pp_token:
    print("❌ 错误: 环境变量 PPTOKEN 未正确获取！")
    sys.exit(1)

# --- 2. 抓取人民日报头条 (使用更稳健的正则表达式) ---
def get_people_daily_headline():
    print(f"\n正在抓取: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        print("✅ HTML获取成功。")
        
        # 使用更通用的正则匹配常见的<a>标签链接和内容
        # 匹配 href="..." 和 >...<之间的内容
        match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', resp.text)
        if match:
            link = match.group(1)
            # 使用正则去除内容中可能包含的HTML标签，得到纯文本标题
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            if title:
                if link.startswith('/'):
                    link = 'https://www.people.com.cn' + link
                return title, link
        return None, None
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        return None, None

# --- 3. 通过PushPlus发送消息 ---
def send_to_wechat(title, content):
    print(f"\n准备发送消息，标题: {title}")
    payload = {
        "token": pp_token,
        "title": title,
        "content": content
    }
    try:
        response = requests.post(PUSHPLUS_API_URL, json=payload, timeout=10)
        result = response.json()
        print(f"📤 PushPlus API 返回状态码: {result.get('code')}")
        print(f"📤 API 返回消息: {result.get('msg')}")
        if result.get('code') == 200:
            print("✅ 消息发送指令成功发出！")
        else:
            print(f"❌ 消息发送失败。请检查：{result.get('msg')}")
    except Exception as e:
        print(f"❌ 调用PushPlus API时发生异常: {e}")

# --- 主程序流程 ---
if __name__ == "__main__":
    headline_title, headline_link = get_people_daily_headline()
    
    if headline_title and headline_link:
        msg_title = "📰 人民日报今日头条"
        msg_content = f"{headline_title}\n{headline_link}"
        print(f"\n🎉 抓取成功！头条内容：{msg_content}")
        send_to_wechat(msg_title, msg_content)
    else:
        print("\n⚠️ 抓取失败，将发送提醒。")
        send_to_wechat("⚠️ 抓取失败", "未能获取人民日报头条，请稍后检查。")
